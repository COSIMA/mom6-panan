import numpy as np
import xarray as xr
import netCDF4
from time import perf_counter

di = xr.open_dataset("/g/data/x77/ahg157/inputs/mom6/panan/forcing_obc_converted.nc", decode_cf=False)
dg = xr.open_dataset("/g/data/x77/ahg157/inputs/mom6/panan/ocean_hgrid_0025.nc")
dv = xr.open_dataset("/g/data/x77/ahg157/inputs/mom6/panan/vcoord.nc")

kwargs = {
    "zlib": True,
    "chunksizes": (1, 11, 169, 360),
    "fill_value": netCDF4.default_fillvals["f8"],
}

s3d = (75, 1690, 7200)

do = netCDF4.Dataset("/g/data/x77/ahg157/inputs/mom6/panan/sponge_uv.nc", "w")
do.createDimension("time", None)
do.createDimension("nxp", s3d[2])
do.createDimension("nyp", s3d[1])
do.createDimension("zl", s3d[0])

do.createVariable("time", "f8", ("time",))
# duplicate attributes from source dataset
for a in di.time.attrs.items():
    do.variables["time"].setncattr(*a)

# we need to give horizontal coordinate axes the cartesian axis attribute
# which means we need to make a variable for them
# we also only need the tracer grid, because the sponge code
# interpolates this onto the velocity grid during application
do.createVariable("nxp", "f8", ("nxp",))
do.createVariable("nyp", "f8", ("nyp",))
do.createVariable("zl", "f8", ("zl",))

do.variables["nxp"].cartesian_axis = "X"
do.variables["nxp"][:] = dg.x.isel(nyp=-1, nxp=slice(1, None, 2))
do.variables["nyp"].cartesian_axis = "Y"
do.variables["nyp"][:] = dg.y.isel(nyp=slice(1, None, 2), nxp=0)
do.variables["zl"].cartesian_axis = "Z"
do.variables["zl"][:] = dv.st_ocean

do.createVariable("u", "f8", ("time", "zl", "nyp", "nxp"), **kwargs)
do.createVariable("v", "f8", ("time", "zl", "nyp", "nxp"), **kwargs)

for i, t in enumerate(di.time):
    print("{}/{}...".format(i, di.time.size), end="", flush=True)

    t_start = perf_counter()

    uv_stripe = (
        di[["u_segment_001", "v_segment_001"]]
        .isel(time=i, nx_segment_001=slice(1, None, 2))
        .interpolate_na(dim="nx_segment_001", method="nearest", use_coordinate=False)
    )

    do.variables["time"][i] = t
    do.variables["u"][i,:,-30:,:] = uv_stripe.u_segment_001
    do.variables["v"][i,:,-30:,:] = uv_stripe.v_segment_001

    t_end = perf_counter()
    print("{:.3}s".format(t_end - t_start))

do.close()
