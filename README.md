# Cause-Based Simulation Model Adaptation (CBSMA)

This project is a Digital Twin pipeline that detects deviations between a physics
simulation model and real plant sensor data, identifies their root cause, and
automatically adapts the model parameters to minimize the deviations.

The pipeline is organized into three successive artefacts:

| Artefact | Entry point | Purpose |
|----------|-------------|---------|
| 1 | `Scripts/Artefact_1/Comparison_Main.py` | Compare sensor data against Modelica simulation output (MAE, sMAPE per channel) |
| 2 | `Scripts/Artefact_2/root_cause_main.py` | Propagate deviation signals through an AutomationML dependency graph to rank simulation parameters by causal influence |
| 3 | `Scripts/Artefact_3/Parameter_Adaptation_Main.py` | Run Bayesian optimization (GPyOpt) to adapt the top-ranked parameters until the simulation matches reality |

The pipeline has been validated on two OpenModelica simulation models — see **Simulation Models** below.

---

## Simulation Models

### ModVA — Fluid Mixing Plant (`modva_online_stable`)

A Modelica model of a laboratory-scale fluid mixing plant with interconnected tanks,
valves, pumps, and analogue flow and level sensors. The plant layout, sensor
configuration, and a labelled anomaly benchmark dataset are described at:
https://github.com/MalteRamonat/fluid-mixing-anomaly-benchmark

### TFS Gasentspannung — Natural Gas Pressure Reduction Station (`TFS_Gasentspannung`)

A Modelica model of a pressure reduction subsystem inside a natural gas storage
facility. High-pressure gas arriving from the distribution grid is throttled to a
lower delivery pressure by a choke valve and a three-way control valve. The station
includes sensors for inlet and outlet pressure, volumetric flow rate, and temperature.
The model captures steady-state and transient pressure dynamics, including the effects
of valve clogging, leakage, sensor faults, and reconfiguration events.

To select the active model, set `MODELICA_MODEL_NAME` in `Scripts/Config.py`.

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.10+ | |
| OpenModelica 1.21+ | Required for Artefacts 1 and 3 (simulation runs) |
| Git | |

---

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd Cause-Based-Simulation-Model-Adaptation

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# 3. Install dependencies
pip install -r requirements.txt
pip install -e .               # makes cross-package imports work without sys.path hacks

# 4. Configure paths (see below)
#    Edit Scripts/Config.py if your datasets live in a non-default location.

# 5. Run Artefact 1 — deviation detection
python Scripts/Artefact_1/Comparison_Main.py
```

---

## Configuration

All paths and model settings are controlled by a single file: [`Scripts/Config.py`](Scripts/Config.py).

After cloning, all paths are derived automatically from the repository root via `PROJECT_ROOT`.
The only variables you typically need to change are:

| Variable | Default | Description |
|----------|---------|-------------|
| `MODELICA_MODEL_NAME` | `"TFS_Gasentspannung"` | Active model: `"TFS_Gasentspannung"` (gas station) or `"modva_online_stable"` (fluid mixing plant) |
| `CURRENT_DATASET_PATH` | `datasets/RAG/Synthetic_Sensors/…` | Real-plant CSV used for comparison |
| `RCA_RESULT_FILE` | `RCA_Results/parameter_influence_testcase_5.csv` | RCA output consumed by Artefact 3 |

---

## Repository Structure

```
Cause-Based-Simulation-Model-Adaptation/
├── Modelica/                          # OpenModelica model files (.mo)
│   ├── TFS_Gasentspannung.mo
│   ├── Current_Model_Build/           # Generated build artefacts (git-ignored)
│   └── Timetables/                    # Actuator input CSV files
│
├── Scripts/
│   ├── Config.py                      # Central configuration (all paths + constants)
│   ├── sensor_simvar_mapping.py       # OPC UA node ID ↔ Modelica variable mapping
│   ├── OMPython_Functionalities.py    # OpenModelica interface helpers
│   ├── run_GUI.py                     # GUI entry point
│   │
│   ├── Artefact_1/                    # Deviation detection
│   │   ├── Comparison_Main.py         # ← entry point
│   │   ├── Data_Preparation.py
│   │   ├── Deviation_Detection.py
│   │   ├── Model_Initialization.py
│   │   └── Resources/                 # Required input CSVs (committed)
│   │
│   ├── Artefact_2/                    # Root cause analysis
│   │   ├── root_cause_main.py         # ← entry point
│   │   ├── Arroyo_DCDG_PLUT.py        # DCDG graph engine
│   │   ├── A2_Utilities.py
│   │   └── Resources/                 # AML file, designation tables, test cases
│   │
│   └── Artefact_3/                    # Bayesian parameter adaptation
│       ├── Parameter_Adaptation_Main.py  # ← entry point
│       ├── Bayesian_Main.py           # GPyOpt objective function + optimizer
│       ├── Bayesian_Functions.py      # Simulation helpers
│       └── Bayesian_Config.py         # Artefact-3-specific paths and bounds
│
├── datasets/                          # Plant measurement data (git-ignored)
├── Comparison_Results/                # Artefact 1 output (git-ignored)
├── RCA_Results/                       # Artefact 2 output (git-ignored)
├── Adaptation_Results/                # Artefact 3 output (git-ignored)
│
├── requirements.txt
├── pyproject.toml
└── .gitignore
```

---

## Dataset

The `datasets/` directory is not committed to the repository (see `.gitignore`).
The required structural input files for Artefact 1 and Artefact 2 are committed under:
- `Scripts/Artefact_1/Resources/` — actuator/sensor input condition CSVs
- `Scripts/Artefact_2/Resources/` — AutomationML plant description, designation tables, test-case Excel files

---

## Running Each Artefact

### Artefact 1 — Deviation Detection

```bash
python Scripts/Artefact_1/Comparison_Main.py
```

Produces:
- `Comparison_Results/comparison_result_unscaled.csv`
- `Comparison_Results/comparison_result_scaled.csv`
- Per-signal comparison plots (PNG) and an interactive HTML chart

### Artefact 2 — Root Cause Analysis

```bash
python Scripts/Artefact_2/root_cause_main.py
```

Requires: deviation and residual Excel files for each test case in
`Scripts/Artefact_2/Resources/Testcases/GAS_Testcases/`.

Produces: `RCA_Results/parameter_influence_testcase_<N>.csv`

### Artefact 3 — Parameter Adaptation

```bash
python Scripts/Artefact_3/Parameter_Adaptation_Main.py
```

Requires: RCA result CSV (set `RCA_RESULT_FILE` in `Config.py`) and a running
OpenModelica installation.

Produces: convergence plots and optimized parameter values in `Adaptation_Results/`.

---

## License

This project is released for academic and research purposes.
