"""
AVEDAS Root Cause Analysis — modular package.

Modules:
- components.analysis_engine: Central analysis engine
- components.graph_builder: Graph construction and AML parsing
- components.parallel_matrix: Parallel matrix computation
- components.valve_manager: Valve management
- config.constants: Central constants and types
- config.rules: External rule configuration

Main classes:
- AnalysisEngine: Orchestrates the full analysis pipeline
- GraphBuilder: Builds graphs from AML files
- ParallelMatrixCalculator: Multiprocessing for matrix computations
- EnhancedValve: Valve implementation with history-based weighting
- ValveManager: Manages multiple valve instances
"""

__version__ = "2.0.0"
__author__ = "AVEDAS Development Team"

from components.analysis_engine import AnalysisEngine
from components.graph_builder import GraphBuilder
from components.parallel_matrix import ParallelMatrixCalculator
from components.valve_manager import EnhancedValve, ValveManager

from config.constants import CarrierTypes, ValveConstants, ProcessingConstants
from config.rules import RuleSetManager, GraphRule

try:
    from main_analysis import AvedasAnalysis
except ImportError:
    AvedasAnalysis = None

__all__ = [
    'AnalysisEngine',
    'GraphBuilder',
    'ParallelMatrixCalculator',
    'EnhancedValve',
    'ValveManager',
    'CarrierTypes',
    'ValveConstants',
    'ProcessingConstants',
    'RuleSetManager',
    'GraphRule',
    'AvedasAnalysis'
]
