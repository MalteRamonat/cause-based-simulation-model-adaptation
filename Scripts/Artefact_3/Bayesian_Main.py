"""
Artefact 3 — Bayesian Optimization Loop.

Defines the objective function used to evaluate simulation parameter sets and
the `run_Bayes_optimization` driver that calls GPyOpt's BayesianOptimization.
Consumed by Parameter_Adaptation_Main.py, which sets up the parameter bounds
and orchestrates single or parallel optimization runs.

Requires matplotlib==3.8.4 and pyDOE to be installed.
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import GPyOpt
from GPy.kern import Matern52
from GPyOpt.methods import BayesianOptimization
from Bayesian_Functions import (
    generate_initial_dataset,
    set_parameters,
    get_result_file,
    preprocess_format_results,
    interpolate_simulation_results,
    apply_noise_reduction,
    calculate_nrmse,
    calculate_scaled_mae,
    simulate,
    plot_results,
    print_optimal_parameters,
    set_opt_parameters,
    apply_unit_conversion,
)
from Bayesian_Config import *

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.width", None)

counter = 0

def objective_function(params, bounds, index_or_list_of_indexes, number_of_parameters=1):
    """Evaluate a parameter set proposed by the Bayesian optimizer.

    Runs one Modelica simulation with the proposed parameters, computes the
    mean scaled MAE between the simulation output and the real-plant reference,
    penalises incomplete simulations by their missing progress, and writes the
    result into the shared optimization results CSV.

    Args:
        params: Parameter values proposed by GPyOpt (numpy array).
        bounds: GPyOpt bounds list used for this optimization run.
        index_or_list_of_indexes: Row index (or list of indices) in the
            optimization results DataFrame to update.
        number_of_parameters: Number of parameters being optimized in parallel.

    Returns:
        Total error scalar (scaled MAE + simulation-progress penalty). Returns
        3.0 as a large-error sentinel on simulation failure.
    """
    index_iter = index_or_list_of_indexes
    optimization_results_df = pd.read_csv(OPTIMIZATION_RESULTS_FILE)
    if number_of_parameters == 1:
        name_value = bounds[0]["name"]
        if isinstance(index_iter, list):
            index_iter = index_iter[0]
    elif number_of_parameters > 1:
        name_value = f"Parallel_from_{bounds[0]['name']}_to_{bounds[number_of_parameters - 1]['name']}"

    result_dir = f"{DEST_PATH}/{name_value}/"
    os.makedirs(os.path.dirname(result_dir), exist_ok=True)

    global counter
    counter += 1
    print(f"Optimization iteration {counter}")

    set_parameters(params, bounds)

    result_filename = f"{MODELICA_MODEL_NAME}_result_{counter}_{name_value}.csv"
    simulate(result_filename)
    get_result_file(result_filename, result_dir)

    result_sim_location  = f"{DEST_PATH}/{name_value}/{result_filename}"
    result_real_location = str(REAL_DATASET_PATH)

    try:
        result_sim_df = pd.read_csv(result_sim_location)
    except pd.errors.ParserError as e:
        print(f"Error reading simulation CSV: {e}")
        return 3
    except Exception as e:
        print(f"Unexpected error reading simulation CSV: {e}")
        return 3

    if result_sim_df.empty:
        return 3

    df_real, df_sim = preprocess_format_results(result_real_location, result_sim_location)
    df_interpolated_sim = interpolate_simulation_results(df_real, df_sim)
    df_noise_free_real  = apply_noise_reduction(df_real)
    df_merged = pd.merge(df_noise_free_real, df_interpolated_sim, on="time", suffixes=("_real", "_sim"))

    max_time = df_sim["time"].max()
    progress_sim      = max_time / int(STOP_TIME)
    progress_deviation = 1 - progress_sim
    print(f"Simulation progress: {progress_sim * 100:.2f}%")

    total_scaled_mae = 0
    for process_variable in REAL_COLUMNS_MAPPING.keys():
        value_real = df_merged[f"{process_variable}_real"].values
        value_sim  = df_merged[f"{process_variable}_sim"].values
        scaled_mae = calculate_scaled_mae(value_real, value_sim)

        opt_col = f"Deviation_of_observed_{process_variable}_after_Optimization"
        if number_of_parameters == 1:
            if optimization_results_df.loc[index_iter, opt_col] > scaled_mae or pd.isna(optimization_results_df.loc[index_iter, opt_col]):
                optimization_results_df.loc[index_iter, opt_col] = scaled_mae
        elif number_of_parameters > 1 and isinstance(index_iter, list):
            for index in range(len(index_iter)):
                if optimization_results_df.loc[index, opt_col] > scaled_mae or pd.isna(optimization_results_df.loc[index, opt_col]):
                    optimization_results_df.loc[index, opt_col] = scaled_mae

        total_scaled_mae += scaled_mae * (1 / len(REAL_COLUMNS_MAPPING))
        print(f"Scaled MAE for {process_variable}: {scaled_mae}")

    total_error = total_scaled_mae + progress_deviation
    print(f"Total error: {total_error}")
    optimization_results_df.to_csv(OPTIMIZATION_RESULTS_FILE, index=False)

    return total_error


def run_Bayes_optimization(
    iterations_for_DoE,
    number_of_optimization_iterations,
    error_tolerance,
    metamodel_data_file,
    bounds,
    index_iter,
    number_of_parameters=1,
):
    """Run one Bayesian optimization pass for the given parameter bounds.

    Uses Latin Hypercube Sampling on the first call (when metamodel_data_file
    does not yet exist) and loads previously saved evaluations on subsequent
    calls. Stops early when the best error falls below error_tolerance.

    Args:
        iterations_for_DoE: Number of initial LHS samples.
        number_of_optimization_iterations: Maximum GPyOpt iterations after LHS.
        error_tolerance: Early-stop threshold for the objective value.
        metamodel_data_file: Path to the CSV that caches LHS evaluations.
        bounds: GPyOpt-format list of bound dicts.
        index_iter: Row index (or list) in the optimization results DataFrame.
        number_of_parameters: How many parameters are optimized in parallel.
    """
    if number_of_parameters == 1:
        name_value = bounds[0]["name"]
    elif number_of_parameters > 1:
        name_value = f"Parallel_from_{bounds[0]['name']}_to_{bounds[number_of_parameters - 1]['name']}"

    result_dir = f"{DEST_PATH}/{name_value}/"
    os.makedirs(os.path.dirname(result_dir), exist_ok=True)

    max_iter       = number_of_optimization_iterations
    error_threshold = float(error_tolerance)
    data_file       = metamodel_data_file

    global counter
    counter = 0

    if not os.path.exists(data_file):
        optimizer = BayesianOptimization(
            f=lambda params: objective_function(params, bounds, index_iter, number_of_parameters),
            domain=bounds,
            initial_design_type="latin",
            initial_design_numdata=iterations_for_DoE,
            model_type="GP",
            acquisition_type="EI",
            acquisition_jitter=0.01,
            normalize_Y=False,
            exact_feval=False,
            num_cores=1,
        )
        print("Generating metamodel with Latin Hypercube Sampling")
        optimizer.run_optimization(max_iter=0)
    else:
        evals = pd.read_csv(data_file, index_col=0, delimiter="\t")
        Y = np.array([[x] for x in evals["Y"]])
        X = np.array(evals.filter(regex="var*"))
        optimizer = GPyOpt.methods.BayesianOptimization(
            f=lambda params: objective_function(params, bounds, index_iter, number_of_parameters),
            domain=bounds,
            X=X,
            Y=Y,
            model_type="GP",
            acquisition_type="EI",
            acquisition_jitter=0.01,
            exact_feval=True,
            num_cores=1,
        )

    current_iter = 0
    while current_iter < max_iter:
        optimizer.run_optimization(max_iter=1)
        print(f"Optimization iteration: {current_iter + 1} of {max_iter}")
        print(f"Current best for {name_value}: {optimizer.fx_opt}")
        current_iter += 1
        fx_opt_value = optimizer.fx_opt.item() if isinstance(optimizer.fx_opt, np.ndarray) else optimizer.fx_opt
        if fx_opt_value < error_threshold:
            print(f"Stopping early: error {fx_opt_value:.4f} < threshold {error_threshold}")
            break

    optimizer.save_evaluations(f"{OUTPUT_PATH}Bayes_results_{name_value}.csv")
    optimizer.plot_convergence(filename=f"{OUTPUT_PATH}convergence_plot_for_iter_{name_value}.png")

    optimization_results_df = pd.read_csv(OPTIMIZATION_RESULTS_FILE)
    optimization_results_df.loc[index_iter, "Total_Deviation_after_Optimization"] = optimizer.fx_opt
    optimization_results_df.loc[index_iter, "Value_after_single_Param_Optimization"] = optimizer.x_opt

    eval_path              = str(EVALUATION_RESULTS_FILE)
    eval_user_choice_path  = str(USER_EVALUATION_RESULTS_FILE)

    if os.path.exists(eval_path) and os.path.exists(eval_user_choice_path):
        evaluation_results_df            = pd.read_csv(eval_path)
        evaluation_results_user_choice_df = pd.read_csv(eval_user_choice_path)

        for i in range(number_of_parameters):
            idx = evaluation_results_df[evaluation_results_df["Parameter"] == bounds[i]["name"]].index
            idx_user = evaluation_results_user_choice_df[evaluation_results_user_choice_df["Parameter"] == bounds[i]["name"]].index

            if not idx.empty and not idx_user.empty:
                evaluation_results_df.at[idx[0], "Value_after_single_Param_Optimization"] = optimizer.x_opt[i]
                evaluation_results_user_choice_df.at[idx_user[0], "Value_after_single_Param_Optimization"] = optimizer.x_opt[i]

            evaluation_results_df.to_csv(eval_path, index=False)
            evaluation_results_user_choice_df.to_csv(eval_user_choice_path, index=False)

    print(optimization_results_df)
    optimization_results_df.to_csv(OPTIMIZATION_RESULTS_FILE, index=False)
    print_optimal_parameters(optimizer.x_opt, bounds)
