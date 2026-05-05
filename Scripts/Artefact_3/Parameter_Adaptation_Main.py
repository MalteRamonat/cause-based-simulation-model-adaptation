"""
Artefact 3 — Parameter Adaptation Pipeline.

Coordinates the full Bayesian parameter optimization workflow:
  1. Loads ranked parameters from the RCA result (Artefact 2 output).
  2. Maps AML component names to Modelica simulation parameter paths.
  3. Derives search bounds automatically from the current model state.
  4. Runs GPyOpt-based optimization via Bayesian_Main.run_Bayes_optimization.

The interactive main() menu exposes three optimization modes:
  A — Sequential single-parameter optimization over all ranked parameters.
  B — Progressive multi-parameter optimization ordered by expected improvement.
  C — Parallel multi-parameter optimization with optional discrete grid search.

Usage:
    python Scripts/Artefact_3/Parameter_Adaptation_Main.py
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import Config
from OMPython_Functionalities import start_modelica, get_modelica_parameter_data
import Bayesian_Main
from Bayesian_Functions import *
import sensor_simvar_mapping
import Bayesian_Config
import csv
import numpy as np
from scipy import stats
from GUI_Bayes import ApplicationGUI
import matplotlib.pyplot as plt
import shutil
import glob



def import_mapping_table():
    """Load the AML-to-simulation parameter mapping table from Excel."""
    return pd.read_excel(Config.RCA_AML_TO_SIMULATION_FILEPATH)


def import_root_cause_parameter_list():
    """Load the ranked parameter list produced by the RCA (Artefact 2)."""
    root_cause_parameter_list = pd.read_csv(Config.RCA_RESULT_FILE, usecols=["Parameter"])
    print(f"Using {Config.RCA_RESULT_FILE} as root cause parameter list.")
    return root_cause_parameter_list


def extract_parameters_from_Modelica_parameter_set(parameterDict, keys_to_extract):
    extracted_dict = {}
    keys_to_extract_lower = {key.lower() for key in keys_to_extract}
    
    for param in parameterDict:
        for key, value in param.items():
            if key.lower() in keys_to_extract_lower:
                extracted_dict[key] = value
    return extracted_dict
    
    
    #for param in parameterDict:
    #    for key in keys_to_extract:
    #        if key in param:
    #            extracted_dict[key] = param[key]
    #return extracted_dict


def generate_bound_values_automatically(simulation_parameter_list, set_sigma=0.05, min_sigma=0.3, continuous_or_discrete='continuous',grid_factor=10, num_discrete_segments=10):
    
    mod = start_modelica()
    parameterDict = get_modelica_parameter_data(mod)
    # Remove duplicate uppercase '.L' keys for Pipe components — both '.l' and '.L' exist
    # in the model but only the lowercase version should be used for bounds generation.
    for param in parameterDict:
        keys_to_remove = [k for k in param.keys() if k.startswith("Pipe_") and k.endswith(".L")]
        for k in keys_to_remove:
            del param[k]
            print(f"Removed duplicate key: {k} from component {param.get('Name', '')}")
    reduced_parameterDict = extract_parameters_from_Modelica_parameter_set(parameterDict=parameterDict, keys_to_extract=simulation_parameter_list)
    # turn the dictionary into a pandas dataframe
    parameter_df = pd.DataFrame(reduced_parameterDict.items(), columns=['Parameter', 'Value'])
    
    
    def get_length_value(parameter_name):
        length_param_name = parameter_name.replace('.height', '.length')
        return reduced_parameterDict.get(length_param_name, float('inf'))
    
    def get_small_value(parameter_value):
        order_of_magnitude = 10 ** np.floor(np.log10(abs(parameter_value)))
        return order_of_magnitude * 0.01  # Small value based on the order of magnitude
    
    
    
    if continuous_or_discrete == 'continuous':
        # 2. set sigma value based on the parameter value
        # add columns for min and max bounds
        parameter_df['Min_Bound'] = 0
        parameter_df['Max_Bound'] = 0
        
        # loop through parameter_df lines
        for index, row in parameter_df.iterrows():
            # parameter value in df might be a string, convert to float
            parameter_value = float(row['Value'])
            # get Parameter Name
            parameter_name = row['Parameter']
            # set the sigma value for the parameter: take into account that the parameter value might be negative
            sigma = abs(set_sigma * parameter_value)
            # set the min and max bounds for the parameter
            if parameter_value == 0:
                min_bound = -1 * min_sigma
                max_bound = 1 * min_sigma
            elif parameter_value < 0:
                min_bound = parameter_value * (1 + sigma)
                max_bound = parameter_value * (1 - sigma)
            else:
                min_bound = parameter_value - 1 * sigma
                max_bound = parameter_value + 1 * sigma
            
            # make sure that the bounds are within the physical limits of the parameter
            # values cannot be negative except for height parameters
            # height parameters cannot be greater than length
            
            if '.height_ab' in parameter_name:
                length_value = get_length_value(parameter_name)
                min_bound = max(min_bound, -length_value)
                max_bound = min(max_bound, length_value)
            else:
                min_bound = max(min_bound, 0)
            
            # dp nom canot be negative but is in Pa so therefore it can be quite large
            if '.dp_nominal' in parameter_name:
                min_bound = max(min_bound, 0)
                max_bound = max_bound*10000  # convert to Pa
                max_bound = min(max_bound, 30000)  # limit the max bound to 300 mbar
            
            # Ensure min_bound is not zero for certain parameters
            if min_bound == 0 and not any(x in parameter_name for x in ['.portsData[1].height', '.height_ab']):
                min_bound = get_small_value(parameter_value)
            
            # add the min and max bounds to the dataframe
            parameter_df.at[index, 'Min_Bound'] = min_bound
            parameter_df.at[index, 'Max_Bound'] = max_bound
            parameter_df.at[index, 'Value'] = parameter_value
    
    if continuous_or_discrete == 'discrete':
        # add columns for as many bounds as the number of segments
        for i in range(num_discrete_segments):
            parameter_df[f'Discrete_Bound_{i}'] = 0
            
        for index, row in parameter_df.iterrows():
           # parameter in df might be a string, convert to float
            parameter_value = float(row['Value'])
            # get Parameter Name
            parameter_name = row['Parameter']
            
            if parameter_value == 0:
                # Handle the case where parameter_value is 0
                order_of_magnitude = 1  # Set a default order of magnitude
                lower_bound = -grid_factor * min_sigma
                upper_bound = grid_factor * min_sigma
            else:
                # Calculate the order of magnitude of the parameter value
                order_of_magnitude = 10 ** np.floor(np.log10(abs(parameter_value)))
                # create a lower and upper bound for the grid
                lower_bound = parameter_value - order_of_magnitude * grid_factor
                upper_bound = parameter_value + order_of_magnitude * grid_factor
            
            # make sure that the bounds are within the physical limits of the parameter
            # values cannot be negative except for height parameters
            # height parameters cannot be  
            if '.height_ab' in parameter_name:
                length_value = get_length_value(parameter_name)
                lower_bound = max(lower_bound, -length_value)
                upper_bound = min(upper_bound, length_value)
            else:
                lower_bound = max(lower_bound, 0)
            
            # Ensure lower_bound is not zero for certain parameters
            if lower_bound == 0 and not any(x in parameter_name for x in ['.portsData[1].height', '.height_ab']):
                lower_bound = get_small_value(parameter_value)
            
            # create a grid of values for the parameter
            grid = np.linspace(lower_bound, upper_bound, num_discrete_segments)      
            # add the grid values to the dataframe
            for i, value in enumerate(grid):
                parameter_df.at[index, f'Discrete_Bound_{i}'] = value    
             
    
    return parameter_df



def create_bounds_df(sigma=0.05, continuous_or_discrete='continuous', grid_factor=10, num_discrete_segments=10):
    # 1. Load the identified parameters from the RCA
    root_cause_parameter_list = import_root_cause_parameter_list()
    # 2. Load the mapping table
    mapping_table = import_mapping_table()
    # create Parameter List for Simulation based on mapping table and root cause parameter list
    print("getting Modelica parameters...")
    simulation_parameter_list = []
    # find the name of each root cause parameter ind the mapping table and add the corresponding simulation parameter to the simulation paramter list
    for parameter in root_cause_parameter_list['Parameter']:
        # Convert parameter to string and strip whitespace
        parameter_str = str(parameter).strip()
    
        # Look for parameter in column 'AML_Parameter_Name' of mapping table, ignoring case
        mask = mapping_table['AML_Parameter_Name'].str.lower() == parameter_str.lower()
        
        if mask.any():
            # Get the corresponding simulation parameter name
            simulation_parameter = mapping_table.loc[mask, 'Simulation_Parameter_Name'].iloc[0]
            # Add the simulation parameter to the simulation parameter list
            simulation_parameter_list.append(simulation_parameter)
        else:
            print(f'Parameter "{parameter}" not found in mapping table')
            
    # Ask user for parameters to exclude
    print("The following parameters are used for the calibration/adaptation:")
    for param in simulation_parameter_list:
        print(param)
    exclude_parameters = input("Enter parameters to exclude (comma-separated): ").split(',')
    exclude_parameters = [param.strip() for param in exclude_parameters]

    # Filter out excluded parameters
    simulation_parameter_list = [param for param in simulation_parameter_list if param not in exclude_parameters]

    print("creating bound_df...")
    bound_value_df = generate_bound_values_automatically(simulation_parameter_list, set_sigma=sigma, continuous_or_discrete=continuous_or_discrete, grid_factor=grid_factor, num_discrete_segments=num_discrete_segments)
    # Ask user for manual bounds
    #printthe lines of the bound_value_df
    print("Current bounds for the parameters:")
    for i, row in bound_value_df.iterrows():
        print(f"{i}: {row['Parameter']} - Value:{row['Value']} Min Bound: {row['Min_Bound']}, Max Bound: {row['Max_Bound']}")
    manual_bounds = {}
    use_man_bounds = input("Do you want to set manual bounds? (y/n): ").strip().lower()
    if use_man_bounds == "y":
        use_bound_template = input("Do you want to use the bounds template? (y/n): ").strip().lower()
        if use_bound_template == 'y':
            manual_bounds = MANUAL_BOUNDS
        elif use_bound_template == 'n':    
            while True:
                param = input("Enter parameter to set manual bounds (or press Enter to finish): ").strip()
                if not param:
                    break
                if param not in simulation_parameter_list:
                    print(f'Parameter "{param}" is not in the simulation parameter list.')
                    continue
                lower_bound = float(input(f"Enter lower bound for {param}: "))
                upper_bound = float(input(f"Enter upper bound for {param}: "))
                manual_bounds[param] = (lower_bound, upper_bound)
        # Apply manual bounds
        for param, bounds in manual_bounds.items():
            if param in bound_value_df['Parameter'].values:
                bound_value_df.loc[bound_value_df['Parameter'] == param, 'Min_Bound'] = bounds[0]
                bound_value_df.loc[bound_value_df['Parameter'] == param, 'Max_Bound'] = bounds[1]
            else:
                print(f'Parameter "{param}" not found in bound_value_df')
    elif use_man_bounds == 'n':
        print("No manual bounds set.")
    #save the bound values to a csv file
    bound_value_df.to_csv(Bayesian_Config.CURRENT_BOUNDS_FILE, index=False)
    excel_path_bounds = Bayesian_Config.CURRENT_BOUNDS_FILE.replace('.csv', '.xlsx')
    bound_value_df.to_excel(excel_path_bounds, index=False)
    
    return bound_value_df
    



def write_bounds(bounds_df, num_rows, continuous_or_discrete='continuous', discrete_bound_number=None, single_or_multiple='single'):
    bounds = []
    #for i in range(min(num_rows, len(bounds_df))):  # Ensure not to exceed the length of the dataframe
    if single_or_multiple == 'single':
        row = bounds_df.iloc[num_rows]
        
        if continuous_or_discrete == 'continuous':
            bound = {
                'name': row['Parameter'],
                'type': continuous_or_discrete,
                'domain': (row['Min_Bound'], row['Max_Bound'])
            }
        elif continuous_or_discrete == 'discrete':
            bound = {
                'name': row['Parameter'],
                'type': continuous_or_discrete,
                'domain': tuple(row[f'Discrete_Bound_{i}'] for i in range(discrete_bound_number))
            }

        bounds.append(bound)  
    elif single_or_multiple == 'multiple':
        # create a list of bounds for each row in the bounds_df
        for i in range(num_rows):
            row = bounds_df.iloc[i]
            if continuous_or_discrete == 'continuous':
                bound = {
                    'name': row['Parameter'],
                    'type': continuous_or_discrete,
                    'domain': (row['Min_Bound'], row['Max_Bound'])
                }
            elif continuous_or_discrete == 'discrete':
                bound = {
                    'name': row['Parameter'],
                    'type': continuous_or_discrete,
                    'domain': tuple(row[f'Discrete_Bound_{i}'] for i in range(discrete_bound_number))
                }
            bounds.append(bound)
    return bounds


def set_real_columns_mapping(selected_variables, mapping_df):
    filtered_df = mapping_df[mapping_df['Simulation_variable_name'].isin(selected_variables)]
    real_columns_mapping = {
        f"{row['Simulation_variable_name']}": row['Sensor_OPCUA_Node_ID']
        for _, row in filtered_df.iterrows()
    }
    return real_columns_mapping
    
    
def read_bounds_from_csv():
    bounds = []
    with open('current_bound_dict_list.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            bounds.append({'name': row['name'], 'type': row['type'], 'domain': (float(row['domain_min']), float(row['domain_max']))})

    print(bounds)
    return bounds


def evaluate_adaptation_improvement(optimization_results_df):
    if "t_statistic" not in optimization_results_df.columns:
        optimization_results_df["t_statistic"] = None
    if "p_value" not in optimization_results_df.columns:
        optimization_results_df["p_value"] = None

    for index, row in optimization_results_df.iterrows():
        relative_improvement = (
            row["Total_Deviation_before_Optimization"] - row["Total_Deviation_after_Optimization"]
        ) / row["Total_Deviation_before_Optimization"]

        observed_values_before = np.array([])
        observed_values_after  = np.array([])

        for col in optimization_results_df.columns:
            if "Deviation_of_observed" in col:
                if "before" in col:
                    observed_values_before = np.append(observed_values_before, row[col])
                if "after" in col:
                    observed_values_after = np.append(observed_values_after, row[col])

        t_stat, p_value = stats.ttest_rel(observed_values_before, observed_values_after)
        significance_of_improvement = 1 if p_value < 0.05 else 0

        optimization_results_df.at[index, "Improvement_of_Deviation"]   = relative_improvement
        optimization_results_df.at[index, "Significance_of_Improvement"] = significance_of_improvement
        optimization_results_df.at[index, "t_statistic"]                 = t_stat
        optimization_results_df.at[index, "p_value"]                     = p_value

    optimization_results_df.to_csv(str(Bayesian_Config.EVALUATION_RESULTS_FILE), index=False)
    excel_path = str(Bayesian_Config.EVALUATION_RESULTS_FILE).replace(".csv", ".xlsx")
    optimization_results_df.to_excel(excel_path, index=False)
      

def plot_deviations(file_path):
    '''Works only for optimization_results.csv'''
    # CSV-Datei laden
    df = pd.read_csv(file_path)
    
    # Spalten extrahieren
    parameters = df['Parameter']
    total_deviation_before = df['Total_Deviation_before_Optimization'].iloc[0]
    total_deviation_after = df['Total_Deviation_after_Optimization']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh('Total Deviation Before Optimization', total_deviation_before, color='blue', label='Before Optimization')
    ax.barh(parameters, total_deviation_after, color='green', label='After Optimization')
    ax.set_xlabel('Deviation')
    ax.set_title('Deviation Before and After Optimization')
    ax.legend()
    plt.tight_layout()
    plt.show()


def plot_improvement_of_deviation(evaluation_results_df):
    '''Works only for evaluation_results.csv'''
    evaluation_results_df = evaluation_results_df.sort_values(by='Improvement_of_Deviation', ascending=False)
    plt.figure(figsize=(10, 6))
    plt.barh(evaluation_results_df['Parameter'], evaluation_results_df['Improvement_of_Deviation'], color='skyblue')
    plt.xlabel('Improvement of Deviation')
    plt.ylabel('Parameter Name')
    plt.title('Improvement of Deviation by Parameter')
    plt.gca().invert_yaxis()
    plt.show()
    



def start_tkinter_app():
    app = ApplicationGUI()
    app.run()


def get_user_choice_for_calibration_or_adaptation():
    """Prompt the user to choose between calibration and wear adaptation, and enter sigma.

    Returns:
        sigma: Float search-radius parameter for bound generation.
    """
    print("Please select an option:")
    print("1: Calibration — parameter values are unknown and must be identified.")
    print("2: Wear adaptation — parameter values drift over time.")

    choice = input("Enter 1 or 2: ")

    if choice == "1":
        print("Calibration selected. Enter a sigma value for the search range.")
        sigma = float(input("Sigma: "))
    elif choice == "2":
        print("Wear adaptation selected.")
        sigma = float(input("Sigma: "))
    else:
        print("Invalid input. Please enter 1 or 2.")
        return get_user_choice_for_calibration_or_adaptation()

    return sigma


def transform_bounds_from_discrete_to_continuous():
    current_bounds_df_location = Bayesian_Config.CURRENT_BOUNDS_FILE
    current_bounds_df = pd.read_csv(current_bounds_df_location)

    optimization_results_df_location = Bayesian_Config.OPTIMIZATION_RESULTS_FILE
    optimization_results_df = pd.read_csv(optimization_results_df_location)

    # Check if 'Min_Bound' and 'Max_Bound' exist in the current bounds file
    if "Min_Bound" in current_bounds_df.columns and "Max_Bound" in current_bounds_df.columns:
        print("Continuous bounds already present — no transformation needed.")
    else:
        # Otherwise, perform the transformation
        transformed_df = pd.DataFrame(columns=['Parameter', 'Value', 'Min_Bound', 'Max_Bound'])

        for _, row in current_bounds_df.iterrows():
            parameter = row['Parameter']

            # Find the corresponding reference value from the optimization results
            reference_value = optimization_results_df.loc[
                optimization_results_df['Parameter'] == parameter,
                'Value_after_single_Param_Optimization'
            ].values[0]

            # Find the column index of the reference value in the current row
            discrete_columns = [col for col in current_bounds_df.columns if 'Discrete_Bound_' in col]
            discrete_values = row[discrete_columns].values

            # Identify the position of the reference value
            try:
                index = list(discrete_values).index(reference_value)
            except ValueError:
                continue  # If reference value is not found, skip to the next parameter

            # Assign Min_Bound and Max_Bound based on neighboring values
            min_bound = discrete_values[index - 1] if index > 0 else None
            max_bound = discrete_values[index + 1] if index < len(discrete_values) - 1 else None

            # Add the new row to the transformed dataframe
            transformed_df = transformed_df.append({
                'Parameter': parameter,
                'Value': row['Value'],
                'Min_Bound': min_bound,
                'Max_Bound': max_bound
            }, ignore_index=True)

        current_bounds_df.to_csv(current_bounds_df_location, index=False)



def finetune_bounds_from_discrete_to_continuous(number_of_root_cause_parameters):
    current_bounds_df_location = Bayesian_Config.CURRENT_BOUNDS_FILE
    current_bounds_df = pd.read_csv(current_bounds_df_location)

    optimization_results_df_location = Bayesian_Config.OPTIMIZATION_RESULTS_FILE
    optimization_results_df = pd.read_csv(optimization_results_df_location)

    user_defined_evaluation_results_df_location = Bayesian_Config.USER_EVALUATION_RESULTS_FILE
    user_defined_evaluation_results_df = pd.read_csv(user_defined_evaluation_results_df_location)

    # Get the top X rows from user_defined_evaluation_results_df
    top_parameters = user_defined_evaluation_results_df.head(number_of_root_cause_parameters)['Parameter']

    # Check if 'Min_Bound' and 'Max_Bound' exist in the current bounds file
    if "Min_Bound" in current_bounds_df.columns and "Max_Bound" in current_bounds_df.columns:
        print("Continuous bounds already present.")
    else:
        for parameter in top_parameters:
            # Find the corresponding reference value from the optimization results
            reference_value = optimization_results_df.loc[
                optimization_results_df['Parameter'] == parameter,
                'Value_after_single_Param_Optimization'
            ].values[0]

            # Find the row in current_bounds_df for the parameter
            row_index = current_bounds_df[current_bounds_df['Parameter'] == parameter].index[0]
            row = current_bounds_df.loc[row_index]

            # Find the column index of the reference value in the current row
            discrete_columns = [col for col in current_bounds_df.columns if 'Discrete_Bound_' in col]
            discrete_values = row[discrete_columns].values

            # Identify the position of the reference value
            try:
                index = list(discrete_values).index(reference_value)
            except ValueError:
                continue  # If reference value is not found, skip to the next parameter

            # Assign Min_Bound and Max_Bound based on neighboring values
            min_bound = discrete_values[index - 1] if index > 0 else reference_value
            max_bound = discrete_values[index + 1] if index < len(discrete_values) - 1 else reference_value

            # Update the current_bounds_df with new Min_Bound and Max_Bound
            current_bounds_df.at[row_index, 'Min_Bound'] = min_bound
            current_bounds_df.at[row_index, 'Max_Bound'] = max_bound

        # Drop columns that start with 'Discrete_Bound_'
        current_bounds_df.drop(columns=discrete_columns, inplace=True)
        print("new bounds:")
        print(current_bounds_df)
        # Save the updated current_bounds_df
        current_bounds_df.to_csv(current_bounds_df_location, index=False)


def transform_bounds_from_continuous_to_discrete(num_discrete_segments=10):
    '''Uses evaluation_results_user_choice_location to transform continuous bounds to discrete bounds'''
    current_bounds_df_location = Bayesian_Config.CURRENT_BOUNDS_FILE
    #current_bounds_df = pd.read_csv(current_bounds_df_location)
    evaluation_results_user_choice_location = Bayesian_Config.USER_EVALUATION_RESULTS_FILE
    current_bounds_df = pd.read_csv(evaluation_results_user_choice_location)
    # Ist current bounds das richtige oder brauche ich evaluation_results user choice?
    # Check if 'Discrete_Bound_0' exists in the current bounds file
    if "Discrete_Bound_0" in current_bounds_df.columns:
        print("Discrete bounds already present.")
    else:
        # create as many columns as the number of segments
        for i in range(num_discrete_segments):
            current_bounds_df[f'Discrete_Bound_{i}'] = 0

        for r, row in current_bounds_df.iterrows():
            # Find the Min_Bound and Max_Bound values
            min_bound = row['Min_Bound']
            max_bound = row['Max_Bound']

            # Create a grid of values between Min_Bound and Max_Bound
            grid = np.linspace(min_bound, max_bound, num_discrete_segments)
            # fill the grid values to the transformed dataframe
            for i, value in enumerate(grid):
                current_bounds_df.at[r, f'Discrete_Bound_{i}'] = value
        # delete the Min_Bound and Max_Bound columns
        current_bounds_df = current_bounds_df.drop(columns=['Min_Bound', 'Max_Bound'])
        print("Discrete bounds created successfully.")
        print(current_bounds_df)
        current_bounds_df.to_csv(current_bounds_df_location, index=False)
    return current_bounds_df


def group_parameters(bounds_df):
    # Kopiere den bounds_df DataFrame
    bounds_df_copy = bounds_df.copy()

    # Importiere die Mapping-Tabelle
    mapping_table = import_mapping_table()

    print("Current bounds DataFrame:")
    print(bounds_df_copy)
    combined_params_df = pd.DataFrame(columns=["Parameter", "Grouped_Variable_Name"])
    grouped_df = pd.DataFrame(columns=bounds_df_copy.columns)

    while True:
        group_params = input("Enter parameters to group (comma-separated) or 'exit' to finish: ").split(",")
        group_params = [param.strip() for param in group_params]

        if "exit" in group_params:
            break

        param_types = []
        for param in group_params:
            param_type = mapping_table.loc[mapping_table["Simulation_Parameter_Name"] == param, "sim_component_parameter_suffix"].values[0]
            if param_types and param_type not in param_types:
                print(f"Parameter '{param}' has a different type than the previously selected parameters.")
                return grouped_df, combined_params_df, bounds_df_copy
            param_types.append(param_type)

        group_names = mapping_table.loc[mapping_table["Simulation_Parameter_Name"].isin(group_params), "Grouped_Variable_Name"].unique()

        if len(group_names) != 1:
            print("Error: The selected parameters have different group names.")
            return grouped_df, combined_params_df, bounds_df_copy

        group_name = group_names[0]
        all_matching_params = []

        for param in group_params:
            matching_params = mapping_table.loc[mapping_table["Simulation_Parameter_Name"] == param, "Simulation_Parameter_Name"].values
            all_matching_params.extend(matching_params)
            bounds_df_copy.loc[bounds_df_copy["Parameter"].isin(matching_params), "Parameter"] = group_name

        for param in group_params:
            combined_params_df = pd.concat(
                [combined_params_df, pd.DataFrame([{"Parameter": param, "Grouped_Variable_Name": group_name}])],
                ignore_index=True,
            )

        grouped_df = bounds_df_copy.groupby("Parameter").mean().reset_index()

        print(f"Current values for group '{group_name}':")
        print(grouped_df[grouped_df["Parameter"] == group_name])

        overwrite = input("Overwrite the averaged values? (yes/no): ").strip().lower()
        if overwrite == "yes":
            for col in grouped_df.columns:
                if col != "Parameter":
                    new_value = input(f"New value for '{col}': ").strip()
                    grouped_df.loc[grouped_df["Parameter"] == group_name, col] = float(new_value)

        # Remove original parameters and replace with the grouped entry
        bounds_df_copy = bounds_df_copy[~bounds_df_copy['Parameter'].isin(group_params)]
        new_row = pd.DataFrame({col: [grouped_df.loc[grouped_df['Parameter'] == group_name, col].values[0]] for col in bounds_df_copy.columns})
        bounds_df_copy = pd.concat([bounds_df_copy, new_row], ignore_index=True)

    return grouped_df, combined_params_df, bounds_df_copy    


def plot_time_series_data():
    """This function takes the last simulation result and plots it in comparison to the sensor data used for calibration"""
    # find last simulation result file
    pass

def clean_directory(directory_path):
    """Remove all files and subdirectories inside directory_path.

    Args:
        directory_path: Path to the directory to empty.
    """
    if not os.path.exists(directory_path):
        print(f"Directory '{directory_path}' does not exist.")
        return

    contents = os.listdir(directory_path)
    if not contents:
        print(f"Directory '{directory_path}' is already empty.")
        return

    for name in contents:
        path = os.path.join(directory_path, name)
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            print(f"Deleted: {path}")
        except Exception as e:
            print(f"Error deleting {path}: {e}")


def main():

    sigma = 0.05 
    # Number of Parameters from Cause List to be considered
    number_of_root_cause_parameters = 19 # These are ranked from the highest to the lowest impact according to the RCA
    # Bounds Dataframe contains all parameters that are considered as root causes
    # From these the top entries will be looped through and optimized
    continuous_or_discrete= 'continuous' # 'continuous'
    grid_factor = 10
    num_discrete_segments=10
    
    clean_directory(Bayesian_Config.DEST_PATH)    
        
    
    sigma = get_user_choice_for_calibration_or_adaptation()
    print(f"sigma: {sigma}")
    
    bounds_df = create_bounds_df(sigma=sigma, continuous_or_discrete=continuous_or_discrete, grid_factor=grid_factor, num_discrete_segments=num_discrete_segments)
    print(bounds_df)

    # Gruppierung der Parameter
    user_grouping_decision = input("Are there parameters with identical behaviour that can be grouped? (y/n): ")
    if user_grouping_decision.lower() == "y":
        grouped_df, combined_params_df, bounds_df = group_parameters(bounds_df)
        combined_params_df.to_csv(Bayesian_Config.GROUPED_PARAMETERS_FILE, index=False)
    elif user_grouping_decision.lower() == "n":
        print("No parameter grouping applied.")
    else:
        print("Invalid input. Please enter 'y' or 'n'.")
        return
    
    number_of_optimization_iterations = 8
    iterations_for_doe = 8
    error_tolerance = 0.01
    metamodel_data_file = 'Data_metamodel.csv'
    mapping_df = sensor_simvar_mapping.create_mapping_table()
   
    while True:
        print("""------------Simulationmodel Adaption Terminal------------
    (A) Loop adaption through all modelparameters (Initialization)
    (B) Start progressive model adaption in order of highest expected Improvement
    (C) Start parallel model adaption in order of highest expected Improvement
    (X) Return""")
        choice = input('Select:')

        match choice.upper():

            case "A":
                optimization_results_df = bounds_df[["Parameter", "Value"]].copy()
                optimization_results_df.rename(columns={"Value": "Value_before_single_Param_Optimization"}, inplace=True)

                for sim_col, real_col in REAL_COLUMNS_MAPPING.items():
                    optimization_results_df[f"Deviation_of_observed_{sim_col}_before_Optimization"] = None
                    optimization_results_df[f"Deviation_of_observed_{sim_col}_after_Optimization"] = None

                optimization_results_df["Total_Deviation_before_Optimization"] = None
                optimization_results_df["Value_after_single_Param_Optimization"] = None
                optimization_results_df["Total_Deviation_after_Optimization"] = None
                optimization_results_df["Improvement_of_Deviation"] = None
                optimization_results_df["Significance_of_Improvement"] = None
                optimization_results_df.to_csv(Bayesian_Config.OPTIMIZATION_RESULTS_FILE, index=False)

                global bounds
                iterations_for_doe = int(input(f"Current DoE samples: {iterations_for_doe}. Enter new value: "))
                number_of_optimization_iterations = int(input(f"Current optimization iterations: {number_of_optimization_iterations}. Enter new value: "))

                for i in range(min(len(bounds_df), number_of_root_cause_parameters)):
                    print(i)
                    bounds = write_bounds(bounds_df, i, continuous_or_discrete=continuous_or_discrete, discrete_bound_number=num_discrete_segments)
                    print(bounds)
                    param_name  = bounds_df.loc[i, "Parameter"]
                    param_value = bounds_df.loc[i, "Value"]
                    generate_initial_dataset(bounds, param_value, index_iter=i)
                    error_tolerance = 0.001
                    print(f"Error tolerance set to {error_tolerance} to find global optimum.")
                    print(f"Starting optimization: {number_of_optimization_iterations} iterations, {iterations_for_doe} LHS samples, tolerance {error_tolerance}")

                    Bayesian_Main.run_Bayes_optimization(
                        iterations_for_DoE=iterations_for_doe,
                        number_of_optimization_iterations=number_of_optimization_iterations,
                        error_tolerance=error_tolerance,
                        metamodel_data_file=metamodel_data_file,
                        bounds=bounds,
                        index_iter=i,
                    )
                    set_original_parameter(param_value, param_name)

                optimization_df = pd.read_csv(Bayesian_Config.OPTIMIZATION_RESULTS_FILE)
                evaluate_adaptation_improvement(optimization_df)
            
            case "B":
                evaluation_already_done = input("Has evaluation already been performed? (yes/no): ")
                if evaluation_already_done.lower() == "no":
                    optimization_df = pd.read_csv(Bayesian_Config.OPTIMIZATION_RESULTS_FILE)
                    evaluate_adaptation_improvement(optimization_df)
                else:
                    print("Evaluation already done — starting progressive parameter adaptation.")
                
                evaluation_results_location = EVALUATION_RESULTS_FILE
                evaluation_results_df = pd.read_csv(evaluation_results_location)

                evaluation_results_df = evaluation_results_df.sort_values(by="Improvement_of_Deviation", ascending=False)
                print(evaluation_results_df)
                plot_improvement_of_deviation(evaluation_results_df)
                transform_bounds_from_discrete_to_continuous()
                start_tkinter_app()

                evaluation_results_UserChoice_location = str(USER_EVALUATION_RESULTS_FILE)
                evaluation_results_UserChoice_df = pd.read_csv(evaluation_results_UserChoice_location)

                global current_bound
                error_tolerance = input(f"Current error tolerance: {error_tolerance}. Enter new value: ")
                iterations_for_doe = int(input(f"Current DoE samples: {iterations_for_doe}. Enter new value: "))
                number_of_optimization_iterations = int(input(f"Current optimization iterations: {number_of_optimization_iterations}. Enter new value: "))
                for i in range(min(len(evaluation_results_UserChoice_df), number_of_root_cause_parameters)):
                    setup_adaption_process(i)
                    if i == 0:
                        continue
                    else:
                        name_in_evaluation_results_UserChoice = evaluation_results_UserChoice_df.loc[i, "Parameter"]
                        index_for_bound = bounds_df[bounds_df["Parameter"] == name_in_evaluation_results_UserChoice].index[0]
                        current_bound = write_bounds(evaluation_results_UserChoice_df, i)
                        print(current_bound)
                        Bayesian_Main.run_Bayes_optimization(
                            iterations_for_DoE=iterations_for_doe,
                            number_of_optimization_iterations=number_of_optimization_iterations,
                            error_tolerance=error_tolerance,
                            metamodel_data_file=metamodel_data_file,
                            bounds=current_bound,
                            index_iter=index_for_bound,
                        )
            case "C":
                evaluation_already_done = input("Has evaluation already been performed? (yes/no): ")
                if evaluation_already_done.lower() == "no":
                    optimization_df = pd.read_csv(Bayesian_Config.OPTIMIZATION_RESULTS_FILE)
                    evaluate_adaptation_improvement(optimization_df)
                else:
                    print("Evaluation already done — starting parallel parameter adaptation.")
                evaluation_results_location = str(EVALUATION_RESULTS_FILE)
                evaluation_results_df = pd.read_csv(evaluation_results_location)
                evaluation_results_df = evaluation_results_df.sort_values(by="Improvement_of_Deviation", ascending=False)
                print(evaluation_results_df)
                plot_improvement_of_deviation(evaluation_results_df)
                start_tkinter_app()
                evaluation_results_UserChoice_location = str(USER_EVALUATION_RESULTS_FILE)
                evaluation_results_UserChoice_df = pd.read_csv(evaluation_results_UserChoice_location)
                max_number_of_parameters_to_optimize_parallel = int(input("How many parameters should be optimized in parallel? "))
                if max_number_of_parameters_to_optimize_parallel > len(evaluation_results_UserChoice_df):
                    print(f"Value exceeds the number of available parameters ({len(evaluation_results_UserChoice_df)}). Capping.")
                    max_number_of_parameters_to_optimize_parallel = len(evaluation_results_UserChoice_df)
                evaluation_results_UserChoice_df = evaluation_results_UserChoice_df.sort_values(by="Improvement_of_Deviation", ascending=False)
                print("Creating discrete bounds within the selected continuous bounds.")
                num_discrete_segments = int(input("Number of discrete segments: "))
                evaluation_results_UserChoice_df = transform_bounds_from_continuous_to_discrete(num_discrete_segments)
                number_of_root_cause_parameters = max_number_of_parameters_to_optimize_parallel
                single_or_multiple_adaptation = "multiple"
                continuous_or_discrete = "discrete"
                print(f"Optimizing {number_of_root_cause_parameters} parameters in parallel.")
                iterations_for_doe = int(input(f"Current DoE samples: {iterations_for_doe}. Enter new value: "))
                number_of_optimization_iterations = int(input(f"Current optimization iterations: {number_of_optimization_iterations}. Enter new value: "))
                if number_of_root_cause_parameters == 0:
                    continue
                else:
                    if single_or_multiple_adaptation == "multiple":
                        name_in_evaluation_results_UserChoice = []
                        index_for_bound = []
                        for i in range(number_of_root_cause_parameters):
                            name = evaluation_results_UserChoice_df.loc[i, "Parameter"]
                            name_in_evaluation_results_UserChoice.append(name)
                            index = bounds_df[bounds_df["Parameter"] == name].index[0]
                            index_for_bound.append(index)

                    current_bound = write_bounds(
                        bounds_df=evaluation_results_UserChoice_df,
                        num_rows=number_of_root_cause_parameters,
                        continuous_or_discrete=continuous_or_discrete,
                        discrete_bound_number=num_discrete_segments,
                        single_or_multiple=single_or_multiple_adaptation,
                    )
                    print(current_bound)
                    if not (isinstance(index_for_bound, list) and len(index_for_bound) == number_of_root_cause_parameters):
                        print("Error: index_for_bound must be a list with length equal to the number of parameters.")
                        break
                    error_tolerance = input(f"Current error tolerance: {error_tolerance}. Enter new value: ")
                    Bayesian_Main.run_Bayes_optimization(
                        iterations_for_DoE=iterations_for_doe,
                        number_of_optimization_iterations=number_of_optimization_iterations,
                        error_tolerance=error_tolerance,
                        metamodel_data_file=metamodel_data_file,
                        bounds=current_bound,
                        index_iter=index_for_bound,
                        number_of_parameters=number_of_root_cause_parameters,
                    )

                finetune = input("Finetune Case C results with continuous bounds? (y/n): ")
                if finetune.lower() == "y":
                    finetune_bounds_from_discrete_to_continuous(number_of_root_cause_parameters)
                    print("Finetuning completed.")
                    current_bounds_df = pd.read_csv(Bayesian_Config.CURRENT_BOUNDS_FILE)
                    continuous_or_discrete = "continuous"
                    current_bound = write_bounds(
                        bounds_df=current_bounds_df,
                        num_rows=number_of_root_cause_parameters,
                        continuous_or_discrete=continuous_or_discrete,
                        discrete_bound_number=num_discrete_segments,
                        single_or_multiple=single_or_multiple_adaptation,
                    )
                    print(current_bound)
                    error_tolerance = input(f"Current error tolerance: {error_tolerance}. Enter new value: ")
                    iterations_for_doe = int(input(f"Current DoE samples: {iterations_for_doe}. Enter new value: "))
                    number_of_optimization_iterations = int(input(f"Current optimization iterations: {number_of_optimization_iterations}. Enter new value: "))
                    Bayesian_Main.run_Bayes_optimization(
                        iterations_for_DoE=iterations_for_doe,
                        number_of_optimization_iterations=number_of_optimization_iterations,
                        error_tolerance=error_tolerance,
                        metamodel_data_file=metamodel_data_file,
                        bounds=current_bound,
                        index_iter=index_for_bound,
                        number_of_parameters=number_of_root_cause_parameters,
                    )

            case "X":
                print("Exiting.")
                break
            case _:
                print("Invalid input. Please try again.")
            
    
    
if __name__ == "__main__":
    main()