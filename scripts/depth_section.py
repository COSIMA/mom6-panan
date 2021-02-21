"""
Compute the dz and vc components for brushcutter open boundary input
from dzt, kmt and ht variables from MOM5, then interpolate onto the
open boundary grid.
"""

import numpy as np
import xarray as xr
import xesmf as xe

from xgcm import Grid

import dask.multiprocessing

# writing with dask after regridding seems to deadlock somewhere
dask.config.set(scheduler="synchronous")

# timestamps of forcing datasets
t = range(621, 625)

# depth of the bottom (unused)
dg = xr.open_dataset(
    f"/g/data/ik11/outputs/access-om2-01/01deg_jra55v13_ryf9091/output{t[0]}/ocean/ocean_grid.nc"
).ht.sel(yt_ocean=slice(-38, -36))

# slice corresponding to y range [-38, -36] + 1 point at the north for interpolating
# dzt onto dzu
ysl = slice(833, 859)

# t-cell thickness (time-varying, might as well because the OBC forcing is too...)
# we need to also select out the q-point data so we can construct the xgcm grid
d = xr.open_mfdataset(
    [
        f"/g/data/ik11/outputs/access-om2-01/01deg_jra55v13_ryf9091/output{i}/ocean/ocean.nc"
        for i in t
    ],
    combine="by_coords",
    parallel=False,
    preprocess=lambda d: d[["dzt", "yu_ocean", "xu_ocean"]].isel(
        yt_ocean=ysl, yu_ocean=ysl
    ),
)

# B-grid, periodic in X direction
g = Grid(
    d,
    periodic=["X"],
    coords={
        "X": {"center": "xt_ocean", "right": "xu_ocean"},
        "Y": {"center": "yt_ocean", "right": "yu_ocean"},
    },
)

# dzu is the minimum of the neighbouring dzt
# vanished layers just get 0 thickness, rather than missing
d["dzu"] = g.min(d.dzt, ["X", "Y"], boundary="fill").chunk({"xu_ocean": None})
d["dzt"] = d.dzt
# we needed a slightly bigger domain to do the above, so now we restrict to the proper domain
d = d.isel(yu_ocean=slice(None, -1), yt_ocean=slice(1, None))

# we don't actually need vc (it's never used by the obc code...)
# flip, sum from the bottom up, then unflip
# d["vc"] = (
#     d.dzt.isel(st_ocean=slice(None, None, -1))
#     .cumsum(dim="st_ocean")
#     .isel(st_ocean=slice(None, None, -1))
#     + dg
# )

# construct the regridders for t and q points
dg = xr.open_dataset("/g/data/x77/ahg157/inputs/mom6/panan/ocean_hgrid_0025.nc").isel(
    nyp=[-1]
)
dg_out = xr.Dataset(
    {"lat": (["location"], dg.y.squeeze()), "lon": (["location"], dg.x.squeeze())}
)
regridder_u = xe.Regridder(
    d[["dzu"]].rename(xu_ocean="lon", yu_ocean="lat"),
    dg_out,
    "bilinear",
    periodic=True,
    locstream_out=True,
    reuse_weights=True,
    filename="bilinear_velocity_weights.nc",
)
regridder_t = xe.Regridder(
    d[["dzt"]].rename(xt_ocean="lon", yt_ocean="lat"),
    dg_out,
    "bilinear",
    periodic=True,
    locstream_out=True,
    reuse_weights=True,
    filename="bilinear_tracer_weights.nc",
)

# regrid separately and recombine, then give dimensions some sensible names
d_out = xr.merge([regridder_u(d[["dzu"]]), regridder_t(d[["dzt"]])]).fillna(0)
d_out = d_out.rename(locations="nx_segment_001")
d_out = d_out.expand_dims("ny_segment_001", 2)

d_out.to_netcdf(
    "obc_vertical.nc",
    encoding={"dzu": {"_FillValue": -1e20}, "dzt": {"_FillValue": -1e20}},
)
