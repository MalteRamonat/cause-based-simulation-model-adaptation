"""
Central configuration for the AVEDAS pipeline.

All paths are resolved relative to the repository root so the project works
on any machine after cloning. To run on a new machine, only the dataset paths
in the 'OPC UA / Dataset Paths' section need to be adjusted.

Sections:
    - Simulation Configuration: Modelica model name, solver settings, result paths
    - Sensor-Simulation Mapping: Input tables and mapping file paths
    - OPC UA / Dataset Paths: Paths to real plant measurement CSV files
    - Root Cause Analysis: AML file, designation tables, test case configuration
    - Parameter Adaptation: Mapping between AML and simulation parameter names
    - Anomaly Detection: OPC UA node naming and sensor/actuator column lists
"""

from pathlib import Path
from typing import Optional
import tempfile

# ---------------------------------------------------------------------------
# Repository root anchor — all other paths derive from here.
# Config.py lives in Scripts/, so the project root is one level up.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Simulation Configuration
# ---------------------------------------------------------------------------

# Temporary directory where OpenModelica writes its output during simulation
TEMP_PATH = Path(tempfile.gettempdir()) / "OpenModelica"

# Directory containing the active Modelica model files
MODELICA_FILE_DIR = PROJECT_ROOT / "Modelica"

# Subdirectory where OpenModelica places the compiled model build
MODEL_BUILD_DIR = MODELICA_FILE_DIR / "Current_Model_Build"

# Backup location for the Modelica source file
MODELICA_BACKUP_DIR = MODELICA_FILE_DIR / "Model_Backup"

# Active model name — switching between models only requires changing this value
MODELICA_MODEL_NAME = "TFS_Gasentspannung"  # alternative: "ModVA_online_stable"

# Derived file names
MODELICA_FILE_NAME = f"{MODELICA_MODEL_NAME}.mo"
RESULT_FILE_NAME = f"{MODELICA_MODEL_NAME}.csv"

# Directory where simulation result CSV files are stored after each run
SIMULATION_RESULTS_DIR = PROJECT_ROOT / "datasets" / "Simulation"

# Directory where Modelica reads the actuator time-table CSV files from
MODELICA_TIMETABLES_DIR = MODELICA_FILE_DIR / "Timetables"

# Solver settings
SOLVER = "dassl"
START_TIME = "0"
STOP_TIME = "1000"
STEP_COUNT = "500"

# ---------------------------------------------------------------------------
# Sensor-Simulation Mapping
# ---------------------------------------------------------------------------

# Excel file mapping OPC UA sensor node IDs to simulation variable names
MAPPING_TABLE_PATH = PROJECT_ROOT / "TFS_Gasentspannung_Sensor_SimVar_Mapping.xlsx"

# Name of the Modelica component that drives all actuator signals
MODEL_CONTROL_BLOCK_NAME = "ActuatorControl"

# Order in which actuator outputs are connected to the ActuatorControl block:
# y[1]:V201, y[2]:V202, y[3]:V203, y[4]:V206, y[5]:V205, y[6]:V204, y[7]:V209,
# y[8]:P201, y[9]:P202
ACTUATOR_ORDER_IN_MODELICA = ["V201", "V202", "V203", "V206", "V205", "V204", "V209", "P201", "P202"]

# Manual initialization input tables (used when initializing from an Excel actuator matrix)
ACTUATOR_EXCEL_TABLE_PATH = PROJECT_ROOT / "Manual_Actuator_Matrix_ModVA.xlsx"
ACTUATOR_TIME_COLUMN = "time_sec"
SENSOR_CSV_TABLE_PATH = PROJECT_ROOT / "Manual_Sensor_Matrix_ModVA.csv"

# Gas model input condition CSV files (read by Modelica CombiTimeTable blocks)
_ARTEFACT1_RESOURCES = PROJECT_ROOT / "Scripts" / "Artefact_1" / "Resources"
INPUT_TABLE_FILES = {
    "Input_Conditions":       _ARTEFACT1_RESOURCES / "input_conditions.csv",
    "Water_Input_Conditions": _ARTEFACT1_RESOURCES / "water_input_conditions.csv",
    "ThreeWayValve_Input":    _ARTEFACT1_RESOURCES / "threewayvalve_input.csv",
    "Choke_Valve_Input":      _ARTEFACT1_RESOURCES / "choke_valve_input.csv",
}

# ---------------------------------------------------------------------------
# Comparison / Deviation Detection Output Paths
# ---------------------------------------------------------------------------

COMPARISON_RESULTS_DIR = PROJECT_ROOT / "Comparison_Results"
COMPARISON_RESULT_FILE_UNSCALED = COMPARISON_RESULTS_DIR / "comparison_result_unscaled.csv"
COMPARISON_RESULT_FILE_SCALED   = COMPARISON_RESULTS_DIR / "comparison_result_scaled.csv"
COMPARISON_ACTUATOR_POSITIONS_FILE = COMPARISON_RESULTS_DIR / "actuator_positions.csv"

# Column groups used to select which signals are included in each plot
PLOT_COLUMNS_GAS_TEMPERATURE = [
    "Temperature_Gas_Input_real",                    "Temperature_Gas_Input_sim",                    "Temperature_Gas_Input_mae",
    "Temperature_Gas_after_Heat_Exchanger_real",     "Temperature_Gas_after_Heat_Exchanger_sim",     "Temperature_Gas_after_Heat_Exchanger_mae",
    "Temperature_Gas_after_Choke_Valve_real",        "Temperature_Gas_after_Choke_Valve_sim",        "Temperature_Gas_after_Choke_Valve_mae",
]

PLOT_COLUMNS_WATER_TEMPERATURE = [
    "Temperature_Water_pre_Heat_Exchanger_real",     "Temperature_Water_pre_Heat_Exchanger_sim",     "Temperature_Water_pre_Heat_Exchanger_mae",
    "Temperature_Water_after_Heat_Exchanger_real",   "Temperature_Water_after_Heat_Exchanger_sim",   "Temperature_Water_after_Heat_Exchanger_mae",
]

PLOT_COLUMNS_GAS_PRESSURE = [
    "Pressure_Gas_Input_real",                       "Pressure_Gas_Input_sim",                       "Pressure_Gas_Input_mae",
    "Pressure_Gas_after_Choke_Valve_real",           "Pressure_Gas_after_Choke_Valve_sim",           "Pressure_Gas_after_Choke_Valve_mae",
]

PLOT_COLUMNS_GAS_FLOW = [
    "Flow_Gas_after_Choke_Valve_real",               "Flow_Gas_after_Choke_Valve_sim",               "Flow_Gas_after_Choke_Valve_mae",
]

# ---------------------------------------------------------------------------
# OPC UA / Dataset Paths
# ---------------------------------------------------------------------------

# Unused database credentials (kept for future live-connection support)
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = ""
DB_USER = ""

# Root directory for synthetic real-plant measurement CSV files
OPCUA_DATASETS_DIR = PROJECT_ROOT / "datasets" / "RAG" / "Synthetic_Sensors"

ANOMALIES_DIR = OPCUA_DATASETS_DIR / "Anomalies"
ANOMALY_FILES = [
    "TFS_Gasentspannung_filter_gradual_clogging.csv",
    "TFS_Gasentspannung_threewayvalve_leakiness.csv",
    "TFS_Gasentspannung_reconfiguration.csv",
]

# Active dataset used as the real-plant input for the comparison pipeline
CURRENT_DATASET_PATH = OPCUA_DATASETS_DIR / "Kalibrierung_Showcase" / "Gasentspannung_Synthetische_Realdaten_2.csv"

# ---------------------------------------------------------------------------
# Anomaly Detection — data paths
# ---------------------------------------------------------------------------

NORMAL_PLANT_DATA = OPCUA_DATASETS_DIR / "Datensatz42_Volle_Tanks_10min_dauerhafter_Durchlauf.csv"

HISTORICAL_PLANT_DATA = [
    OPCUA_DATASETS_DIR / "Datensatz21_Volle_Tanks_10min_dauerhafter_Durchlauf.csv",
    OPCUA_DATASETS_DIR / "Datensatz22_Volle_Tanks_10min_dauerhafter_Durchlauf.csv",
    OPCUA_DATASETS_DIR / "Datensatz23_Volle_Tanks_10min_dauerhafter_Durchlauf.csv",
    OPCUA_DATASETS_DIR / "Datensatz31_Volle_Tanks_10min_dauerhafter_Durchlauf_grossesLeck.csv",
]

# Autoencoder training / test data lives outside this repository.
# Set these paths to the external data directory before running anomaly_detection.py.
AUTOENCODER_TRAIN_DIR: Optional[Path] = None
AUTOENCODER_TEST_DIR: Optional[Path] = None

# ---------------------------------------------------------------------------
# Root Cause Analysis (Artefact 2)
# ---------------------------------------------------------------------------

_ARTEFACT2_RESOURCES = PROJECT_ROOT / "Scripts" / "Artefact_2" / "Resources"

# AutomationML system description file used to build the dependency graph
AML_FILE = _ARTEFACT2_RESOURCES / "Gas_Entspannungsstrecke_incl_SensorNamingConvention.aml"

# Excel file listing sensor/actuator designations in the order they appear in test-case sheets
RCA_DESIGNATIONS = _ARTEFACT2_RESOURCES / "GAS_Designations.xlsx"

# Mapping between the column names used in Artefact 1 comparison results and RCA designations
MAPPING_FILE_COMPARISON_TO_RCA = _ARTEFACT2_RESOURCES / "GAS_Mapping_between_Comparison_and_RCA.xlsx"

# Output path for the initial graph HTML (generated once for visual inspection)
RCA_INITIAL_GRAPH_OUTPUT = _ARTEFACT2_RESOURCES / "Testcases" / "GAS_Testcases" / "Graph_GAS_after_generation.html"

# File names for the per-test-case Excel input sheets
RESIDUAL_OUTPUT_FILE = "GAS_residual_adjusted.xlsx"
DEVIATION_OUTPUT_FILE = "GAS_deviation_adjusted.xlsx"
ACTUATOR_OUTPUT_FILE  = "XMV.xlsx"

# Residuals above this threshold are treated as a deviation signal (dimensionless, 0–1 scale)
TOLERANCE_THRESHOLD = 0.01

# Directory containing the numbered test-case sub-folders
TESTCASE_DIRECTORY = _ARTEFACT2_RESOURCES / "Testcases" / "GAS_Testcases"

# Test cases to process (folder names relative to TESTCASE_DIRECTORY)
TESTCASE_DIR_LIST = [
    "Testcase_5",
]

# Number of sensors and actuators in the GAS model
NUMBER_OF_SENSORS   = 9   # 5 temperature + 3 pressure + 1 flow
NUMBER_OF_ACTUATORS = 2   # choke valve + three-way valve

# Ground-truth parameters changed in each test case (for evaluation / benchmarking)
CHANGED_PARAMETERS = {
    "Testcase_2": "filter_clogging.height",
    "Testcase_3": "ThreeWayValve.relativeLeakiness",
    "Testcase_4": "Reconfiguration: Sink before Filter",
    "Testcase_5": "Heat_Exchanger_HeatT, Pipe_Choke_Valve_Output_Alpha",
}

# RCA algorithm tuning constants
RCA_DECAY_FACTOR     = 0.001  # Exponential time-weighting: weights early timesteps more heavily (e^(-t * factor))
RCA_ABORT_TIMESTEP   = 100    # Stop processing a test case after this many timesteps
RCA_TOP_N_PARAMETERS = 60     # Number of top-ranked parameters written to the result CSV

# ---------------------------------------------------------------------------
# RCA Output
# ---------------------------------------------------------------------------

RCA_RESULTS_DIR  = PROJECT_ROOT / "RCA_Results"
RCA_RESULT_FILE  = RCA_RESULTS_DIR / "parameter_influence_testcase_5.csv"

# ---------------------------------------------------------------------------
# Parameter Adaptation (Artefact 3)
# ---------------------------------------------------------------------------

_ARTEFACT3_RESOURCES = PROJECT_ROOT / "Scripts" / "Artefact_3" / "Resources"

# Mapping between AML component names and Modelica simulation parameter paths
RCA_AML_TO_SIMULATION_FILEPATH = _ARTEFACT3_RESOURCES / "Mapping_of_AML_and_Simulation_Parameters_GAS.xlsx"

ADAPTATION_RESULTS_DIR = PROJECT_ROOT / "Adaptation_Results"

# ---------------------------------------------------------------------------
# Anomaly Detection — OPC UA node naming (ModVA plant)
# ---------------------------------------------------------------------------

_ROOT_NODE       = "ns=4;s=|var|WAGO 750-8212 PFC200 G2 2ETH RS.Application."
_NODE_GLOBAL_VAR = "IoConfig_Globals_Mapping."
_NODE_APP_CONV   = "Umrechnung_Analogsensorik."

# Columns to subscribe to / read from the OPC UA server
COLUMNS_TO_KEEP = [
    _ROOT_NODE + _NODE_GLOBAL_VAR + "LA201",          # Level sensor 1
    _ROOT_NODE + _NODE_GLOBAL_VAR + "LA202",          # Level sensor 2
    _ROOT_NODE + _NODE_GLOBAL_VAR + "LA203",          # Level sensor 3
    _ROOT_NODE + _NODE_GLOBAL_VAR + "LA204",          # Level sensor 4
    _ROOT_NODE + _NODE_GLOBAL_VAR + "LA205",          # Level sensor 5
    _ROOT_NODE + _NODE_GLOBAL_VAR + "LA210",          # Level sensor 6
    _ROOT_NODE + _NODE_GLOBAL_VAR + "LA220",          # Level sensor 7
    _ROOT_NODE + _NODE_GLOBAL_VAR + "LA230",          # Level sensor 8
    _ROOT_NODE + _NODE_GLOBAL_VAR + "LA240",          # Level sensor 9
    _ROOT_NODE + _NODE_APP_CONV   + "VolumeB201",     # Fluid volume in ml
    _ROOT_NODE + _NODE_APP_CONV   + "VolumeB202",     # Fluid volume in ml
    _ROOT_NODE + _NODE_APP_CONV   + "VolumeB203",     # Fluid volume in ml
    _ROOT_NODE + _NODE_APP_CONV   + "VolumeB204",     # Fluid volume in ml
    _ROOT_NODE + _NODE_APP_CONV   + "DruckB201",      # Pressure in kPa
    _ROOT_NODE + _NODE_APP_CONV   + "DruckB202",      # Pressure in kPa
    _ROOT_NODE + _NODE_APP_CONV   + "DruckB203",      # Pressure in kPa
    _ROOT_NODE + _NODE_APP_CONV   + "DruckB204",      # Pressure in kPa
    _ROOT_NODE + _NODE_APP_CONV   + "Temperatur261",  # Temperature in °C
    _ROOT_NODE + _NODE_APP_CONV   + "Temperatur262",  # Temperature in °C
    _ROOT_NODE + _NODE_APP_CONV   + "FlowP201",       # Flow FI271 in l/min
    _ROOT_NODE + _NODE_APP_CONV   + "FlowP202",       # Flow FI272 in l/min
    _ROOT_NODE + _NODE_GLOBAL_VAR + "V201_Control",   # Digital output V201
    _ROOT_NODE + _NODE_GLOBAL_VAR + "V202_Control",   # Digital output V202
    _ROOT_NODE + _NODE_GLOBAL_VAR + "V203_Control",   # Digital output V203
    _ROOT_NODE + _NODE_GLOBAL_VAR + "V204_Control",   # Digital output V204
    _ROOT_NODE + _NODE_GLOBAL_VAR + "V205_Control",   # Digital output V205
    _ROOT_NODE + _NODE_GLOBAL_VAR + "V206_Control",   # Digital output V206
    _ROOT_NODE + _NODE_GLOBAL_VAR + "V209_Control",   # Digital output V209
    _ROOT_NODE + _NODE_GLOBAL_VAR + "P201_Control",   # Digital output P201
    _ROOT_NODE + _NODE_GLOBAL_VAR + "P202_Control",   # Digital output P202
    _ROOT_NODE + _NODE_GLOBAL_VAR + "R201_Control",   # Digital output R201
]

# Column used to detect the start index of active plant operation
COLUMN_FOR_START_IDX = _ROOT_NODE + _NODE_GLOBAL_VAR + "V201_Control"

# ---------------------------------------------------------------------------
# Data preprocessing constants
# ---------------------------------------------------------------------------

OUTLIER_FILTER_KERNEL_SIZE  = 5    # Median filter kernel size for level sensor outlier removal
OUTLIER_FILTER_THRESHOLD    = 3    # Standard deviations above mean to classify as outlier
NOISE_REDUCTION_WINDOW      = 10   # Rolling window size for sensor noise smoothing
NOISE_REDUCTION_THRESHOLD   = 1.5  # Z-score threshold for noise spike detection
