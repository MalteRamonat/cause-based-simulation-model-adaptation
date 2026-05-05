"""
Simulation interface and objective function utilities for Bayesian optimization (Artefact 3).

Call initialize_modelica_session() once before using any simulation functions.
All functions that drive the Modelica model depend on the session initialized there.
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
import matplotlib.gridspec as gridspec
from OMPython import OMCSessionZMQ
from OMPython import ModelicaSystem
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from scipy.signal import medfilt
from Bayesian_Config import *


# Module-level session objects — populated by initialize_modelica_session()
_omc = None
_mod = None


def initialize_modelica_session():
    """Initialize the OpenModelica session and load the Modelica model.

    Must be called once before any simulation function is used.
    Keeping initialization separate from import allows this module to be imported
    in environments where OpenModelica is not installed (e.g., for unit tests).

    Returns:
        tuple: (omc, mod) — the OMC session and the loaded ModelicaSystem object.
    """
    global _omc, _mod
    _omc = OMCSessionZMQ()
    print(_omc.sendExpression("getVersion()"))
    print(_omc.sendExpression("cd()"))
    modelica_file = str(MODELICA_FILE_DIR / MODELICA_FILE_NAME)
    _omc.sendExpression(f'loadFile("{modelica_file}")')
    _omc.sendExpression(f"instantiateModel({MODELICA_MODEL_NAME})")
    _mod = ModelicaSystem(modelica_file, MODELICA_MODEL_NAME)
    _mod.setSimulationOptions([
        f"startTime={START_TIME}",
        f"stopTime={STOP_TIME}",
        f"tolerance={TOLERANCE}",
        f"stepSize={STEP_SIZE}",
        f"solver={SOLVER}",
        f"outputFormat={OUTPUT_FORMAT}",
    ])
    _mod.buildModel()
    return _omc, _mod


def simulate(resultfile):
    _mod.simulate(resultfile=resultfile, simflags="-abortSlowSimulation -noEventEmit")


def set_original_parameter(param_value, param_name):
    print(f"Resetting parameter {param_name} to original value: {param_value}")
    _mod.setParameters(f"{param_name}={param_value}")


def generate_initial_dataset():
    resultfile_initial = f"{MODELICA_MODEL_NAME}_resultInitialSim.csv"
    resultfile_path = os.path.join(DEST_PATH, resultfile_initial)

    if not os.path.exists(resultfile_path):
        print("No initial simulation found. Resetting parameters to original values and simulating.")
        for param_name, param_value in ORIGINAL_PARAMETER_VALUES.items():
            print(f"Parameter: {param_name}, value: {param_value}")
            _mod.setParameters(f"{param_name}={param_value}")
        _mod.simulate(resultfile=resultfile_initial)
        get_result_file(resultfile_initial)
    else:
        print(f"File {resultfile_initial} already exists. Skipping simulation.")


def setup_adaptation_process(index_iter, single_or_multiple="single"):
    """Set already-optimized parameters for progressive (sequential) optimization.

    Args:
        index_iter: Row index up to which parameters are applied from the
            user-defined evaluation results file.
        single_or_multiple: "single" applies parameters one at a time;
            "multiple" is not yet implemented.
    """
    evaluation_df = pd.read_csv(USER_EVALUATION_RESULTS_FILE)

    print("----------------------")
    if single_or_multiple == "single":
        for index, row in evaluation_df.iterrows():
            param_name = evaluation_df.loc[index, "Parameter"]
            param_value = evaluation_df.loc[index, "Value_after_single_Param_Optimization"]
            print(f"Parameter: {param_name}, value: {param_value}")
            _mod.setParameters(f"{param_name}={param_value}")
            if index == index_iter:
                break
    elif single_or_multiple == "multiple":
        print("Multiple progressive optimization is not yet implemented.")


def apply_unit_conversion(df, mapping):
    """Apply unit conversion to the DataFrame columns that match a known unit type.

    Args:
        df: DataFrame whose columns may need unit conversion.
        mapping: Unused — conversion factors are defined internally.

    Returns:
        DataFrame with converted values.
    """
    conversion_factors = {
        "level":  0.01,       # cm -> m
        "V_flow": 1 / 60000,  # l/min -> m³/s
    }
    for column in df.columns:
        for key, factor in conversion_factors.items():
            if key in column:
                df[column] = df[column] * factor
    return df


def initial_dataset(bounds, param_value, index_iter):
    name_value = bounds[0]["name"]
    resultfile_initial = f"{MODELICA_MODEL_NAME}_resultInitialSim_{name_value}.csv"
    resultfile_path = str(DEST_PATH / name_value) + "/"
    os.makedirs(os.path.dirname(resultfile_path), exist_ok=True)
    initial_dataset_location = os.path.join(resultfile_path, resultfile_initial)

    if not os.path.exists(initial_dataset_location):
        print(f"Parameter: {name_value}, value: {param_value}")
        _mod.setParameters(f"{name_value}={param_value}")
        _mod.simulate(resultfile=resultfile_initial)
        get_result_file(resultfile_initial, resultfile_path)
    else:
        print(f"File {resultfile_initial} already exists. Skipping simulation.")

    optimization_results_df = pd.read_csv(OPTIMIZATION_RESULTS_FILE)

    df_real, df_sim = preprocess_format_results(str(REAL_DATASET_PATH), initial_dataset_location)
    df_interpolated_sim = interpolate_simulation_results(df_real, df_sim)
    df_noisefree_real = apply_noise_reduction(df_real)

    df_merged = pd.merge(df_noisefree_real, df_interpolated_sim, on="time", suffixes=("_real", "_sim"))

    max_time = df_sim["time"].max()
    progress_sim = max_time / int(STOP_TIME)
    print(f"Simulation progress: {progress_sim * 100:.2f}%")
    progress_deviation = 1 - progress_sim

    total_scaled_mae = 0
    for process_variable in REAL_COLUMNS_MAPPING.keys():
        value_real = df_merged[f"{process_variable}_real"].values
        value_sim  = df_merged[f"{process_variable}_sim"].values
        scaled_mae = calculate_scaled_mae(value_real, value_sim)

        col = f"Deviation_of_observed_{process_variable}_before_Optimization"
        if optimization_results_df.loc[index_iter, col] > scaled_mae or \
                pd.isna(optimization_results_df.loc[index_iter, col]):
            optimization_results_df.loc[index_iter, col] = scaled_mae

        total_scaled_mae += scaled_mae * (1 / len(REAL_COLUMNS_MAPPING))
        print(f"Scaled MAE for {process_variable}: {scaled_mae}")

    total_error = total_scaled_mae + progress_deviation
    print(f"Total error for initial simulation of {name_value}: {total_error}")

    col_total = "Total_Deviation_before_Optimization"
    if optimization_results_df.loc[index_iter, col_total] > total_error or \
            pd.isna(optimization_results_df.loc[index_iter, col_total]):
        optimization_results_df.loc[index_iter, col_total] = total_error

    optimization_results_df.to_csv(OPTIMIZATION_RESULTS_FILE, index=False)


def get_result_file(file, destination=None):
    """Locate the simulation result file in the OpenModelica temp directory and move it.

    OpenModelica writes result files to a system temp directory. This function
    finds the most recently modified matching file and moves it to the destination.

    Args:
        file: File name to search for.
        destination: Target directory. Defaults to DEST_PATH if not provided.
    """
    if destination is None:
        destination = str(DEST_PATH)

    latest_file_path = None
    latest_mod_time = 0

    for root, dirs, files in os.walk(TEMP_PATH):
        for fname in files:
            if fname == file:
                full_path = os.path.join(root, fname)
                mod_time = os.path.getmtime(full_path)
                if mod_time > latest_mod_time:
                    latest_mod_time = mod_time
                    latest_file_path = full_path

    if latest_file_path:
        destination_file_path = os.path.join(destination, file)
        shutil.move(latest_file_path, destination_file_path)


def set_parameters(params, bounds):
    """Set simulation parameters, expanding grouped parameters where applicable.

    Grouped parameters allow a single optimization variable to control multiple
    Modelica parameters simultaneously (configured in Grouped_Parameters.csv).

    Args:
        params: 2-D numpy array of parameter values from the Bayesian optimizer.
        bounds: List of bound dicts, each with a 'name' key.
    """
    grouped_params_df = pd.read_csv(GROUPED_PARAMETERS_FILE)

    for i, bound in enumerate(bounds):
        param_name  = bound["name"]
        param_value = params[0, i] if params.shape[1] > 1 else params[0, 0]

        if param_name in grouped_params_df["Grouped_Variable_Name"].values:
            matching_rows = grouped_params_df[grouped_params_df["Grouped_Variable_Name"] == param_name]
            for _, row in matching_rows.iterrows():
                grouped_param_name = row["Parameter"]
                print(f"Grouped parameter {param_name} → setting {grouped_param_name} = {param_value}")
                _mod.setParameters(f"{grouped_param_name}={param_value}")
                _mod.getParameters()
        else:
            print(f"Parameter: {param_name}, value: {param_value}")
            _mod.setParameters(f"{param_name}={param_value}")


def set_opt_parameters(opt_params, bounds):
    """Set the optimal parameters found by the Bayesian optimizer, with grouped parameter support.

    Args:
        opt_params: 1-D array of optimal parameter values (one per bound entry).
        bounds: List of bound dicts, each with a 'name' key.
    """
    grouped_params_df = pd.read_csv(GROUPED_PARAMETERS_FILE)

    for i, bound in enumerate(bounds):
        param_name  = bound["name"]
        param_value = opt_params[i]

        if param_name in grouped_params_df["Grouped_Variable_Name"].values:
            matching_rows = grouped_params_df[grouped_params_df["Grouped_Variable_Name"] == param_name]
            for _, row in matching_rows.iterrows():
                grouped_param_name = row["Parameter"]
                print(f"Parameter: {grouped_param_name}, value: {param_value}")
                _mod.setParameters(f"{grouped_param_name}={param_value}")
        else:
            print(f"Parameter: {param_name}, value: {param_value}")
            _mod.setParameters(f"{param_name}={param_value}")


def print_optimal_parameters(opt_params, bounds):
    param_str = ", ".join([f"{b['name']} = {opt_params[i]}" for i, b in enumerate(bounds)])
    print(f"Optimal parameters: {param_str}")


def plot_results():
    result_real_location  = str(REAL_DATASET_PATH)
    result_sim_location   = str(DEST_PATH / f"{MODELICA_MODEL_NAME}_result_final.csv")
    result_initial_location = str(DEST_PATH / f"{MODELICA_MODEL_NAME}_resultInitialSim.csv")

    result_real    = pd.read_csv(result_real_location)
    result_sim     = pd.read_csv(result_sim_location)
    result_initial = pd.read_csv(result_initial_location)

    real_data_temp = {key: load_data_csv(value) for key, value in REAL_COLUMNS_MAPPING.items()}
    real_data_temp["time"] = result_real["time"]
    df_real = pd.DataFrame(real_data_temp)
    real_data = apply_noise_reduction(df_real)

    time_real    = real_data["time"]
    time_sim     = result_sim["time"]
    time_initial = result_initial["time"]

    fig = plt.figure(figsize=(20, 10))
    gs  = gridspec.GridSpec(1, 2, width_ratios=[5, 1])
    ax  = fig.add_subplot(gs[0])

    lines  = []
    labels = []

    for sim_col in REAL_COLUMNS_MAPPING:
        level_real    = real_data[sim_col]
        level_sim     = result_sim[sim_col]
        level_initial = result_initial[sim_col]

        line_real,    = ax.plot(time_real,    level_real,    label=f"Real {sim_col}")
        line_sim,     = ax.plot(time_sim,     level_sim,     label=f"Optimized simulation {sim_col}",  linestyle="--")
        line_initial, = ax.plot(time_initial, level_initial, label=f"Initial simulation {sim_col}", linestyle="dotted")

        lines.extend([line_real, line_sim, line_initial])
        labels.extend([f"Real {sim_col}", f"Optimized simulation {sim_col}", f"Initial simulation {sim_col}"])

    rax = fig.add_subplot(gs[1], facecolor="lightgoldenrodyellow")
    check = CheckButtons(rax, labels, [True] * len(labels))

    def toggle(label):
        idx = labels.index(label)
        lines[idx].set_visible(not lines[idx].get_visible())
        plt.draw()

    check.on_clicked(toggle)

    ax.set_xlabel("Time")
    ax.set_ylabel("Value")
    ax.legend()
    plt.title("Comparison of optimized simulation against real plant data")
    plt.show()


def preprocess_format_results(result_real_location, result_sim_location):
    result_real = pd.read_csv(result_real_location)
    result_sim  = pd.read_csv(result_sim_location)

    real_data = {key: load_data_csv(value) for key, value in REAL_COLUMNS_MAPPING.items()}
    real_data["time"] = result_real["time"]

    sim_data = {key: result_sim[key] for key in REAL_COLUMNS_MAPPING.keys()}
    sim_data["time"] = result_sim["time"]

    df_real = pd.DataFrame(real_data)
    df_real = df_real[["time"] + [col for col in df_real.columns if col != "time"]]
    df_real = df_real.drop_duplicates(subset=["time"])

    df_sim = pd.DataFrame(sim_data)
    df_sim = df_sim[["time"] + [col for col in df_sim.columns if col != "time"]]
    df_sim = df_sim.drop_duplicates(subset=["time"])

    return df_real, df_sim


def interpolate_simulation_results(df_real, df_sim):
    """Interpolate simulation columns onto the timestamps of the real dataset.

    Uses np.interp (linear interpolation). Values outside the simulation time
    range are clamped to the nearest boundary value.

    Args:
        df_real: DataFrame with the real sensor timestamps in a 'time' column.
        df_sim:  DataFrame with simulation results including a 'time' column.

    Returns:
        DataFrame aligned to df_real's timestamps with interpolated simulation values.
    """
    interpolated_df = pd.DataFrame()
    interpolated_df["time"] = df_real["time"]

    real_times = df_real["time"].astype(float).to_numpy()
    sim_times  = df_sim["time"].astype(float).to_numpy()

    for column in df_real.columns:
        if column != "time" and column in df_sim.columns:
            sim_values = df_sim[column].astype(float).to_numpy()
            interpolated_df[column] = np.interp(
                real_times, sim_times, sim_values,
                left=sim_values[0], right=sim_values[-1],
            )

    return interpolated_df


def load_data_csv(column_name):
    """Read a single column from the real-plant dataset CSV.

    Args:
        column_name: Name of the column to extract.

    Returns:
        List of values for the requested column, or None if not found.
    """
    with open(str(REAL_DATASET_PATH), "r") as f:
        header_line = f.readline().strip()

    headers = [h.strip('"') for h in header_line.split(",")]
    df = pd.read_csv(str(REAL_DATASET_PATH), delimiter=",", skiprows=1, names=headers)

    if column_name in df.columns:
        return df[column_name].tolist()
    print(f"Column '{column_name}' not found. Available columns: {df.columns.tolist()}")
    return None


def apply_noise_reduction(df_real):
    """Apply a moving-average noise reduction pass to the real-plant data.

    Args:
        df_real: DataFrame of real sensor measurements.

    Returns:
        Smoothed copy of df_real.
    """
    cleaned_df = df_real.copy()
    cleaned_df = apply_moving_average(cleaned_df, window_size=3)
    return cleaned_df


def remove_negative_values(df):
    """Clamp negative values to zero for physical quantity columns (level, volume, etc.)."""
    keywords = ["level", "volume", "pressure", "temperature"]
    for col in df.columns:
        if any(kw in col.lower() for kw in keywords):
            df[col] = df[col].apply(lambda x: max(x, 0) if pd.notnull(x) else x)
    return df


def smooth_sudden_jumps(df, time_col="time", volume_threshold=1000, level_threshold=15, temperature_threshold=15):
    """Detect and smooth abrupt step changes using a median filter.

    Args:
        df: DataFrame to smooth.
        time_col: Name of the time column.
        volume_threshold: Max allowed single-step change for volume signals.
        level_threshold: Max allowed single-step change for level signals.
        temperature_threshold: Max allowed single-step change for temperature signals.

    Returns:
        Smoothed copy of df.
    """
    df = df.copy()
    for col in df.columns:
        if col not in REAL_COLUMNS_MAPPING:
            continue
        col_lower = col.lower()
        if "volume" in col_lower:
            threshold = volume_threshold
        elif "level" in col_lower:
            threshold = level_threshold
        elif "temperature" in col_lower:
            threshold = temperature_threshold
        else:
            continue

        time_diffs  = df[time_col].diff().fillna(0).astype(float)
        value_diffs = df[col].diff().fillna(0).abs()
        sudden_jumps = (time_diffs < 5) & (value_diffs > threshold)

        if sudden_jumps.any():
            print(f"Abrupt changes detected in {col}. Applying median filter.")
        df[col] = medfilt(df[col], kernel_size=3)
    return df


def apply_moving_average(df, window_size=3):
    """Apply a centered rolling mean to all numeric process-variable columns.

    Args:
        df: DataFrame to smooth.
        window_size: Rolling window length in samples.

    Returns:
        Smoothed copy of df.
    """
    df = df.copy()
    for col in df.columns:
        if col in REAL_COLUMNS_MAPPING and pd.api.types.is_numeric_dtype(df[col]):
            smoothed = df[col].rolling(window=window_size, center=True, min_periods=1).mean()
            df[col] = smoothed.fillna(df[col])
    return df


def calculate_nrmse(real, sim):
    """Compute the Normalized Root Mean Squared Error between two arrays."""
    rmse = root_mean_squared_error(real, sim)
    value_range = np.max(real) - np.min(real)
    return rmse / value_range


def calculate_scaled_mae(real, sim):
    """Compute the Min-Max scaled MAE between two 1-D arrays.

    Both arrays are jointly normalized to [0, 1] before computing MAE so that
    the metric is dimensionless and comparable across different physical quantities.

    Args:
        real: 1-D numpy array of real sensor values.
        sim:  1-D numpy array of simulation values.

    Returns:
        Scaled MAE as a float in [0, 1].
    """
    scaler = MinMaxScaler()
    combined = np.concatenate([real, sim]).reshape(-1, 1)
    scaler.fit(combined)
    real_scaled = scaler.transform(real.reshape(-1, 1))
    sim_scaled  = scaler.transform(sim.reshape(-1, 1))
    return mean_absolute_error(real_scaled, sim_scaled)
