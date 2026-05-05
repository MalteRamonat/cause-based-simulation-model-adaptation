# AVEDAS Root Cause Analysis — Modular Version

This modular version of the AVEDAS Root Cause Analysis system provides a
maintainable, extensible, and performant alternative to the original script.

## Overview

The system has been restructured with the following improvements:
- **Modular architecture** with clear separation of responsibilities
- **Multiprocessing support** for matrix computations
- **External configuration** of rules and constants
- **No magic strings** — all constants are managed centrally
- **Improved maintainability** through clean class structures
- **Parallel timestep processing** support

## Architecture

```
Scripts/Artefact_2/
├── main_analysis.py          # New entry point (replaces root_cause_main.py)
├── config/
│   ├── constants.py          # Central constants and types
│   └── rules.py              # External rule configuration
└── components/
    ├── analysis_engine.py    # Main analysis engine
    ├── graph_builder.py      # Graph construction and AML parsing
    ├── parallel_matrix.py    # Parallel matrix computations
    └── valve_manager.py      # Valve state management
```

## Core Components

### 1. AnalysisEngine (`components/analysis_engine.py`)
The central engine orchestrates the entire analysis process:
- Graph initialization from AML
- System state updates
- Matrix computations (parallel / sequential)
- Parameter ranking
- Export functionality

### 2. GraphBuilder (`components/graph_builder.py`)
Responsible for building the analysis graph:
- AML parsing via lxml
- Hierarchy construction
- Attribute and interface processing
- External rule application
- Valve initialization

### 3. ParallelMatrixCalculator (`components/parallel_matrix.py`)
Provides multiprocessing for matrix computations:
- Parallel Dijkstra computations
- Parameter matrix calculation
- State-variable matrix calculation
- Timestep batch processing

### 4. ValveManager (`components/valve_manager.py`)
Encapsulates valve logic:
- Valve state management
- Weight calculation
- Graph integration

### 5. External Configuration (`config/`)
- **constants.py**: All magic strings, types, and colors as classes/enums
- **rules.py**: Data-driven rule set for graph construction

## Usage

### Basic Usage

```bash
# Simple analysis
python main_analysis.py --aml path/to/model.aml

# With parallel computation (default)
python main_analysis.py --aml path/to/model.aml --parallel

# With sequential computation
python main_analysis.py --aml path/to/model.aml --sequential

# With result export
python main_analysis.py --aml path/to/model.aml --export results
```

### Programmatic Usage

```python
from components.analysis_engine import AnalysisEngine

engine = AnalysisEngine(max_processes=4)
engine.initialize_from_aml("model.aml")

engine.update_system_state(
    valve_states={"XV_101_State": 50.0},
    alarm_states={"YIC_101_Measurement": 1},
    deviations={"YIC_101_Measurement": -2.5},
)

matrices = engine.compute_influence_matrices(use_parallel=True)
ranking  = engine.get_parameter_ranking(top_n=10)
summary  = engine.get_analysis_summary()
engine.export_matrices("output_prefix")
```

## System Requirements

- Python 3.10+
- Required packages:
  ```
  igraph
  numpy
  pandas
  lxml
  openpyxl  # optional, for Excel export
  ```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Import errors | Verify all dependencies are installed |
| AML parsing errors | Check the AML file for syntax issues |
| Memory issues | Reduce `max_processes` or switch to sequential mode |
| Path errors | Use absolute paths for AML files |

## Comparison with Legacy System

| Feature | Legacy | Modular |
|---------|--------|---------|
| Architecture | Monolithic | Modular |
| Constants | Magic strings | Centrally configured |
| Rules | Hardcoded | Externally configurable |
| Parallelization | Limited | Full multiprocessing |
| Maintainability | Difficult | Easy |
| Performance | Sequential | Parallel-optimized |
