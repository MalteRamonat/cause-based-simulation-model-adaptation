"""
Constants and string literals for the AVEDAS Root Cause Analysis system.
This module centralizes all magic strings and constants to improve maintainability.
"""

# Carrier Types - State Variables
class CarrierTypes:
    TEMPERATURE = "Temperature"
    PRESSURE = "Pressure"
    FLOW = "Flow"
    LEVEL = "Level"
    POWER = "Power"
    STATE = "State"
    HIERARCH = "hierarch"
    
    # Measurement Types
    MEASUREMENT_TEMPERATURE = "Measurement_Temperature"
    MEASUREMENT_PRESSURE = "Measurement_Pressure"
    MEASUREMENT_FLOW = "Measurement_Flow"
    MEASUREMENT_LEVEL = "Measurement_Level"
    MEASUREMENT_STATE = "Measurement_State"
    MEASUREMENT_POWER = "Measurement_Power"
    
    # Parameter Types
    HEIGHT = "Height"
    ROTATIONAL_SPEED = "Rotational_Speed"
    PUMP_VOLUME = "PumpVolume"
    AREA = "Area"
    LENGTH = "Length"
    DIAMETER = "Diameter"
    ROUGHNESS = "Roughness"
    HDIFF = "HDiff"
    PDROP_NOM = "PDropNom"
    MF_NOMINAL = "MFNominal"
    
    # Gas-specific parameters
    CLOGGING = "Clogging"
    HLOSS = "HLoss"
    PRIMARY_CA = "Primary_CA"
    PRIMARY_HTRANSFER = "Primary_HTransfer"
    SECONDARY_CSURFACE = "Secondary_CSurface"
    SECONDARY_HEATT = "Secondary_HeatT"
    ALPHA = "Alpha"

# Edge Types
class EdgeTypes:
    HAS_PARENT = "hasparent"
    HAS_CHILD = "haschild"
    PRODUCT = "Product"
    IS_ALARM = "isalarm"
    HAS_ALARM = "hasalarm"
    HASH_HIERARCHY_PARENT = "hashierarchieparent"
    MIXED = "mixed"

# AML XML Namespaces and Tags
class AMLTags:
    NAMESPACE = "{http://www.dke.de/CAEX}"
    INTERNAL_ELEMENT = f"{NAMESPACE}InternalElement"
    ATTRIBUTE = f"{NAMESPACE}Attribute"
    EXTERNAL_INTERFACE = f"{NAMESPACE}ExternalInterface"
    INTERNAL_LINK = f"{NAMESPACE}InternalLink"

# Interface Suffixes
class InterfaceSuffixes:
    OUT = "_OUT"
    IN = "_IN"
    INOUT = "_INOUT"

# Colors for Graph Visualization
class NodeColors:
    TEMPERATURE = "red"
    PRESSURE = "green"
    FLOW = "blue"
    LEVEL = "yellow"
    STATE = "gray"
    HIERARCH = "lightgray"
    HAS_PARENT = "orange"
    HAS_CHILD = "purple"
    PRODUCT = "cyan"
    HAS_ALARM = "pink"
    IS_ALARM = "brown"
    THERMAL_CONNECTION = "olive"
    CONTROL = "navy"
    PUMP_ROTATIONAL_SPEED = "teal"
    PRESSURE_DROP_NOMINAL = "gold"
    DIAMETER = "darkgreen"
    HEIGHT_DIFFERENCE = "darkred"
    ROUGHNESS = "darkblue"
    LENGTH = "darkorange"
    AREA = "darkviolet"
    MF_NOMINAL = "darkgray"
    CLOGGING = "darkviolet"
    CSURFACE = "darkorange"
    HTRANSFER = "darkred"
    HLOSS = "darkgreen"
    ALPHA = "darkviolet"
    DEFAULT = "slategray"

# Rule Probabilities
class RuleProbabilities:
    HIGH = 0.99
    MEDIUM = 0.7
    LOW = 0.3

# Processing Constants
class ProcessingConstants:
    DEFAULT_DECAY_FACTOR = 0.001
    DEFAULT_ABORT_TIME = 400
    MIN_EDGE_WEIGHT = 0.01
    MAX_PATH_LENGTH = 20
    TOP_PARAMETERS_COUNT = 60
    MIN_CUTOFF_THRESHOLD = 0.1

# File Extensions and Patterns
class FileConstants:
    EXCEL_EXTENSION = ".xlsx"
    CSV_EXTENSION = ".csv"
    HTML_EXTENSION = ".html"
    
# Valve History Settings
class ValveConstants:
    DEFAULT_HISTORY_LENGTH = 3
    DEFAULT_VALVE_STATE = 1.0
    VALVE_STATE_SUFFIX = "_State"

# Matrix Calculation Settings
class MatrixConstants:
    DIAGONAL_VALUE_DISTANCE = 0
    DIAGONAL_VALUE_STATEVARIABLE = 1
    MIN_FACTOR_INFLUENCE = 0.1
    NEUTRAL_INFLUENCE_POWER = 0.9
    RANGE_INFLUENCE_POWER = 1.1

# String Replacement Patterns
class StringPatterns:
    V_TO_YIC = ("V", "YIC")
    UNDERSCORE_TO_MEASUREMENT = ("_", "_Measurement_")
    STATE_SUFFIX = "_State"
    
# Multiprocessing Settings
class MultiprocessingConstants:
    DEFAULT_MAX_PROCESSES = 8
    CHUNK_SIZE_MULTIPLIER = 2
