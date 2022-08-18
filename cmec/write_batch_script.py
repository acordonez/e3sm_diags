#!/usr/bin/env python

import json
import os
import sys

wk_dir = os.getenv("CMEC_WK_DIR")

configuration_name = sys.argv[1]

out_script = os.path.join(wk_dir,"user_slurm_script.sh")

# Get user parameters from cmec.json
cmec_settings = os.getenv("CMEC_CONFIG_DIR")
cmec_settings_json = os.path.join(cmec_settings,"cmec.json")
with open(cmec_settings_json,"r") as cmec_json:
    cmec_user_settings = json.load(cmec_json)["e3sm_diags/{0}".format(configuration_name)]

# Validate user settings
slurm_settings = cmec_user_settings["slurm"]
if "account" not in slurm_settings:
    raise RuntimeError("'account' is a required setting for the cori-slurm configuration")

# Assemble batch script
headers = [
    "#!/bin/bash -l\n",
    "#SBATCH --job-name={0}\n".format(slurm_settings.get("job-name","cmec")),
    "#SBATCH --qos={0}\n".format(slurm_settings.get("queue","regular")),
    "#SBATCH --account={0}\n".format(slurm_settings.get("account")),
    "#SBATCH --nodes={0}\n".format(slurm_settings.get("nodes","1")),
    "#SBATCH --time={0}\n".format(slurm_settings.get("time","00:30:00")),
    "#SBATCH --constraint=haswell\n"
]

source = ["source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_cori-haswell.sh\n"]

param = ["python ${CMEC_CODE_DIR}/generate_parameter_file.py \"cori_slurm\"\n"]

num_workers = slurm_settings.get("num_workers","32")
run = ["python ${CMEC_WK_DIR}/run_e3sm_diags.py --multiprocessing --num_workers="+str(num_workers)+"\n"]

lines = headers + source + param + run

with open(out_script,"w") as dest:
    dest.writelines(lines)

