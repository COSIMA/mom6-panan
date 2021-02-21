"""
Convert 0.1° ACCESS 3D daily outputs of temperature, salt and velocity
into the "brushcutter" format suitable for MOM6 open boundary forcing.
"""

from itertools import cycle

import dask.array as da
import numpy as np
import xarray as xr
import xesmf as xe

import dask.multiprocessing
from dask.diagnostics import ProgressBar

# range of files to use -- 3 months of daily data per file
t = range(621, 625)

surface_tracer_vars = ["temp", "salt"]
line_tracer_vars = ["eta_t"]
surface_velocity_vars = ["u", "v"]

# we're probably io-bound, and we just get some kind of lock contention
# in parallel anyway...
dask.config.set(scheduler="synchronous")

# open target grid dataset
# we interpolate onto the hgrid
dg = xr.open_dataset("/g/data/x77/ahg157/inputs/mom6/panan/ocean_hgrid_0025.nc").isel(
    nyp=[-1]
)

# interpolation grid
dg_out = xr.Dataset(
    {"lat": (["location"], dg.y.squeeze()), "lon": (["location"], dg.x.squeeze())}
)
surface_tracer_vars = ["temp", "salt"]
line_tracer_vars = ["eta_t"]
surface_velocity_vars = ["u", "v"]

chunks = {
    "T": {"time": 1, "st_ocean": 7, "yt_ocean": 300, "xt_ocean": None},
    "U": {"time": 1, "st_ocean": 7, "yu_ocean": 300, "xu_ocean": None},
}

# open source datasets
surface_vars = surface_tracer_vars + surface_velocity_vars

in_datasets = {}
for var, staggering in list(zip(surface_tracer_vars, cycle("T"))) + list(
    zip(surface_velocity_vars, cycle("U"))
):
    d = xr.open_mfdataset(
        [
            f"/g/data/ik11/outputs/access-om2-01/01deg_jra55v13_ryf9091/output{i}/ocean/ocean_daily_3d_{var}.nc"
            for i in t
        ],
        chunks=chunks[staggering],
        combine="by_coords",
        parallel=False,
    )[var]
    in_datasets[var] = staggering, d

# line datasets, assume they all come from ocean_daily
d_2d = xr.open_mfdataset(
    [
        f"/g/data/ik11/outputs/access-om2-01/01deg_jra55v13_ryf9091/output{i}/ocean/ocean_daily.nc"
        for i in t
    ],
    chunks={"time": 1, "yt_ocean": 300, "xt_ocean": None},
    combine="by_coords",
    parallel=False,
)[line_tracer_vars]

d_tracer = xr.merge([d for s, d in in_datasets.values() if s == "T"] + [d_2d])
d_velocity = xr.merge([d for s, d in in_datasets.values() if s == "U"])

# reduce selection around target latitude
# and remove spatial chunks (required for xesmf)
d_tracer = d_tracer.sel(yt_ocean=slice(-38, -36)).chunk(
    {"yt_ocean": None, "xt_ocean": None}
)
d_velocity = d_velocity.sel(yu_ocean=slice(-38, -36)).chunk(
    {"yu_ocean": None, "xu_ocean": None}
)

# create the regridding weights between our grids
regridder_tracer = xe.Regridder(
    d_tracer.rename(xt_ocean="lon", yt_ocean="lat"),
    dg_out,
    "bilinear",
    periodic=True,
    locstream_out=True,
    reuse_weights=True,
    filename="bilinear_tracer_weights.nc",
)
regridder_velocity = xe.Regridder(
    d_velocity.rename(xu_ocean="lon", yu_ocean="lat"),
    dg_out,
    "bilinear",
    periodic=True,
    locstream_out=True,
    reuse_weights=True,
    filename="bilinear_velocity_weights.nc",
)

# now we can apply it to input DataArrays:
ds_out = xr.merge([regridder_tracer(d_tracer), regridder_velocity(d_velocity)])

# fix up all the coordinate metadata
ds_out = ds_out.rename(locations="nx_segment_001")
for var in surface_vars:
    ds_out[var] = ds_out[var].rename(st_ocean=f"nz_segment_001_{var}")
    ds_out = ds_out.rename({var: f"{var}_segment_001"})
    ds_out[f"nz_segment_001_{var}"] = np.arange(ds_out[f"nz_segment_001_{var}"].size)

for var in line_tracer_vars:
    ds_out = ds_out.rename({var: f"{var}_segment_001"})

# segment coordinates (x, y, z)
ds_out["nx_segment_001"] = np.arange(ds_out["nx_segment_001"].size)
ds_out["ny_segment_001"] = [0]

# boundary gridpoints
ds_out["ilist_segment_001"] = (
    ["ny_segment_001", "nx_segment_001"],
    (np.arange(0, 14401) / 2)[None, :],
)
ds_out["ilist_segment_001"].attrs["orientation"] = 0

ds_out["jlist_segment_001"] = (
    ["ny_segment_001", "nx_segment_001"],
    np.empty((ds_out.ny_segment_001.size, ds_out.nx_segment_001.size)),
)
ds_out["jlist_segment_001"][:] = 1942
ds_out["jlist_segment_001"].attrs["orientation"] = 0

# lat/lon/depth/dz
ds_out["lon_segment_001"] = (["ny_segment_001", "nx_segment_001"], dg.x)
ds_out["lat_segment_001"] = (["ny_segment_001", "nx_segment_001"], dg.y)

# reset st_ocean so it's not an index coordinate
ds_out = ds_out.reset_index("st_ocean").reset_coords("st_ocean_")
depth = ds_out["st_ocean_"]
depth.name = "depth"
depth["st_ocean"] = np.arange(depth["st_ocean"].size)
del ds_out["st_ocean_"]

# some fiddling to do dz in the same way as brushcutter, while making xarray happy
dz = depth.diff("st_ocean")
dz.name = "dz"
dz = xr.concat([dz, dz[-1]], dim="st_ocean")
dz["st_ocean"] = depth["st_ocean"]

for var in line_tracer_vars:
    ds_out[f"{var}_segment_001"] = ds_out[f"{var}_segment_001"].expand_dims(
        "ny_segment_001", axis=1
    )

for var in surface_vars:
    # add the y dimension
    ds_out[f"{var}_segment_001"] = ds_out[f"{var}_segment_001"].expand_dims(
        "ny_segment_001", axis=2
    )

    ds_out[f"vc_{var}_segment_001"] = (
        ["time", f"nz_segment_001_{var}", "ny_segment_001", "nx_segment_001"],
        da.broadcast_to(
            depth.data[None, :, None, None],
            ds_out[f"{var}_segment_001"].shape,
            chunks=(1, None, None, None),
        ),
    )
    ds_out[f"dz_{var}_segment_001"] = (
        ["time", f"nz_segment_001_{var}", "ny_segment_001", "nx_segment_001"],
        da.broadcast_to(
            dz.data[None, :, None, None],
            ds_out[f"{var}_segment_001"].shape,
            chunks=(1, None, None, None),
        ),
    )

with ProgressBar():
    ds_out.to_netcdf("forcing_obc.nc")
