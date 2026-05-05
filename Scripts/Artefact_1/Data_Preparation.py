import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pandas as pd
import numpy as np
from scipy.signal import medfilt
from datetime import datetime
from typing import Dict, Tuple
from sensor_simvar_mapping import create_mapping_table, filter_dataframe


class DataPreparation:
    """
    A class to handle loading, preprocessing, and preparing real and simulation datasets,
    including mapping and unit harmonization.
    """

    def __init__(self, sensor_path: str, simulation_path: str):
        """
        Initialize the DataPreparation class with paths to sensor and simulation datasets.
        """
        self.sensor_data = self._load_data(sensor_path, "sensor")
        self.simulation_data = self._load_data(simulation_path, "simulation")
        self.mapping_df = create_mapping_table()
        self.mapping_dict = None
        self.clearname_mapping = None

    def _load_data(self, path: str, data_type: str) -> pd.DataFrame:
        """
        Load sensor or simulation data from a CSV file.
        """
        try:
            data = pd.read_csv(path)
            data = data.drop_duplicates(subset="time", keep="first")
            print(f"{data_type.capitalize()} data loaded successfully from {path}.")
            if data.empty:
                print("DataFrame is empty — aborting.")
                sys.exit()
            return data
        except Exception as e:
            raise ValueError(f"Error loading {data_type} data: {e}")

    def map_variables(self) -> None:
        """
        Map sensor variables to simulation variables using the mapping DataFrame.
        Clear names are derived from the mapping DataFrame's 'Name' column.
        Sensor data columns get a '_real' suffix, and simulation data columns get a '_sim' suffix.
        """
        sensor_columns = [col for col in self.sensor_data.columns if col != 'time']
        sim_columns = [col for col in self.simulation_data.columns if col != 'time']

        # Initialize a mapping dictionary to store sensor-to-simulation relationships
        self.mapping_dict = {}
        for sensor_col in sensor_columns:
            # Find the corresponding simulation variable for the sensor column in the mapping DataFrame
            match = self.mapping_df[self.mapping_df['Sensor_OPCUA_Node_ID'] == sensor_col]
            if not match.empty:
                sim_var = match['Simulation_variable_name'].iloc[0]
                if sim_var in sim_columns:
                    self.mapping_dict[sensor_col] = sim_var

        # Initialize a dictionary to store clear names for the sensor columns
        self.clearname_mapping = {}
        for sensor_col in sensor_columns:
            # Find the clear name for the sensor column in the mapping DataFrame
            match = self.mapping_df[self.mapping_df['Sensor_OPCUA_Node_ID'] == sensor_col]
            if not match.empty:
                clearname = match['Name'].iloc[0]
                self.clearname_mapping[sensor_col] = clearname

        # Create new column names for sensor_data and simulation_data
        sensor_renamed_columns = {}
        simulation_renamed_columns = {}
        for sensor_col, clearname in self.clearname_mapping.items():
            # Sensor columns get a '_real' suffix
            sensor_renamed_columns[sensor_col] = f"{clearname}_real"
            # Simulation columns get a '_sim' suffix
            if sensor_col in self.mapping_dict:
                sim_col = self.mapping_dict[sensor_col]
                simulation_renamed_columns[sim_col] = f"{clearname}_sim"

        # Rename columns in sensor_data based on the sensor_renamed_columns mapping
        self.sensor_data.rename(columns=sensor_renamed_columns, inplace=True)

        # Rename columns in simulation_data based on the simulation_renamed_columns mapping
        self.simulation_data.rename(columns=simulation_renamed_columns, inplace=True)
        # Delete unused columns in simulation_data except for "time"
        self.simulation_data.drop(columns=[col for col in self.simulation_data.columns if col not in simulation_renamed_columns.values() and col != "time"], inplace=True)
        print("Sensor-Simulation variable mapping completed with clear names.")


    def resample_simulation(self) -> None:
        """
        Resample the simulation data to match the timestamps of the sensor data.
        Adjusts for '_real' and '_sim' suffixes in column names.
        """
        self.sensor_data = self.sensor_data.sort_values('time')
        self.simulation_data = self.simulation_data.sort_values('time')
        resampled_simulation = pd.DataFrame({'time': self.sensor_data['time']})

        # Iterate through the mapping dictionary to resample simulation data
        for sensor_col, sim_col in self.mapping_dict.items():
            # Derive the clear names with '_real' and '_sim' suffixes
            sensor_col_with_suffix = f"{self.clearname_mapping[sensor_col]}_real"
            sim_col_with_suffix = f"{self.clearname_mapping[sensor_col]}_sim"

            # Ensure the simulation column exists before proceeding
            if sim_col_with_suffix not in self.simulation_data.columns:
                print(f"Skipping column '{sim_col_with_suffix}' as it does not exist in simulation data.")
                continue

            # Resample the simulation column to match sensor timestamps
            ## differentiale between analogues and binary variables in the simulation
            try:
                resampled_simulation[sim_col_with_suffix] = np.interp(
                    self.sensor_data['time'].astype(float),
                    self.simulation_data['time'].astype(float),
                    self.simulation_data[sim_col_with_suffix],
                )
                binary_or_analogue = self.mapping_df[self.mapping_df['Sensor_OPCUA_Node_ID'] == sensor_col]['Binary_or_Analogue'].iloc[0]
                if binary_or_analogue == 'binary':
                    resampled_simulation[sim_col_with_suffix] = np.round(resampled_simulation[sim_col_with_suffix])
                    resampled_simulation[sim_col_with_suffix] = resampled_simulation[sim_col_with_suffix].apply(lambda x: 1 if x >= 1 else 0)
            except Exception as e:
                print(f"Error resampling column '{sim_col_with_suffix}': {e}")
                print("Dataframe might be empty due to aborted simulation")

        self.simulation_data = resampled_simulation
        if not self.sensor_data['time'].equals(self.simulation_data['time']):
            raise ValueError("Time column values are not aligned between sensor and simulation data.")
        print("Simulation data resampled to align with sensor data timestamps.")



    def harmonize_units(self) -> None:
        """
        Harmonize units between the sensor and simulation data based on the mapping DataFrame.
        Adjusts for '_real' and '_sim' suffixes in column names.
        """
        # Define unit conversion factors as a dictionary
        conversions = {
            ('m3', 'ml'): 1e6,
            ('bar', 'kPa'): 100,
            ('m3/s', 'l/min'): 60000,
            ('m', 'cm'): 100,
            ('binary', 'binary'): 1,
            ('°C', '°C'): 1,
            ('not_assigned', 'not_assigned'): 1,
            ('R201_not_in_model', 'binary'): 1,
        }


        # Iterate through the mapping dictionary
        for sensor_col, sim_col in self.mapping_dict.items():
            # Find the row in the mapping DataFrame corresponding to this mapping
            row = self.mapping_df[self.mapping_df['Sensor_OPCUA_Node_ID'] == sensor_col]
            if row.empty:
                print(f"Skipping column '{sensor_col}' because it was not found in the mapping.")
                continue

            # Extract the units from the mapping 
            # We want the units of the Sensors, thus we convert from the Simulation (from_unit) to the Sensor (to_unit)
            from_unit = row['Unit_Simulation_variable'].iloc[0]
            to_unit = row['Unit_Sensor'].iloc[0]
             

            # Perform the unit conversion if the pair exists in the conversion dictionary
            if (from_unit, to_unit) in conversions:
                # Adjust for '_real' and '_sim' suffixes in column names
                sensor_col_with_suffix = f"{self.clearname_mapping[sensor_col]}_real"
                sim_col_with_suffix = f"{self.clearname_mapping[sensor_col]}_sim"
                # Only Apply conversion to the simulation columns because sensor data is already in the desired unit
                if sim_col_with_suffix in self.simulation_data.columns:
                    self.simulation_data[sim_col_with_suffix] *= conversions[(from_unit, to_unit)]

        print("Unit harmonization completed.")

    def remove_sensor_errors(self) -> None:
        """Sensor Errors include negative Values for Volume, Level, Pressure and Temperature as well as sudden jumps for Volume, Level and Temperature"""
        # Remove negative values for Volume, Level, Pressure and Temperature
        # 1. Volume, Level and pressure should not be negative
        for col in self.sensor_data.columns:
            if 'Level' in col or 'Volume' in col:
                print(f"Negative values in {col}: deemed unrealstic and will be set to 0.")
                self.sensor_data[col] = self.sensor_data[col].apply(lambda x: max(x, 0))
        pass
    
        # 2. ensure that there are no sudden jumps in the data of Volume, Level and Temperature
        # Volume: ml
        # Level: cm
        # Temperature: °C
        self.peak_filter(volume_threshold=1000, level_threshold=15, temperature_threshold=15)
        
        
    
    def peak_filter(self, volume_threshold: float, level_threshold: float, temperature_threshold: float) -> None:
        """Detect sudden jumps in sensor data and smooth them with a median filter.

        Args:
            volume_threshold: Max allowed single-step change for volume columns.
            level_threshold: Max allowed single-step change for level columns.
            temperature_threshold: Max allowed single-step change for temperature columns.
        """
        for col in self.sensor_data.columns:
            if 'volume' in col.lower():
                jump_threshold = volume_threshold
            elif 'level' in col.lower():
                jump_threshold = level_threshold
            elif 'temperature' in col.lower():
                jump_threshold = temperature_threshold
            else:
                continue

            time_diffs = self.sensor_data['time'].diff().fillna(0).astype(float)
            value_diffs = self.sensor_data[col].diff().fillna(0).abs()
            sudden_jumps = (time_diffs < 5) & (value_diffs > jump_threshold)

            if sudden_jumps.any():
                print(f"Sudden jumps detected in {col}. These will be smoothed out.")

            self.sensor_data[col] = medfilt(self.sensor_data[col], kernel_size=3)    
    
    def denoise_sensor_data(self, window_size=3, sensors_to_smoothen=None) -> None:
        """
        Denoise sensor data using a moving average filter.
        
        Parameters:
            window_size (int): The size of the moving average window. Must be an odd number.
        """
        # List of Sensors that should be smoothened
        sensor_list = filter_dataframe(self.mapping_df,role='Sensor', binary_or_analogue='analogue')
        # create clearnames by mapping_df since the sensor_dataset has been changed to clearnames
        sensor_list = [self.mapping_df[self.mapping_df['Sensor_OPCUA_Node_ID'] == sensor]['Name'].values[0] for sensor in sensor_list]
        # add suffix "_real" to the sensor_list
        sensor_list = [sensor + "_real" for sensor in sensor_list]
        if window_size % 2 == 0:
            raise ValueError("Window size must be an odd number.")

        for col in self.sensor_data.columns:
            if col in sensor_list:
            # Skip columns that are non-numeric or not suitable for denoising
                if not np.issubdtype(self.sensor_data[col].dtype, np.number):
                    print(f"Skipping column '{col}' as it is not numeric.")
                    continue
                # Apply moving average to the column
                smoothed_series = self.sensor_data[col].rolling(window=window_size, center=True, min_periods=1).mean()
                # Fill NaN values with original values
                self.sensor_data[col] = smoothed_series.fillna(self.sensor_data[col])
            else:
                continue
        print(f"Data has been denoised using a moving average with window size {window_size}.")

    def get_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        return self.sensor_data, self.simulation_data
