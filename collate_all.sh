#!/bin/bash

read current < .current
cd archive/output${current}
all_files=(*.nc.????)
readarray -td '' base_names < <(printf '%s\0' "${all_files[@]%.*}" | LC_ALL=C sort -zu)
for f in "${base_names[@]}"; do
	cat <<EOS | qsub -P ot56 -q normal -S /bin/bash -l ncpus=4,mem=16GB,walltime=06:00:00,wd,storage=scratch/e14+scratch/x77 -
module load openmpi
mpiexec /scratch/x77/ahg157/software/mppnccombine-fast -r -o "$f" "$f.*"
EOS
done
