#!/bin/bash

# Run script that generates the bash submission script with user settings
python ${CMEC_CODE_DIR}/write_batch_script.py "cori_slurm"

sbatch ${CMEC_WK_DIR}/user_slurm_script.sh
