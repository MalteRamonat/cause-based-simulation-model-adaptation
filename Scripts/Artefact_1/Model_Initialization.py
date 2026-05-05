import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pandas as pd
import re
import shutil
import sensor_simvar_mapping
from OMPython_Functionalities import (
    get_modelica_parameter_data, simulate, get_modelica_continuous_data,
    start_modelica, set_parameters, get_result_file,
)
import Config




class ModelInitialization():
    def __init__(self,sensor_data_path: str, exclude_actuators: list = []):
        self.search_pattern = re.compile(
            r'Modelica\.Blocks\.Sources\.CombiTimeTable\s+ActuatorControl\(table\s*=\s*\[(.*?)\]\s*,',
    
            re.DOTALL
        )
        self.simulation_file_path = str(Config.MODELICA_FILE_DIR / Config.MODELICA_FILE_NAME)
        self.backup_file_path = str(Config.MODELICA_BACKUP_DIR) + "/"
        self.modelica_file_name = Config.MODELICA_FILE_NAME
        self.sensor_data_path = sensor_data_path
        self.exclude_actuators = exclude_actuators
        self.dict_for_input_conditions = Config.INPUT_TABLE_FILES
    
    def read_csv(self):
        try:
            df = pd.read_csv(self.sensor_data_path)
            print("CSV file successfully loaded.")
            print("\nFirst few rows of the DataFrame:")
            print(df.head())
            # Changed for GAS
            df = df.drop_duplicates(subset="time", keep="first")
            return df
        except FileNotFoundError:
            print(f"File '{self.sensor_data_path}' not found.")
            return None    

    def convert_timestamp_to_seconds(self, dataframe, timestamp_column_name):
        if timestamp_column_name not in dataframe.columns:
            print(f"Column '{timestamp_column_name}' not found in the DataFrame.")
            return None

        dataframe[timestamp_column_name] = pd.to_datetime(dataframe[timestamp_column_name])
        dataframe['TimeInSeconds'] = (dataframe[timestamp_column_name] - dataframe[timestamp_column_name].iloc[0]).dt.total_seconds()
        return dataframe

    def format_dataframe_as_string(self, dataframe):
        formatted_rows = []
        for _, row in dataframe.iterrows():
            formatted_values = [str(value) for value in row]
            formatted_row = ", ".join(formatted_values)
            formatted_rows.append(formatted_row)
        formatted_string = "; ".join(formatted_rows)
        return f"[{formatted_string}]"


    def remove_consecutive_duplicates(self, df):
        df_copy = df.copy()
        columns = [col for col in df_copy.columns if col != 'Session Time Stamps']
        mask = df_copy[columns].shift(1) != df_copy[columns]
        df_copy = df_copy[mask.any(axis=1)]
        return df_copy

    def replace_string_in_modelica_file(self, file_path, search_pattern, new_string):
        with open(file_path, 'r+') as file:
            content = file.read()
            content = re.sub(search_pattern, new_string, content)
            file.seek(0)
            file.truncate()
            file.write(content)

    def replace_actuator_table_contents(self, new_actuator_table_contents):
        # Create a Backup because this is altering the modelica file
        shutil.copyfile(self.simulation_file_path, self.backup_file_path + self.modelica_file_name)
        print(f"Backup created: {self.backup_file_path}{self.modelica_file_name}")

        with open(self.simulation_file_path, 'r') as file:
            modelica_model_as_string = file.read()

        matches = self.search_pattern.findall(modelica_model_as_string)
        if not matches:
            print("No match found.")
            return

        print("Match found. Replacing actuator table contents...")
        modified_modelica_model_string = modelica_model_as_string.replace(matches[0], new_actuator_table_contents)
        with open(self.simulation_file_path, 'w') as file:
            file.write(modified_modelica_model_string)
        print(f"Replacement completed. Model saved at {self.simulation_file_path}")
        
    def replace_table_contents_by_blockname(self, modelica_file_path: str, block_name: str, new_table_string: str):
        # Backup
        shutil.copyfile(self.simulation_file_path, self.backup_file_path + self.modelica_file_name)
        print(f"Backup created: {self.backup_file_path}{self.modelica_file_name}")

        # Read Modelica file
        with open(self.simulation_file_path, 'r') as file:
            modelica_model_as_string = file.read()

        # Regex: suche table = [...] in einem spezifischen Block
        pattern = re.compile(
            rf'Modelica\.Blocks\.Sources\.CombiTimeTable\s+{block_name}\(.*?table\s*=\s*\[(.*?)\]\s*(?=[,;\)])',
            re.DOTALL
        )
        match = pattern.search(modelica_model_as_string)
        if not match:
            print(f"No table found for block: {block_name}")
            return

        old_table = match.group(1)
        print(f"Old table found: {old_table}")
        print(f"New table to be inserted: {new_table_string}")
        modelica_model_as_string = modelica_model_as_string.replace(old_table, new_table_string.strip("[]"))

        # Save
        with open(modelica_file_path, 'w') as file:
            file.write(modelica_model_as_string)
        print(f"Table for '{block_name}' replaced in {modelica_file_path}")   
        

    def initialize_start_values_for_sensors(self, sensor_list, mapping_df, opcua_dataframe, mod):
        sensor_columns = ['Session Time Stamps'] + sensor_list
        sensor_data_frame = opcua_dataframe.drop(columns=opcua_dataframe.columns.difference(sensor_columns))
        sensor_data_frame = self.convert_units(sensor_data_frame, mapping_df)

        sensor_init_dict = {col: sensor_data_frame[col].iloc[0] for col in sensor_data_frame.columns if col != 'Session Time Stamps'}
        sensor_init_dict = {mapping_df[mapping_df['Sensor_OPCUA_Node_ID'] == key]['Simulation_initialization_parameters'].values[0]: value 
                            for key, value in sensor_init_dict.items()}
        sensor_init_dict = {key: value for key, value in sensor_init_dict.items() if not key.startswith('not_needed')}
        for key, value in sensor_init_dict.items():
            if key.endswith('level_start') and value < 0:
                print(f"Warning: {key} is negative ({value}). Clamping to 0.0001.")
                sensor_init_dict[key] = 0.0001
        print("Initial sensor values:")
        for key, value in sensor_init_dict.items():
            print(f"{key}: {value}")
        # Delete sensor_init_dict entries that do not contain "level_start"
        sensor_init_dict = {key: value for key, value in sensor_init_dict.items() if 'level_start' in key}
        print("Reduced sensor values:")
        for key, value in sensor_init_dict.items():
            print(f"{key}: {value}")
        set_parameters(mod, sensor_init_dict)

    def create_actuator_table_from_excel(self, excel_file_path):
        # load Dataframe
        actuator_data_frame = pd.read_excel(excel_file_path)
        
        # Ensure that all actuators are present in the dataframe
        actuator_column_names = Config.ACTUATOR_ORDER_IN_MODELICA
        missing_columns = set(actuator_column_names) - set(actuator_data_frame.columns)
        if missing_columns:
            print(f"Warning: Missing actuator columns: {missing_columns}")
        new_order = [Config.ACTUATOR_TIME_COLUMN] + [col for col in actuator_column_names if col in actuator_data_frame.columns]
        actuator_data_frame = actuator_data_frame[new_order]
        
        formatted_acutator_string = self.format_dataframe_as_string(actuator_data_frame).strip('[]')
        print(formatted_acutator_string)
        return f"[{formatted_acutator_string}]"
    
    def convert_csv_to_modelica_table(self,csv_file_path, table_name, output_file_path):
        # Lade die CSV-Datei
        df = pd.read_csv(csv_file_path)
        n_rows, n_cols = df.shape
        lines = ["#1\n"]
        lines.append(f"double {table_name}({n_rows},{n_cols})   # Modelica table\n")
        for row in df.itertuples(index=False):
            line = "  " + "  ".join(str(val) for val in row) + "\n"
            lines.append(line)
        with open(output_file_path, "w") as f:
            f.writelines(lines)
    
    def convert_units(self, sensor_data_frame, mapping_df):
        unit_conversion_factors = {
            ('cm', 'm'): 0.01,
            ('m3/s', 'l/s'): 1000,
            ('l/min', 'm3/s'): 1 / 60000,
            ('l/min', 'kg/s'): 1 / 60,
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
                sensor_data_frame[column] *= factor
            elif unit_sensor != unit_simulation:
                print(f"No conversion factor for units '{unit_sensor}' and '{unit_simulation}'.")

        return sensor_data_frame
    
    def return_simulation_data(self):
        return self.simulation_data
    def load_and_merge_actuator_data(self, actuator_dict):
        """Load and merge CSV files from a dictionary of actuator file paths.

        Args:
            actuator_dict: Mapping of actuator name → CSV file path.

        Returns:
            Merged and time-sorted DataFrame with duplicates removed.
        """
        dataframes = []
        for key, file_path in actuator_dict.items():
            df = pd.read_csv(file_path)
            if "time" not in df.columns:
                raise ValueError(f"Missing 'time' column in file for '{key}'.")
            dataframes.append(df)

        merged_df = pd.concat(dataframes, axis=0).sort_values(by="time").reset_index(drop=True)
        merged_df.ffill(inplace=True)
        merged_df = merged_df.dropna(subset=merged_df.columns.difference(["time"]))
        merged_df = merged_df.drop_duplicates(subset="time", keep="first")
        return merged_df
    
    def run(self):
        opcua_dataframe = self.read_csv()

        mapping_df = sensor_simvar_mapping.create_mapping_table()
        actuator_list = sensor_simvar_mapping.filter_dataframe(mapping_df, 'Actuator')
        # Not needed for GAS
        actuator_excel_table_path = Config.ACTUATOR_EXCEL_TABLE_PATH

        # check if one of the actuators is in the exclude list
        for actuator in actuator_list:
            if actuator in self.exclude_actuators:
                actuator_list.remove(actuator)

        # Create the actuator table --> This needs to be done before the model is started because it alters the models source code
        # This is done because the size of the matrix, i.e. timesteps may change and this can not be done while the model is running (adding new parameters is forbidden during runtime)
        # Changed for GAS
        #create_actuator_table_from_sensors = input("Do you want to create the actuator table from the real dataset? (y/n): ")
        create_actuator_table_from_sensors = input("Do you want to create the input conditions from the real datasets? (y/n): ")
        if create_actuator_table_from_sensors.lower() == 'y':
            
            print(f"Creating Actuator Matrix from the dataset provided in {self.sensor_data_path}")
            # Changed for GAS
            #actuator_columns = ['Session Time Stamps'] + actuator_list
            actuator_columns = ['time'] + actuator_list
            actuator_data_frame = opcua_dataframe.drop(columns=opcua_dataframe.columns.difference(actuator_columns))
            actuator_data_frame.to_csv(str(Config.COMPARISON_ACTUATOR_POSITIONS_FILE), index=False)
            actuator_dict = {key: value for key, value in self.dict_for_input_conditions.items() if key in ["ThreeWayValve_Input", "Choke_Valve_Input"]}
            actuator_data_frame = self.load_and_merge_actuator_data(actuator_dict)

            for block_name, csv_file_path in self.dict_for_input_conditions.items():
                input_condition_data_frame = pd.read_csv(csv_file_path)
                print(f"Creating Input Conditions from the dataset provided in {csv_file_path}")
                formatted_output = self.format_dataframe_as_string(input_condition_data_frame).strip('[]')
                self.replace_table_contents_by_blockname(self.simulation_file_path, block_name, formatted_output)
            # To Do: Ensure correct Actuator Order in Matrix    
            
            
            
        elif create_actuator_table_from_sensors.lower() == 'n':
            #changed for GAS
            print("Not yet implemented for GAS")
            pass
            create_actuator_Table_from_excel = input("Do you want to create the actuator table from an Excel file? (y/n): ")
            if create_actuator_Table_from_excel.lower() == 'y':
                print(f"Creating Actuator Matrix from Table provided in {actuator_excel_table_path}")
                # To Do: Implement the possibility to provide a table with the actuator values
                formatted_output = self.create_actuator_table_from_excel(actuator_excel_table_path)
                # To Do: Ensure correct Actuator Order in Matrix    
                self.replace_actuator_table_contents(formatted_output)
            elif create_actuator_Table_from_excel.lower() == 'n':
                print("Using Actuator Matrix from the modelica file")
                pass
        
        
        mod = start_modelica()

        sensor_list = sensor_simvar_mapping.filter_dataframe(mapping_df, 'Sensor', 'analogue')
        # Filter Sensor list for sensors that contain the stirng "level_start"
        # sensor_list = [sensor for sensor in sensor_list if 'level_start' in sensor]
        create_initial_sensor_values = input("Do you want to create the initial sensor values? from the real dataset? (y/n): ")
        if create_initial_sensor_values.lower() == 'y':
            #changed for GAS
            print("Not needed for GAS. Script not updated and will be faulty")
            print(f"Creating Initial Values from the dataset provided in {self.sensor_data_path}")
            # Initialize the start values for the sensors - This is done while the model is started
            self.initialize_start_values_for_sensors(sensor_list, mapping_df, opcua_dataframe, mod)
        elif create_initial_sensor_values.lower() == 'n':
            create_initial_sensor_values_from_csv = input("Do you want to create the initial sensor values from a CSV file? (y/n): ")
            if create_initial_sensor_values_from_csv.lower() == 'y':   
                #changed for GAS
                print("You should have activated tableOnFile within your Modelica model for this to work")
                for block_name, csv_file_path in self.dict_for_input_conditions.items():
                    input_condition_data_frame = pd.read_csv(csv_file_path)
                    print(f"Creating Input Conditions as external .txt file from the dataset provided in {csv_file_path}")
                    modelica_table_filename = str(Config.MODELICA_TIMETABLES_DIR / (block_name + ".txt"))
                    self.convert_csv_to_modelica_table(csv_file_path, table_name=block_name, output_file_path=modelica_table_filename)
                    print(f"Table for {block_name} created in {modelica_table_filename}")
                # print(f"Creating Initial Values from {Config.sensor_csv_table_path}")
                # manual_sensor_dataframe = pd.read_csv(Config.sensor_csv_table_path)
                # self.initialize_start_values_for_sensors(sensor_list, mapping_df, manual_sensor_dataframe, mod)
            elif create_initial_sensor_values_from_csv.lower() == 'n':
                print("Using Initial Sensor Values from the modelica file")
                pass

        modelica_parameter_list = get_modelica_parameter_data(mod)

        simulate(
            simulation_setup=None,
            selected_plot_params=None,
            solver=Config.SOLVER,
            start_time=Config.START_TIME,
            stop_time=Config.STOP_TIME,
            step_count=Config.STEP_COUNT,
            mod=mod,
            usage="Initialize_Simulation",
        )
        simulation_result_file = f"{Config.MODELICA_MODEL_NAME}_res.csv"
        destination_file_path = os.path.join(str(Config.SIMULATION_RESULTS_DIR), simulation_result_file)
        return destination_file_path
        

if __name__ == "__main__":
    simulation = ModelInitialization(str(Config.CURRENT_DATASET_PATH), exclude_actuators=[])
    simulation.run()