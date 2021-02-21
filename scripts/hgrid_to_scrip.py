import sys
import numpy as np
import xarray as xr
from netCDF4 import Dataset

if len(sys.argv) < 3:
    print("Usage: hgrid_to_scrip [hgrid.nc] [out.nc]")
    sys.exit(1)

hgrid = xr.open_dataset(sys.argv[1])

nlon = hgrid.nxp.size // 2
nlat = hgrid.nyp.size // 2

x_t = hgrid.x.isel(nxp=slice(1, None, 2), nyp=slice(1, None, 2))
y_t = hgrid.y.isel(nxp=slice(1, None, 2), nyp=slice(1, None, 2))

scrip = Dataset(sys.argv[2], "w")

scrip.createDimension("grid_size", nlat * nlon)
scrip.createDimension("grid_corners", 4)
scrip.createDimension("grid_rank", 2)

grid_dims = scrip.createVariable("grid_dims", "i4", ("grid_rank",))
grid_dims[:] = [nlon, nlat]

center_lat = scrip.createVariable("grid_center_lat", "f8", ("grid_size",))
center_lat.units = "degrees"
center_lat[:] = y_t.data.flatten()

center_lon = scrip.createVariable("grid_center_lon", "f8", ("grid_size",))
center_lon.units = "degrees"
center_lon[:] = x_t.data.flatten()

imask = scrip.createVariable("grid_imask", "i4", ("grid_size",))
imask.units = "unitless"
imask[:] = 1 - np.zeros(nlat * nlon, dtype=np.int)

corner_lat = scrip.createVariable("grid_corner_lat", "f8", ("grid_size", "grid_corners"))
corner_lat.units = "degrees"
corner_lat[:,0] = hgrid.y.isel(nyp=slice(0, -1, 2), nxp=slice(0, -1, 2)).data.flatten()
corner_lat[:,1] = hgrid.y.isel(nyp=slice(0, -1, 2), nxp=slice(2, None, 2)).data.flatten()
corner_lat[:,2] = hgrid.y.isel(nyp=slice(2, None, 2), nxp=slice(2, None, 2)).data.flatten()
corner_lat[:,3] = hgrid.y.isel(nyp=slice(2, None, 2), nxp=slice(0, -1, 2)).data.flatten()

corner_lon = scrip.createVariable("grid_corner_lon", "f8", ("grid_size", "grid_corners"))
corner_lon.units = "degrees"
corner_lon[:,0] = hgrid.x.isel(nyp=slice(0, -1, 2), nxp=slice(0, -1, 2)).data.flatten()
corner_lon[:,1] = hgrid.x.isel(nyp=slice(0, -1, 2), nxp=slice(2, None, 2)).data.flatten()
corner_lon[:,2] = hgrid.x.isel(nyp=slice(2, None, 2), nxp=slice(2, None, 2)).data.flatten()
corner_lon[:,3] = hgrid.x.isel(nyp=slice(2, None, 2), nxp=slice(0, -1, 2)).data.flatten()

scrip.close()
