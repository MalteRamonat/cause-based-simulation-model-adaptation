"""
Artefact 1 — Sensor-Simulation Comparison Pipeline.

Loads real plant sensor data and Modelica simulation output, aligns their
timestamps, computes MAE and sMAPE deviation metrics per sensor channel,
and saves both scaled and unscaled comparison results as CSV files.

Usage:
    python Scripts/Artefact_1/Comparison_Main.py

Configure the active dataset path and model name in Scripts/Config.py before running.
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Artefact_1.Data_Preparation import DataPreparation
from Artefact_1.Deviation_Detection import DeviationDetection
from Artefact_1.Model_Initialization import ModelInitialization
from Config import CURRENT_DATASET_PATH as sensor_data_path
from Config import SIMULATION_RESULTS_DIR as simulation_folder_path
from Config import MODELICA_MODEL_NAME as simulation_model_name
from Config import (
    COMPARISON_RESULT_FILE_UNSCALED,
    COMPARISON_RESULT_FILE_SCALED,
    COMPARISON_RESULTS_DIR,
    PLOT_COLUMNS_GAS_TEMPERATURE,
    PLOT_COLUMNS_GAS_PRESSURE,
    PLOT_COLUMNS_GAS_FLOW,
    PLOT_COLUMNS_WATER_TEMPERATURE,
)
import glob
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import pandas as pd


def plot_interactive_time_series(df, time_column, exclude_columns=None):
    """Plot an interactive time series chart using Plotly and save it as HTML.

    Args:
        df: DataFrame containing the data to plot.
        time_column: Name of the column to use as the x-axis.
        exclude_columns: List of column names to omit from the plot.
    """
    exclude_columns = exclude_columns or []
    columns_to_plot = [col for col in df.columns if col not in exclude_columns and col != time_column]

    fig = go.Figure()
    for col in columns_to_plot:
        fig.add_trace(go.Scatter(
            x=df[time_column], y=df[col],
            mode="lines", name=col,
        ))

    fig.update_layout(
        title="Interactive Time Series Plot",
        xaxis_title="Time (seconds)",
        yaxis_title="Values",
        legend_title="Variables",
        template="plotly",
        hovermode="x unified",
    )
    fig.show()
    fig.write_html(str(COMPARISON_RESULTS_DIR / "interactive_time_series_plot.html"))


def plot_time_series(df, time_column, exclude_columns=None, legend_loc="upper right", save_path=None):
    """Create a Matplotlib time series plot and optionally save it to disk.

    Pressure columns (in Pa) are automatically converted to bar for display.

    Args:
        df: DataFrame containing the data.
        time_column: Name of the time axis column.
        exclude_columns: Columns to omit from the plot.
        legend_loc: Legend position string accepted by Matplotlib.
        save_path: File path to save the figure (e.g. 'plot.png'). Optional.
    """
    exclude_columns = exclude_columns or []
    columns_to_plot = [col for col in df.columns if col not in exclude_columns and col != time_column]

    if (any("Pressure" in c for c in columns_to_plot)
            and not any("_scaled" in c for c in columns_to_plot)
            and not any("mae" in c for c in columns_to_plot)):
        df[columns_to_plot] = df[columns_to_plot].apply(lambda x: x / 100000)
        for col in columns_to_plot:
            if "Pressure" in col:
                print(f"preprocessing: converting {col} from Pa to bar")

    plt.figure(figsize=(10, 5))
    for col in columns_to_plot:
        plt.plot(df[time_column], df[col], label=col)

    if any("Pressure" in c for c in columns_to_plot):
        y_label = "Pressure"
        y_unit = "[-]" if any("scaled" in c for c in columns_to_plot) else "[bar]"
    elif any("Flow" in c for c in columns_to_plot):
        y_label = "Flow Rate"
        y_unit = "[-]" if any("scaled" in c for c in columns_to_plot) else "[kg/s]"
    elif any("Temperature" in c for c in columns_to_plot):
        y_label = "Temperature"
        y_unit = "[-]" if any("scaled" in c for c in columns_to_plot) else "[°C]"
    elif any("Position" in c for c in columns_to_plot):
        y_label = "Position"
        y_unit = "[-]"
    else:
        y_label = ""
        y_unit = ""

    plt.title("Comparison")
    plt.xlabel("Time [s]")
    plt.ylabel(f"{y_label} {y_unit}")
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.gca().set_facecolor("white")

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")


def check_column_differences(sensor_data, simulation_data):
    """Warn if sensor and simulation DataFrames have mismatched channels.

    Compares base column names (without the '_real'/'_sim' suffixes) and
    prints any channels that appear in only one of the two DataFrames.

    Args:
        sensor_data: DataFrame with '_real'-suffixed columns.
        simulation_data: DataFrame with '_sim'-suffixed columns.
    """
    sensor_columns     = {col.replace("_real", "") for col in sensor_data.columns}
    simulation_columns = {col.replace("_sim",  "") for col in simulation_data.columns}

    only_in_sensor     = sensor_columns.difference(simulation_columns)
    only_in_simulation = simulation_columns.difference(sensor_columns)

    if only_in_sensor or only_in_simulation:
        print("\nWARNING: Column mismatch between sensor_data and simulation_data!")
        if only_in_sensor:
            print(f"Columns only in sensor_data (without suffix): {only_in_sensor}")
        if only_in_simulation:
            print(f"Columns only in simulation_data (without suffix): {only_in_simulation}")
    else:
        print("\nINFO: No column differences found between sensor_data and simulation_data.")


def main():
    sensor_path = str(sensor_data_path)

    actuators_to_exclude = []

    init_necessary = input("Do you want to initialize the simulation? (y/n): ").lower() == "y"
    if init_necessary:
        model_init = ModelInitialization(sensor_path, exclude_actuators=actuators_to_exclude)
        simulation_path = model_init.run()
    else:
        print(f"Using latest simulation file in {simulation_folder_path}")
        latest_simulation_file = max(
            glob.glob(os.path.join(str(simulation_folder_path), f"{simulation_model_name}*.csv")),
            key=os.path.getctime,
        )
        simulation_path = latest_simulation_file

    # Data Preparation
    data_prep = DataPreparation(sensor_path, simulation_path)
    data_prep.map_variables()
    data_prep.denoise_sensor_data()
    data_prep.resample_simulation()

    sensor_data, simulation_data = data_prep.get_data()

    sensor_data     = sensor_data[    [col for col in sensor_data.columns     if col.endswith("_real") or col == "time"]]
    simulation_data = simulation_data[[col for col in simulation_data.columns if col.endswith("_sim")  or col == "time"]]

    check_column_differences(sensor_data, simulation_data)

    simulation_data_copy = simulation_data.drop(columns=["time"])
    sensor_and_sim_data  = sensor_data.join(simulation_data_copy, how="outer")

    # Deviation Detection
    deviation_detector = DeviationDetection(sensor_data, simulation_data)
    scaled_sensor_data, scaled_simulation_data = deviation_detector.scale_data()

    mae_df, smape_df, per_channel_mae_smape_df, total_mae, total_smape = deviation_detector.calculate_mae_smape()
    print(per_channel_mae_smape_df)
    print(f"Total MAE: {total_mae}, Total SMAPE: {total_smape:.2f}%")

    actuator_names = [idx for idx in per_channel_mae_smape_df.index if "Position_" in idx]
    print(actuator_names)
    if any(per_channel_mae_smape_df.loc[actuator_names, "MAE"] > 0):
        print("\n******************")
        print("Warning: Actuator values are not synchronized between real and simulation data.")
        print("******************\n")

    mae_df.columns = [col.replace("_real", "_mae") for col in mae_df.columns]

    total_deviation_df = pd.merge(mae_df, sensor_data, on="time")
    total_deviation_df = pd.merge(total_deviation_df, simulation_data, on="time")
    if "time" not in total_deviation_df.columns:
        raise KeyError("Column 'time' not found in merged deviation DataFrame.")

    scaled_deviation_df = pd.merge(mae_df, scaled_sensor_data.reset_index(), on="time")
    scaled_deviation_df = pd.merge(scaled_deviation_df, scaled_simulation_data.reset_index(), on="time")
    if "time" not in scaled_deviation_df.columns:
        raise KeyError("Column 'time' not found in scaled deviation DataFrame.")

    total_deviation_df.to_csv(str(COMPARISON_RESULT_FILE_UNSCALED), index=False)
    scaled_deviation_df.to_csv(str(COMPARISON_RESULT_FILE_SCALED),   index=False)

    # Plotting
    timestamp_label = "after_update"

    plot_interactive_time_series(sensor_and_sim_data, time_column="time", exclude_columns=[])

    exclude_columns = [col for col in sensor_and_sim_data.columns if col not in PLOT_COLUMNS_GAS_TEMPERATURE]
    plot_time_series(sensor_and_sim_data, time_column="time", exclude_columns=exclude_columns,
                     save_path=str(COMPARISON_RESULTS_DIR / f"Comparison_Gas_Temperature_{timestamp_label}.png"))

    exclude_columns = [col for col in sensor_and_sim_data.columns if col not in PLOT_COLUMNS_WATER_TEMPERATURE]
    plot_time_series(sensor_and_sim_data, time_column="time", exclude_columns=exclude_columns,
                     save_path=str(COMPARISON_RESULTS_DIR / f"Comparison_Water_Temperature_{timestamp_label}.png"))

    exclude_columns = [col for col in sensor_and_sim_data.columns if col not in PLOT_COLUMNS_GAS_PRESSURE]
    plot_time_series(sensor_and_sim_data, time_column="time", exclude_columns=exclude_columns,
                     save_path=str(COMPARISON_RESULTS_DIR / f"Comparison_Gas_Pressure_{timestamp_label}.png"))

    exclude_columns = [col for col in sensor_and_sim_data.columns if col not in PLOT_COLUMNS_GAS_FLOW]
    plot_time_series(sensor_and_sim_data, time_column="time", exclude_columns=exclude_columns,
                     save_path=str(COMPARISON_RESULTS_DIR / f"Comparison_Gas_Flow_{timestamp_label}.png"))

    scaled_sensor_and_sim_data = scaled_sensor_data.join(scaled_simulation_data, how="outer")
    scaled_sensor_and_sim_data.reset_index(inplace=True)


if __name__ == "__main__":
    main()
