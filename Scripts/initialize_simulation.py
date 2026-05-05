import pandas as pd
import Config
import sensor_simvar_mapping
from OMPython_Functionalities import getParameterModelica_Data, simulate, getContinuousModelica_Data, startModelica, set_parameters
import re
import shutil


def read_csv(filename):
    # Read the CSV file into a DataFrame
    try:
        df = pd.read_csv(filename)
        print("CSV file successfully loaded.")
       
        # Display the first few rows of the DataFrame
        print("\nFirst few rows of the DataFrame:")
        print(df.head())
            
        return df
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
        return None


def convert_timestamp_to_seconds(dataframe, timestamp_column_name):
    if timestamp_column_name not in dataframe.columns:
        print(f"Column '{timestamp_column_name}' not found in the DataFrame.")
        return None
    
    # Convert the timestamp column to pandas datetime
    dataframe[timestamp_column_name] = pd.to_datetime(dataframe[timestamp_column_name])
    
    # Calculate the time differences in seconds and create a new column
    dataframe['TimeInSeconds'] = (dataframe[timestamp_column_name] - dataframe[timestamp_column_name].iloc[0]).dt.total_seconds()
    
    return dataframe


def format_dataframe_as_string(dataframe):
    formatted_rows = []
    for index, row in dataframe.iterrows():
        formatted_values = [str(value) for value in row]
        formatted_row = ", ".join(formatted_values)
        formatted_rows.append(formatted_row)
    
    formatted_string = "; ".join(formatted_rows)
    return f"[{formatted_string}]"

#def overwrite_values_in_modelica():
    
def check_model_component(component_name, modelica_model):
    # Check if a specified model component exists in the model
    pass


def check_order_of_actuators(actuator_list, mapping_df):
    
    intended_order = Config.actuator_order_in_modelica
    # make sure the order of the actuator List is in line with the ActuatorControl exit signals
    # Check if the order of the actuator list is in line with the intended order
    if actuator_list != intended_order:
        # Map the actuator names to the corresponding sensor IDs using the mapping dataframe
        mapped_actuator_list = [mapping_df[mapping_df['OPCUA_Node_ID'] == actuator]['Sensor_ID'].values[0] for actuator in actuator_list]
        
        # Sort the mapped actuator list based on the intended order
        sorted_actuator_list = [actuator for _, actuator in sorted(zip(Config.actuator_order_in_modelica, mapped_actuator_list))]
        
        # Update the actuator list with the sorted actuator list
        actuator_list = sorted_actuator_list
    else:
        print("Actuator list is in the intended order.")


def remove_consecutive_duplicates(df):
    df_copy = df.copy()
    columns = [col for col in df_copy.columns if col != 'Session Time Stamps']
    mask = df_copy[columns].shift(1) != df_copy[columns]
    return df_copy[mask.any(axis=1)]


def replace_string_in_modelica_file(file_path, search_pattern, new_string):
    with open(file_path, 'r+') as file:
        content = file.read()
        content = re.sub(search_pattern, new_string, content)
        file.seek(0)
        file.truncate()
        file.write(content)


def replace_actuator_table_contents_in_modelica_file(file_path, search_pattern, new_actuator_table_contents, backup_file_path=Config.modelicafilelocation_backup, modelica_file_name=Config.modelicafilename):
    
    # Check if user wants to update actuator positions in the modelica model
    user_input = input("Do you want to update the actuator positions in the Modelica model? (y/n): ")
    if user_input.lower() != 'y':
        print("Actuator positions will not be updated in the Modelica model.")
        return
    # make a backup of the modelica model
    shutil.copyfile(file_path, backup_file_path+modelica_file_name)
    print(f"Backup of the modelica model created: {backup_file_path}{modelica_file_name}")
    # Open the file in read and write mode
    with open(file_path, 'r') as file:
        modelica_model_as_string = file.read()
    
    # Find ActuatorControl table contents based on predefined search pattern
    matches = search_pattern.findall(modelica_model_as_string)
    if matches is None:
        print("No match found.")
        return
    else:
        print("Match found.")
        print(matches[0])
        print("Replacing the matched string with the new actuator table contents...")
        # Replace String in the modelica model as a string 
        modified_modelica_model_string = modelica_model_as_string.replace(matches[0], new_actuator_table_contents)
        # Write the modified string to the modelica model file
        with open(file_path, 'w') as file:
            file.write(modified_modelica_model_string)
        print("Replacement completed.")       


def initialize_start_values_for_sensors(sensor_list, mapping_df, opcua_dataframe, mod):
       
    sensor_columns = ['Session Time Stamps'] + sensor_list
    sensor_data_frame = opcua_dataframe.drop(columns=opcua_dataframe.columns.difference(sensor_columns))
    # make sure units are correct
    sensor_data_frame = convert_units(sensor_data_frame, mapping_df)
    sensor_init_dict ={}
    for col in sensor_data_frame.columns:
        # get the first value of each sensor       
        sensor_init_dict[col] = sensor_data_frame[col].iloc[0]
    # Session Time Stamps is not a sensor value
    # delete 'Session Time Stamps' key and its value from the dictionary
    sensor_init_dict.pop('Session Time Stamps', None)
    # change the keys of the dictionary to the corresponding Simulation_initialization_parameters found in the mapping dataframe
    sensor_init_dict = {mapping_df[mapping_df['Sensor_OPCUA_Node_ID'] == key]['Simulation_initialization_parameters'].values[0]: value for key, value in sensor_init_dict.items()}
    # delete all keys that show 'not_needed' in the mapping dataframe
    sensor_init_dict = {key: value for key, value in sensor_init_dict.items() if not key.startswith('not_needed')}
    print(sensor_init_dict)
    # Choose sensors / parameters to initialize simulation
    print("Choose sensors / parameters to initialize simulation:")
    print("1. All Elements")
    for index, key in enumerate(sensor_init_dict.keys()):
        print(f"{index+2}. {key}")

    user_choice = input("Enter the numbers corresponding to your choices (comma-separated): ")
    if user_choice == "1":
        # No elements to delete, keep all elements
        pass
    else:
        # Convert user_choice to a list of integers
        user_choice = [int(choice) for choice in user_choice.split(",")]

        # Create a list of keys to delete
        keys_to_delete = []
        for index, key in enumerate(sensor_init_dict.keys()):
            if index+2 not in user_choice:
                keys_to_delete.append(key)

        # Delete keys from sensor_init_dict
        for key in keys_to_delete:
            sensor_init_dict.pop(key)

    print(sensor_init_dict)
    
    # overwrite sensor values in modelica model
    set_parameters(mod, sensor_init_dict)
    

def convert_units(sensor_data_frame, mapping_df):
    # Definieren Sie die Umrechnungsfaktoren
    unit_conversion_factors = {
        ('cm', 'm'): 0.01,
        ('m3/s', 'l/s'): 1000,
        ('l/min', 'm3/s'): 1 / 60000,
        ('l/min', 'kg/s'): 1 / 60,  # assumes water density 1000 kg/m³
        ('ml', 'm3'): 1e-6,
        ('kPa', 'bar'): 0.01
    }

    for column in sensor_data_frame.columns:
        if column == 'Session Time Stamps':
            continue
        row = mapping_df[mapping_df['Sensor_OPCUA_Node_ID'] == column].iloc[0]
        unit_sensor = row['Unit_Sensor']
        unit_simulation = row['Unit_Simulation_initialization_parameters']
        if (unit_sensor, unit_simulation) in unit_conversion_factors:
            factor = unit_conversion_factors[(unit_sensor, unit_simulation)]
            sensor_data_frame[column] = sensor_data_frame[column] * factor
        elif unit_sensor == unit_simulation:
            pass
        else:
            print(f"No conversion factor found for units '{unit_sensor}' and '{unit_simulation}'.")
            
    return sensor_data_frame



def main():


    search_pattern = re.compile(
    r'Modelica\.Blocks\.Sources\.CombiTimeTable\s+ActuatorControl\(table\s*=\s*\[(.*?)\]\s*,',
    re.DOTALL)
            
    file_path = Config.modelicafilelocation+Config.modelicafilename
     
        
    # Set datapath to access the historical data from opc ua
    digital_shadow_path = Config.path_to_current_dataset
    # set datapath to access the simulation model output
    modelica_output_path = Config.Temp_path
    # set path to the modelica model
    model_path = Config.modelicafilelocation+Config.modelicafilename
    # read opcua data from digital shadow as csv
    sensor_filepath = Config.path_to_current_dataset
    opcua_dataframe = read_csv(sensor_filepath)
    
    # map data to modelica model
    mapping_df = sensor_simvar_mapping.create_mapping_table()
    actuator_list = sensor_simvar_mapping.filter_dataframe(mapping_df, 'Actuator')
    #delete mixer, since I cannot use it in simulation
    if 'ns=4;s=|var|WAGO 750-8212 PFC200 G2 2ETH RS.Application.IoConfig_Globals_Mapping.R201_Control' in actuator_list:
        actuator_list.remove('ns=4;s=|var|WAGO 750-8212 PFC200 G2 2ETH RS.Application.IoConfig_Globals_Mapping.R201_Control')

    # get actuator positions from historical data
    actuator_columns = ['Session Time Stamps'] + actuator_list
    actuator_data_frame = opcua_dataframe.drop(columns=opcua_dataframe.columns.difference(actuator_columns))
    
    # Delete rows with no changes in actuator positions 
    actuator_data_frame = remove_consecutive_duplicates(actuator_data_frame)
    # save actuator data to csv
    actuator_data_frame.to_csv('modelica_model_actuator_input.csv', index=False)
    # change actuator positions to form required by modelica model
    formatted_output = format_dataframe_as_string(actuator_data_frame)
    # Remove the square brackets
    formatted_output = formatted_output.strip('[]')
    # fill ActuatorControl table with new values
    replace_actuator_table_contents_in_modelica_file(file_path, search_pattern, formatted_output)
    # get modelica model
    mod = startModelica()
    # get sensor values from historical data
    # filter for analogue sensors
    sensor_list = sensor_simvar_mapping.filter_dataframe(mapping_df, 'Sensor', 'analogue')
    initialize_start_values_for_sensors(sensor_list, mapping_df, opcua_dataframe, mod)
    getParameterModelica_Data(mod)
    
    # setup simulation parameters
    solver = 'ida'
    startTime = '0'
    stopTime = '600'
    StepNumber = '600'
    # run simulation
    #SimulationSetupParameter, SelectedParameterPlot, solver, startTime, stopTime, StepNumber, mod, usage='GUI'
    simulate(SimulationSetupParameter=None, SelectedParameterPlot=None, solver=solver, startTime=startTime, stopTime=stopTime, StepNumber=StepNumber, mod=mod, usage='Initialize_Simulation')
    

if __name__ == "__main__":
    main()


