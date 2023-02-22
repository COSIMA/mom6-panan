# MOM6 Pan-Antarctic Model

Regional model south of 37°S. MOM6-SIS2 coupled configuration,
forced at the open boundary by one year of daily output (currently) from
ACCESS-OM2-01 RYF, and at the surface by JRA55v13 RYF. This repository
contains the model configurations, and the scripts required to
generate the input forcing.

For up to date diagnostics on the model output see the [mom6-panan-diagnostics](https://github.com/COSIMA/mom6-panan-diagnostics) repository.

Panan development meetings are at 11:30am on Mondays. Get in touch with Adele if you'd like to join the development team.

Current working configurations are:
* 1/10° zstar, in the [panan-01-zstar-run](https://github.com/COSIMA/mom6-panan/tree/panan-01-zstar-run) branch. Boundary forcing and initial condition is year 2170 (i.e. 270 year spinup) of ACCESS-OM2-01 RYF (note the discrepancy between conservative temperature at the boundary and potential temperature as the prognostic temperature!).
* 1/10° with hycom vertical coordinate, in the [panan-01-hycom1-run](https://github.com/COSIMA/mom6-panan/tree/panan-01-hycom-run) branch. Boundary forcing is ACCESS-OM2-01 RYF as above (same issue as above).
* 1/20° zstar, in the [test-1/20deg](https://github.com/COSIMA/mom6-panan/tree/test-1/20deg) branch. Currently it has ACCESS-OM2-01 RYF boundary forcing and initial condition, as above.

As far as Adele knows, the master, hycom1-run and zstar-run branches do not correspond to any up to date configurations.
