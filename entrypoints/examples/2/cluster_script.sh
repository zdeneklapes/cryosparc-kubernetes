#!/bin/bash
#PBS -N cryosparc_{{ project_uid }}_{{ job_uid }}
#PBS -q default
#PBS -l walltime=115:00:00
#PBS -l select=1:ncpus={{ num_cpu }}:ngpus={{ num_gpu }}:mem=62gb:scratch_local=1000gb
#PBS -o {{ job_dir_abs }}
#PBS -e {{ job_dir_abs }}

umask 0027

{{ run_cmd }}

clean_scratch