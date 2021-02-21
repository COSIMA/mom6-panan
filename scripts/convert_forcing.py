"""Convert forcing from default xarray output to something MOM/SIS friendly."""

import cftime
import numpy as np
import xarray as xr
import netCDF4
from progress.bar import Bar

# 3d variables
v3d = ["temp", "salt", "u", "v"]
# mapping from variable to vertical spacing coordinate
vv = {"temp": "dzt", "salt": "dzt", "u": "dzu", "v": "dzu"}

# datasets
d = xr.open_dataset("forcing_obc.nc", decode_times=False)
dv = xr.open_dataset("obc_vertical.nc")
do = netCDF4.Dataset("forcing_obc_converted.nc", "w")

# create static dimensions
do.createDimension("ny_segment_001", 1)
do.createDimension("nx_segment_001", 14401)
for v in v3d:
    do.createDimension(f"nz_segment_001_{v}", 75)

# create coordinate data
for dim in do.dimensions:
    do.createVariable(dim, "i4", (dim,))
    do.variables[dim][:] = d[dim]

# create index lists
ilist = do.createVariable(
    "ilist_segment_001", "f8", ("ny_segment_001", "nx_segment_001")
)
ilist[:] = d["ilist_segment_001"]
ilist.orientation = np.int32(0)

jlist = do.createVariable(
    "jlist_segment_001", "f8", ("ny_segment_001", "nx_segment_001")
)
jlist[:] = d["jlist_segment_001"]
jlist.orientation = np.int32(0)

# create time dim in preparation for data variables
do.createDimension("time", None)
time = do.createVariable("time", "f8", ("time",))
time.long_name = "time"
time.cartesian_axis = "T"
time.calendar_type = "NOLEAP"
# time.units = "days since 2056-04-01 12:00:00"
time.units = "days since 1900-01-01 12:00:00"
time.calendar = "noleap"
time.modulo = " "

# create all variables
var_names = []
for v in v3d:
    n = f"{v}_segment_001"
    do.createVariable(
        n,
        "f8",
        ("time", f"nz_segment_001_{v}", "ny_segment_001", "nx_segment_001"),
        zlib=True,
        chunksizes=(1, 11, 1, 280),
        fill_value=netCDF4.default_fillvals["f8"],
    )
    var_names.append(n)

    # vertical info
    for z in ["dz"]:
        n = f"{z}_{v}_segment_001"
        do.createVariable(
            n,
            "f8",
            ("time", f"nz_segment_001_{v}", "ny_segment_001", "nx_segment_001"),
            zlib=True,
            chunksizes=(1, 11, 1, 280),
        )

do.createVariable(
    "eta_t_segment_001",
    "f8",
    ("time", "ny_segment_001", "nx_segment_001"),
    fill_value=netCDF4.default_fillvals["f8"],
)
var_names.append("eta_t_segment_001")

bar = Bar("Exporting", max=d.time.size)
s = d.time.size
for t in range(s):
    # skip to january first -- tt is index in file beginning with april
    tt = (t + 275) % 365
    time[t] = t

    # get month that we belong to (for vertical data)
    m = (cftime.num2date(t, time.units, time.calendar).month - 1 + 9) % 12

    # copy vertical info
    for v in v3d:
        # do.variables[f"vc_{v}_segment_001"][t, ...] = dv.vc.isel(time=m)
        do.variables[f"dz_{v}_segment_001"][t, ...] = dv[vv[v]].isel(time=m)

    # copy actual data
    for v in var_names:
        # propagate NaNs through depth so we don't blow stuff up later
        data = d[v][tt, ...]
        if data.ndim >= 3:
            data = data.ffill(data.dims[0])

        # linear interp across masked points
        # this may be less accurate if we have
        # masked points at the periodic edge
        data = data.interpolate_na("nx_segment_001")

        # make V integrate to 0
        if v == "v_segment_001":
            # fiddle with coords on dz so it multiplies nicely
            dz = (dv[vv["v"]].isel(time=m)
                  .rename({"st_ocean": "nz_segment_001_v"})
                  .reset_index("nz_segment_001_v"))
            a = dz.sum().item()
            i = (dz * data).sum().item()
            data -= i/a

        do.variables[v][t, ...] = data.to_masked_array()

    bar.next()

bar.finish()
do.close()
