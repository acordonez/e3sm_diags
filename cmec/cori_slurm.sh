#!/bin/bash

echo "#!/bin/bash -l" >> ${CMEC_WK_DIR}/submit_script.sh
echo "#SBATCH --job-name="${CMEC_JOB_NAME} >> ${CMEC_WK_DIR}/submit_script.sh
echo "#SBATCH --qos="${CMEC_QUEUE} >> ${CMEC_WK_DIR}/submit_script.sh
echo "#SBATCH --account="${CMEC_ACCT_CODE} >> ${CMEC_WK_DIR}/submit_script.sh
echo "#SBATCH --nodes="${CMEC_NODES} >> ${CMEC_WK_DIR}/submit_script.sh
echo "#SBATCH --time="${CMEC_TIME} >> ${CMEC_WK_DIR}/submit_script.sh
echo "#SBATCH -C haswell" >> ${CMEC_WK_DIR}/submit_script.sh

echo "source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_cori-haswell.sh" >> ${CMEC_WK_DIR}/submit_script.sh

echo "python ${CMEC_CODE_DIR}/generate_parameter_file.py \"cori_slurm\"" >> ${CMEC_WK_DIR}/submit_script.sh

echo "python ${CMEC_WK_DIR}/run_e3sm_diags.py --multiprocessing --num_workers=32" >> ${CMEC_WK_DIR}/submit_script.sh

sbatch ${CMEC_WK_DIR}/submit_script.sh
