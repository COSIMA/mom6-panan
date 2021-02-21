import numpy as np
import xarray as xr

# load 1/10 deg grid file which has been pared down
# to everything south of 37S

d = xr.open_dataset("/g/data/x77/ahg157/inputs/mom6/panan/ocean_hgrid.nc")

# grid is uniform, so just work with a single meridional profile
# drop the first row so we don't put a tracer point further south
# than the source grid (makes interpolation hard)
yc = d.y.isel(nxp=0).values[1:-1]

# bisect every pair of points for t points
yt = (yc[1:] + yc[:-1]) / 2

# higher-res longitudes
xc = d.x.isel(nyp=0).values
xt = (xc[1:] + xc[:-1]) / 2

# broadcast to meshgrid
XC, YC = np.meshgrid(xc, yc)
XT, YT = np.meshgrid(xt, yt)

# create output dataset
ds = xr.Dataset({
    "grid_lon":  (["grid_yc", "grid_xc"], XC),
    "grid_lat":  (["grid_yc", "grid_xc"], YC),
    "grid_lont": (["grid_yt", "grid_xt"], XT),
    "grid_latt": (["grid_yt", "grid_xt"], YT),
})

ds.to_netcdf("/g/data/x77/ahg157/inputs/mom6/panan/grid_0025.nc")
