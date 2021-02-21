import xarray as xr
import numpy as np
import netCDF4
from datetime import timedelta

de = xr.open_dataset("/g/data/x77/ahg157/inputs/mom6/panan/vcoord.nc")
di = xr.open_dataset(
    "/data/panan/temp_salt_init_z_0025.nc",
    chunks={"depth": 11, "nyp": 169, "nxp": 360}
)
df = xr.open_dataset("/g/data/x77/ahg157/inputs/mom6/panan/forcing_obc_converted.nc")
dg = xr.open_dataset("/g/data/x77/ahg157/inputs/mom6//panan/ocean_hgrid_0025.nc")

velocity_timescale = timedelta(days=1).total_seconds()

c2d = (169, 360)
c3d = (11, 169, 360)

kwargs = {
    "zlib": True,
    "chunksizes": c3d,
    "fill_value": netCDF4.default_fillvals["f8"],
}

do = netCDF4.Dataset("/g/data/x77/ahg157/inputs/mom6/panan/sponge_idamp_velonly.nc", "w")
do.createDimension("nxp", 7200)
do.createDimension("nyp", 1690)
do.createDimension("zl", 75)
do.createDimension("zi", 76)

do.createVariable("Idamp", "f8", ("nyp", "nxp"), zlib=True, chunksizes=c2d, fill_value=netCDF4.default_fillvals["f8"])[:] = 0
do.variables["Idamp"][:] = (1 / 3600) * (dg.y.isel(nyp=slice(1, None, 2), nxp=slice(1, None, 2)) > -38)

# h = df.dz_u_segment_001.isel(time=0, ny_segment_001=0, nx_segment_001=slice(1, None, 2))
# do.createVariable("uv_thickness", "f8", ("zl", "nyp", "nxp"), **kwargs)
# do.variables["uv_thickness"][:] = h.values[:,None,:]

do.close()
