#!/usr/bin/env python

import json
import os
import sys

configuration_name = sys.argv[1]

test_path = os.getenv("CMEC_MODEL_DATA")
ref_path = os.getenv("CMEC_OBS_DATA")
out_path = str(os.getenv("CMEC_WK_DIR"))

# Get settings from cmec settings file
cmec_settings = os.getenv("CMEC_CONFIG_DIR")
cmec_settings_json = os.path.join(cmec_settings,"cmec.json")
with open(cmec_settings_json,"r") as cmec_json:
    cmec_user_settings = json.load(cmec_json)["e3sm_diags/{0}".format(configuration_name)]

# Assemble E3SM diags parameter file
header = [
    "import os",
    "\n",
    "\nfrom e3sm_diags.parameter.core_parameter import CoreParameter",
    "\nfrom e3sm_diags.run import runner",
    "\n",
    "\nparam = CoreParameter()",
]

parameters = [
    "\nparam.test_data_path = '{0}/'".format(test_path),
    "\nparam.reference_data_path = '{0}/'".format(ref_path),
    "\nparam.results_dir = '{0}/'".format(out_path)
]

years = [
    '\nparam.seasons = ["ANN"]'
]

# Get user parameters from cmec.json
user_parameters = []
for item in cmec_user_settings["parameters"]:
    val = cmec_user_settings["parameters"][item]
    if isinstance(val,str):
        line = "\nparam.{0} = '{1}'".format(item, val)
    else:
        line = "\nparam.{0} = {1}".format(item,val)
    user_parameters.append(line)

default_set = ["zonal_mean_xy", "zonal_mean_2d", "meridional_mean_2d", "lat_lon", "polar", "area_mean_time_series"]

if "sets" in cmec_user_settings:
    if isinstance(cmec_user_settings["sets"],list):
        runner = ["\nrunner.sets_to_run = {0}".format(cmec_user_settings["sets"])]
    else:
        print("'Sets' parameter is not valid list. Using defaults.")
        runner = ["\nrunner.sets_to_run = {0}".format(default_set)]
else:
    runner = ["\nrunner.sets_to_run = {0}".format(default_set)]

runner.append(
    "\nrunner.run_diags([param])",
    )

parameter_file_text = header + parameters + years + user_parameters + runner

with open(os.path.join(out_path, "run_e3sm_diags.py"), "w") as parameter_file:
    parameter_file.writelines(parameter_file_text)
