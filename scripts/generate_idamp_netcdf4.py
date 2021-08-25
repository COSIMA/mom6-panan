import xarray as xr
import numpy as np
import netCDF4
import argparse
from datetime import timedelta
from pathlib import Path

input_dir = "/g/data/x77/ahg157/inputs/mom6/panan"

parser = argparse.ArgumentParser(description="Generate a sponge idamp file")
parser.add_argument("-i", "--input-dir",
                    default=input_dir,
                    type=Path,
                    help="the directory containing experiment inputs")
parser.add_argument("-o", "--output-path",
                    required=True,
                    type=Path,
                    help="the output file path, relative to INPUT_DIR")
parser.add_argument("-w", "--width",
                    required=True,
                    type=float,
                    help="sponge width (in degrees)")
parser.add_argument("-l", "--linear",
                    action="store_true",
                    help="if true, ramp linearly over the sponge width")
parser.add_argument("--seconds",
                    default=0,
                    type=int,
                    help="sponge timescale (in seconds)")
parser.add_argument("--hours",
                    default=0,
                    type=int,
                    help="sponge timescale (in hours)")
parser.add_argument("--days",
                    default=0,
                    type=int,
                    help="sponge timescale (in days)")
args = parser.parse_args()

dg = xr.open_dataset(args.input_dir / "ocean_hgrid_0025.nc")

sponge_timescale = (
    timedelta(
        seconds=args.seconds,
        hours=args.hours,
        days=args.days
    ).total_seconds()
)

# hardcode chunk sizes...
c2d = (169, 360)
c3d = (11, 169, 360)

do = netCDF4.Dataset(str(args.input_dir / args.output_path), "w")
# hardcode dimension sizes...
do.createDimension("nxp", 7200)
do.createDimension("nyp", 1690)
do.createDimension("zl", 75)
do.createDimension("zi", 76)

do.createVariable("Idamp", "f8", ("nyp", "nxp"), zlib=True, chunksizes=c2d, fill_value=netCDF4.default_fillvals["f8"])[:] = 0

y = dg.y.isel(nyp=slice(1, None, 2), nxp=slice(1, None, 2))
north_lat = y.isel(nyp=-1).item(0)
south_lat = north_lat - args.width
sponge_region = y > south_lat

if args.linear:
    do.variables["Idamp"][:] = sponge_region * (((y - south_lat) / args.width) / sponge_timescale)
else:
    do.variables["Idamp"][:] = sponge_region * (1 / sponge_timescale)

do.close()
