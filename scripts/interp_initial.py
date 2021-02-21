"""Modified interpolation script to use a larger source domain"""

import xarray as xr
import xesmf as xe

# target grid (t points)
dg = xr.open_dataset("/g/data/x77/ahg157/inputs/mom6/panan/ocean_hgrid_0025.nc")
dg = (
    dg[["x", "y"]]
    .isel(nxp=slice(1, None, 2), nyp=slice(1, None, 2))
    .rename(x="lon", y="lat")
)

# source grid (t points)
dg01 = xr.open_dataset("/g/data/x77/ahg157/inputs/mom6/panan/ocean_hgrid.nc")
dg01 = (
    dg01[["x", "y"]]
    .isel(nxp=slice(1, None, 2), nyp=slice(1, None, 2))
    .rename(x="lon", y="lat")
)

regridder = xe.Regridder(
    dg01,
    dg,
    "bilinear",
    periodic=True,
    filename="bilinear_2d_weights.nc",
    reuse_weights=True,
)


def interp_topog(enc):
    dt = xr.open_dataset(
        "/g/data/ik11/inputs/access-om2/input_08022019/mom_01deg/topog.nc"
    )
    dt = dt.isel(yy=slice(None, dg01.nyp.size))
    dt_out = regridder(dt).rename(nxp="nx", nyp="ny")
    del dt

    del dt_out["lon"]
    del dt_out["lat"]
    dt_out.to_netcdf(
        "ocean_topog.nc", encoding={"depth": enc},
    )
    del dt_out


def interp_initial(enc):
    dd = xr.open_dataset("temp_salt_init_z.nc")[["temp", "salt"]]
    dd["temp"] -= 273.15  # kelvin to celsius

    dd_out = regridder(dd)
    del dd

    dd_out["nxp"] = dd_out["lon"].isel(nyp=0)
    dd_out["nyp"] = dd_out["lat"].isel(nxp=0)
    del dd_out["lon"]
    del dd_out["lat"]
    dd_out.to_netcdf("temp_salt_init_z_0025.nc", encoding={"temp": enc, "salt": enc})


enc = {
    "_FillValue": -1e20,
    "chunksizes": (169, 360),
    # "zlib": True,
    # "shuffle": True,
    # "complevel": 1,
}
# interp_topog(enc)

enc["chunksizes"] = (11, 169, 360)
#interp_initial(enc)
