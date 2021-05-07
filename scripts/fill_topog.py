from netCDF4 import Dataset
import numpy as np

def fill_basin(ds, point):
    mask = np.zeros(ds.shape, dtype=bool)
    q = [point]

    while len(q) > 0:
        p = q.pop(0)
        if mask[p]: continue

        mask[p] = True

        for delta in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            dy, dx = delta
            pp = (p[0] + dy, p[1] + dx)

            if not np.ma.is_masked(ds[pp]):
                q.append(pp)

    return mask

# list of (y, x) points within the basins that need to be masked
edits = [
    (1279,4097),
    (1270,4405),
    (844,4469),
    (555,6327),
]

d = Dataset("/g/data/x77/ahg157/inputs/mom6/panan/ocean_topog_masked.nc", "a")

mask = np.zeros(d["depth"].shape, dtype=bool)
for edit in edits:
    mask |= fill_basin(d["depth"], edit)

# we can't do masked indexing?
for c in zip(*np.where(mask)):
    d["depth"][c] = d["depth"]._FillValue

d.close()
