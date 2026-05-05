"""
Configuration for the Bayesian parameter optimization pipeline (Artefact 3).

All variables defined here are imported via wildcard import in Bayesian_Functions.py.
Paths are derived from Config.py so the project works on any machine after cloning.
"""

import sys
import os
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import Config

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_RESOURCES_DIR = Path(__file__).resolve().parent / "Resources"

TEMP_PATH          = Config.TEMP_PATH
MODELICA_FILE_DIR  = Config.MODELICA_FILE_DIR
MODELICA_MODEL_NAME = Config.MODELICA_MODEL_NAME
MODELICA_FILE_NAME  = Config.MODELICA_FILE_NAME

# Destination directory for calibration result CSV files
DEST_PATH = Config.SIMULATION_RESULTS_DIR / "Calibration_Results"

# Artefact 3 resource files
OPTIMIZATION_RESULTS_FILE        = _RESOURCES_DIR / "optimization_results.csv"
EVALUATION_RESULTS_FILE          = _RESOURCES_DIR / "evaluation_results.csv"
USER_EVALUATION_RESULTS_FILE     = _RESOURCES_DIR / "user_defined_evaluation_results.csv"
GROUPED_PARAMETERS_FILE          = _RESOURCES_DIR / "Grouped_Parameters.csv"
CURRENT_BOUNDS_FILE              = _RESOURCES_DIR / "Current_Bounds.csv"

# Active real-plant dataset used as reference signal during optimization
REAL_DATASET_PATH = Config.CURRENT_DATASET_PATH

# Output directory for Bayesian optimization results
OUTPUT_PATH = Config.ADAPTATION_RESULTS_DIR

# ---------------------------------------------------------------------------
# Simulation settings (mirrors Config.py for local convenience)
# ---------------------------------------------------------------------------

OUTPUT_FORMAT = "csv"
SOLVER     = Config.SOLVER
START_TIME = Config.START_TIME
STOP_TIME  = Config.STOP_TIME
STEP_COUNT = Config.STEP_COUNT
STEP_SIZE  = (int(STOP_TIME) - int(START_TIME)) / int(STEP_COUNT)
TOLERANCE  = "1e-05"

# ---------------------------------------------------------------------------
# Parameter bounds and mappings
# ---------------------------------------------------------------------------

counter = 0

# Full parameter bounds list used when optimizing without RCA pre-selection
FIXED_BOUNDS = [
    {"name": "Pipe_Input_Filter.r",                  "type": "continuous", "domain": (0.1, 1)},
    {"name": "Pipe_Input_Filter.l",                  "type": "continuous", "domain": (0.1, 1)},
    {"name": "Filter.Kvs",                           "type": "continuous", "domain": (0.1, 1)},
    {"name": "filter_clogging.height",               "type": "continuous", "domain": (0.1, 1)},
    {"name": "Pipe_Filter_Heat_Exchanger.r",         "type": "continuous", "domain": (0.1, 1)},
    {"name": "Pipe_Filter_Heat_Exchanger.l",         "type": "continuous", "domain": (0.1, 1)},
    {"name": "Heat_Exchanger.A",                     "type": "continuous", "domain": (0.1, 1)},
    {"name": "Heat_Exchanger.k_NTU",                "type": "continuous", "domain": (0.1, 1)},
    {"name": "Pipe_Heat_Exchanger_Choke_Valve.r",    "type": "continuous", "domain": (0.1, 1)},
    {"name": "Pipe_Heat_Exchanger_Choke_Valve.l",    "type": "continuous", "domain": (0.1, 1)},
    {"name": "Choke_Valve.Kvs",                      "type": "continuous", "domain": (0.1, 1)},
    {"name": "Heat_Loss_Choke_Valve.alpha",          "type": "continuous", "domain": (0.1, 1)},
    {"name": "corrective_factor.k",                  "type": "continuous", "domain": (0.1, 1)},
    {"name": "Pipe_Choke_Valve_Output.r",            "type": "continuous", "domain": (0.1, 1)},
    {"name": "Pipe_Choke_Valve_Output.l",            "type": "continuous", "domain": (0.1, 1)},
    {"name": "ThreeWayValve.p_ref",                  "type": "continuous", "domain": (0.1, 1)},
    {"name": "Pipe_Water_pre_Heat_Exchanger.r",      "type": "continuous", "domain": (0.1, 1)},
    {"name": "Pipe_Water_pre_Heat_Exchanger.l",      "type": "continuous", "domain": (0.1, 1)},
    {"name": "Pipe_Water_post_Heat_Exchanger.r",     "type": "continuous", "domain": (0.1, 1)},
    {"name": "Pipe_Water_post_Heat_Exchanger.l",     "type": "continuous", "domain": (0.1, 1)},
]

# Physically motivated parameter bounds used in the GUI-driven optimization workflow
MANUAL_BOUNDS = {
    "corrective_factor.k":               (-32.5, -17.5),
    "Heat_Loss_Choke_Valve.alpha":        (56, 104),
    "Heat_Exchanger.A":                   (3.5, 11),
    "Heat_Exchanger.k_NTU":             (70, 130),
    "Choke_Valve.Kvs":                    (28, 52),
    "Filter.Kvs":                         (700, 1300),
    "filter_clogging.height":             (-0.3, 0.3),
    "ThreeWayValve.p_ref":              (70000.0, 300000.0),
    "Pipe_Water_pre_Heat_Exchanger.r":    (0.004, 0.006),
    "Pipe_Water_pre_Heat_Exchanger.l":    (0.959, 1.781),
    "Pipe_Water_post_Heat_Exchanger.r":   (0.00364, 0.00676),
    "Pipe_Water_post_Heat_Exchanger.l":   (0.959, 1.781),
}

# Nominal (original) parameter values — the model is reset to these before each optimization run
ORIGINAL_PARAMETER_VALUES = {
    "Pipe_Input_Filter.r":               0.0052,
    "Pipe_Input_Filter.l":               0.1,
    "Filter.Kvs":                        1000,
    "filter_clogging.height":            0,
    "Pipe_Filter_Heat_Exchanger.r":      0.0052,
    "Pipe_Filter_Heat_Exchanger.l":      1.27,
    "Heat_Exchanger.A":                  5,
    "Heat_Exchanger.k_NTU":            100,
    "Pipe_Heat_Exchanger_Choke_Valve.r": 0.0052,
    "Pipe_Heat_Exchanger_Choke_Valve.l": 2.048,
    "Choke_Valve.Kvs":                   40,
    "Heat_Loss_Choke_Valve.alpha":       80,
    "corrective_factor.k":              -25,
    "Pipe_Choke_Valve_Output.r":         0.05,
    "Pipe_Choke_Valve_Output.l":         1.673,
    "ThreeWayValve.p_ref":             100000.0,
    "Pipe_Water_pre_Heat_Exchanger.r":   0.01,
    "Pipe_Water_pre_Heat_Exchanger.l":   1.37,
    "Pipe_Water_post_Heat_Exchanger.r":  0.0052,
    "Pipe_Water_post_Heat_Exchanger.l":  1.37,
}

# Mapping from Modelica simulation variable names to the corresponding sensor column names
# in the real-plant dataset CSV
REAL_COLUMNS_MAPPING = {
    "Multisensor_Input.T":                    "Multisensor_Input.T",
    "Multisensor_post_Heat_Exchanger.T":      "Multisensor_post_Heat_Exchanger.T",
    "Multisensor_Output.T":                   "Multisensor_Output.T",
    "Multisensor_Water_Pre_Heat_Exchanger.T": "Multisensor_Water_Pre_Heat_Exchanger.T",
    "Multisensor_Water_Post_Heat_Exchanger.T":"Multisensor_Water_Post_Heat_Exchanger.T",
    "Multisensor_Input.p":                    "Multisensor_Input.p",
    "Filter.dp":                              "Filter.dp",
    "Multisensor_Output.p":                   "Multisensor_Output.p",
    "Multisensor_Output.m_flow":              "Multisensor_Output.m_flow",
}
