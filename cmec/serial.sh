#!/bin/bash

#source ${CONDA_SOURCE}
#conda activate ${CONDA_ENV_ROOT}/e3sm_diags_env
source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_cori-haswell.sh

cd ${CMEC_CODE_DIR}
python generate_parameter_file.py "serial"

python ${CMEC_WK_DIR}/run_e3sm_diags.py
