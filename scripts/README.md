# Input generation scripts


## Grid refinement

First, we start with the 0.1° supergrid, `ocean_hgrid.nc`, which is in
the input format of the mosaic grid. We restrict this grid to just the
region of interest (i.e. south of 37°S) to act as a source grid for
interpolating the existing data.

Using `generate_grid.py`, we refine by simply bisecting between pairs
of points. Since we're safely out of the tripole region, we can treat
the latitude and longitude dimensions orthogonally, and then broadcast
them together to write the hgrid input file. To convert this back to a
mosaic-style grid, we use `make_hgrid` from the FRE tools:

```
$ ./mom5/src/tools/make_hgrid/make_hgrid --grid_type from_file --my_grid_file grid_0025.nc

```

## Regridding weights

We use xESMF for interpolating existing data up to the new
resolution. For this, we need a file containing the weights for
bilinear interpolation to make this operation as efficient as
possible, deferring most of the expense to the weight generation step
using `ESMF_RegridWeightGen`. The easiest format for this tool appears
to be SCRIP, for which we define cell centres and corners. Since we
already have a supergrid, this is trivial using the
`hgrid_to_scrip.py` script.

Then we can generate our bilinear weights with (likely using multiple cores with MPI):
```
$ ESMF_RegridWeightGen -s src_grid -d dst_grid -w weight_file -m bilinear
```

## Interpolating the initial state and topography

In order to start close to the surrounding model's state, we use its
final snapshot of salinity and temperature (daily average) restricted
to the interpolation domain. Similarly, we simply refine the
topography by a bilinear interpolation. These operations are both
performed by the `interp_initial.py` script.

## Generating the open boundary forcing

As a regional model, we force the open northern boundary with daily
temperature, salinity, and velocity fields from the surrounding
model. These data need to be interpolated onto the 0.05° supergrid at
the northern boundary, and put in the correct format for the open
boundary routines.

The initial OBC forcing was generated using `brushcut_xesmf.py`, which
does the main job of interpolating the year of 3D daily data onto the
open boundary supergrid. However, this script gets the vertical
coordinate for the forcing data wrong — it needs to match the actual
topography of the source data, or the open boundary code ends up
bringing in NaN/junk values at land.

## Correctly extracting the vertical grid

To generate a time-varying vertical grid on both tracer and velocity
points, we use the `depth_section.py` script. This uses only the `dzt`
variable from the model outputs, and sets `dzu` as a minimum of the
neighbouring `dzt`s, then interpolates that onto the open boundary
supergrid.

## Modifying the OBC sections

To convert the originally-generated forcing to be in the actual
correct format, incorporating correct variable attributes and vertical
coordinate information, we use `convert_forcing.py`. We also tweak the
meridional velocity on the open boundary so that it integrates to zero
globally, which might help keep the total mass in the domain
reasonably constant.


# Sponge generation scripts

Unfortunately, the open boundary doesn't seem to be sufficient to
handle all the boundary forcing: a strong signal in the forcing data
tends to overwhelm the model. To deal with this, we also need to add a
sponging term to spread some of this input signal into the domain
instead of just at a single point.

We use `generate_idamp_netcdf4.py` to create the generic sponge
damping file. As we use a modification of the model that disables
tracer sponging, this essentially just provides the damping field and
nothing else.

To generate the time-dependent velocity sponging, we use
`generate_sponge_uv_netcdf4.py`, which creates a sponging field from
the OBC forcing. As the script names suggest, these use the
lower-level netCDF4 library to generate the sponge files, as they can
be quite large.


# Input modification scripts

With some experience of actually running the model under our belts,
some issues with the input files have cropped up, particularly in the
topography which was interpolated up from a lower resolution. There
are a couple of scripts to tweak this interpolated topography without
requiring it to be fully regenerated.

## Filling basins

There were a few small basins that played no role by being a single
point, or connected by a channel one-cell wide. Upon interpolation,
these got doubled in size, and started causing problems. The
`fill_topog.py` script takes a list of points within any basins that
should be filled, and flood-fills them in.

## Smoothing coastlines

Some coastlines from the original topography are very long and
horizontal. With the interpolation, these stretches are separated by a
two-point jump, and seem to excessively accelerate velocities, leading
to a seasonal cycle of excessive CFL. As an attempt to fix this, we
can specify a section of coastline with `smooth_coasts.py`, which will
create an intermediate step between the two-point jumps.
