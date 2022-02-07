#!/bin/bash
#PBS -q normalbw
#PBS -l ncpus=1
#PBS -l wd
#PBS -l storage=gdata/x77+scratch/x77+gdata/ik11
#PBS -l walltime=1:00:00,mem=7GB
#PBS -P x77
#PBS -N output_to_gdata

# Set this directory to something in /g/data3/hh5/tmp/cosima/
# Make a unique path for your set of runs.
# DOUBLE-CHECK IT IS UNIQUE SO YOU DON'T OVERWRITE EXISTING OUTPUT!
GDATADIR=/g/data/ik11/outputs/mom6-panan/panant-01-hycom1-v13

mkdir -p ${GDATADIR}
cd archive
rsync -vrltoD --safe-links output* ${GDATADIR}
rsync -vrltoD --safe-links error_logs ${GDATADIR}
rsync -vrltoD --safe-links pbs_logs ${GDATADIR}

# Be careful here!
#rsync -vrltoD --safe-links restart* ${GDATADIR}
