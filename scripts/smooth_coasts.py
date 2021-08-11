import xarray as xr
import numpy as np
from netCDF4 import Dataset

# first, set up X/Y slices of the desired section in physical space
d = xr.open_dataset("/scratch/x77/amh157/mom6/archive/mom6-panan/output000/19910101.ocean_static.nc").depth_ocean
xs = slice(*np.where((-177 <= d.xh) & (d.xh <= -165))[0][[0, -1]] + [3, 1]) # tweak: bump the left edge by a few points
ys = slice(*np.where((-79 <= d.yh) & (d.yh <= -77))[0][[0, -1]] + [0, 1])

sect = d.isel(xh=xs, yh=ys)
# find the index of the coastal boundary for each point along the section
coast = sect.notnull().argmax(dim="yh")
# get a list of the steps along the coast
jumps = np.where(coast[:-1] != coast[1:])[0]
# whether the jump is a rising or falling edge
rising = coast[jumps] < coast[jumps + 1]
# half-spans between jumps
widths = (np.diff(jumps) + 2) // 2

filled = coast.copy()
for i in range(len(jumps) - 1):
    if not rising[i] and not rising[i+1]:
        # create a half-step between two falling steps
        filled[jumps[i] + 1:jumps[i] + widths[i]] += 1

    elif not rising[i] and rising[i+1]:
        # fill the entire span between a fall followed by a rise
        filled[jumps[i] + 1:jumps[i+1] + 1] += 1

# reconstruct a mask from the new coast locations
mask = xr.ones_like(sect)
for i, f in enumerate(filled):
    mask[:f.item(), i] = False

d = Dataset("/g/data/x77/ahg157/inputs/mom6/panan/ocean_topog_filled.nc", "a")
for c in zip(*np.where(mask != sect.notnull())):
    # convert local coords in the mask to global
    c = (c[0] + ys.start, c[1] + xs.start)
    d["depth"][c] = d["depth"]._FillValue

d.close()
