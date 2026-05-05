import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error
from typing import Dict, Tuple
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
from sensor_simvar_mapping import create_mapping_table

class DeviationDetection:
    """
    A class to calculate deviations (MAE and SMAPE) between real and simulation data
    and detect time shifts.
    """

    def __init__(self, sensor_data: pd.DataFrame, simulation_data: pd.DataFrame):
        """
        Initialize with prepared sensor and simulation data.
        """
        self.sensor_data = sensor_data.set_index('time')
        self.simulation_data = simulation_data.set_index('time')
        self.sensor_data = self.sensor_data[~self.sensor_data.index.duplicated(keep='first')]
        self.simulation_data = self.simulation_data[~self.simulation_data.index.duplicated(keep='first')]
        self.mapping_df = create_mapping_table()

    def scale_data(self):
        """
        Scale the simulation and sensor data to the same range.
        Necessary preprocessing: both dataframes must have been aligned with regard to their units.
        Uses mapping_df to resolve column names and their suffixes.
        """
        for _, row in self.mapping_df.iterrows():
            # Extract the original sensor and simulation column names
            sensor_col = row['Sensor_OPCUA_Node_ID']
            sim_col = row['Simulation_variable_name']
            clearname = row['Name']

            # Create column names with suffixes
            sensor_col_with_suffix = f"{clearname}_real"
            sim_col_with_suffix = f"{clearname}_sim"

            # Ensure both columns exist in their respective DataFrames
            if sensor_col_with_suffix not in self.sensor_data.columns or sim_col_with_suffix not in self.simulation_data.columns:
                print(f"Skipping '{clearname}' as one of the columns is missing.")
                continue

            # Find the global min and max across both columns
            min_val = min(self.sensor_data[sensor_col_with_suffix].min(), self.simulation_data[sim_col_with_suffix].min())
            max_val = max(self.sensor_data[sensor_col_with_suffix].max(), self.simulation_data[sim_col_with_suffix].max())

            if max_val == min_val:
                print(f"Warning: All values for '{clearname}' are the same. Setting to 0.")
                self.sensor_data[sensor_col_with_suffix] = 0.0
                self.simulation_data[sim_col_with_suffix] = 0.0
            else:
                self.sensor_data[sensor_col_with_suffix] = (self.sensor_data[sensor_col_with_suffix] - min_val) / (max_val - min_val)
                self.simulation_data[sim_col_with_suffix] = (self.simulation_data[sim_col_with_suffix] - min_val) / (max_val - min_val)

        print("Data scaling completed.")
        return self.sensor_data, self.simulation_data


    
    def calculate_mae_smape(self) -> Tuple[pd.DataFrame, float, float]:
        """
        Calculate MAE and SMAPE for each variable, including detailed per-timestamp results.
    
        Returns:
            per_channel_mae_smape_df: DataFrame with MAE and SMAPE (%) per channel.
            total_mae: Overall MAE across all channels.
            total_smape: Overall SMAPE (%) across all channels.
            mae_df: DataFrame with absolute error for each timestamp and channel.
            smape_df: DataFrame with sMAPE (%) for each timestamp and channel.
        """
        mae = {}
        smape = {}
        mae_df = pd.DataFrame(index=self.sensor_data.index)
        smape_df = pd.DataFrame(index=self.sensor_data.index)

        
        exclude_columns = [col for col in self.sensor_data.columns if col.replace("_real", "") not in self.mapping_df['Name'].values]
        for col in self.sensor_data.columns:
            # Skip columns not present in simulation data or explicitly excluded
            if col in exclude_columns:
                continue
            
            # Derive the clear name without suffixes
            clearname = col.rsplit('_', 1)[0]  # Remove the suffix (_real or _sim)
            sensor_col_with_suffix = f"{clearname}_real"
            sim_col_with_suffix = f"{clearname}_sim"
            
            # Ensure both columns exist in their respective DataFrames
            if sensor_col_with_suffix not in self.sensor_data.columns or sim_col_with_suffix not in self.simulation_data.columns:
                print(f"Skipping column '{col}' as one of the columns is missing in the data.")
                continue
            
            # Retrieve the actual sensor and predicted simulation data
            actual = self.sensor_data[sensor_col_with_suffix]
            predicted = self.simulation_data[sim_col_with_suffix]
            
            # Calculate absolute error for MAE
            abs_error = np.abs(actual - predicted) # used for df
            mae[col] = abs_error.mean()
            mae_df[col] = abs_error

            # Calculate sMAPE for each timestamp
            smape_per_timestep = 2 * abs_error / (np.abs(actual) + np.abs(predicted) + 1e-8)
            smape[col] = smape_per_timestep.mean() * 100  # Convert to percentage
            smape_df[col] = smape_per_timestep * 100  # Convert to percentage for detailed output

        per_channel_mae_smape_df = pd.DataFrame({'MAE': mae, 'SMAPE (%)': smape})
        total_mae = per_channel_mae_smape_df['MAE'].mean()
        total_smape = per_channel_mae_smape_df['SMAPE (%)'].mean()
        print("MAE and SMAPE calculation completed.")
        return mae_df, smape_df, per_channel_mae_smape_df, total_mae, total_smape

    def detect_time_shift(self, max_lag: int = 10) -> int:
        """
        Detect the optimal time shift using cross-correlation.
        """
        real = self.sensor_data.iloc[:, 0].values
        sim = self.simulation_data.iloc[:, 0].values

        cross_corr = [np.corrcoef(real[:-lag], sim[lag:])[0, 1] for lag in range(1, max_lag)]
        optimal_shift = np.argmax(cross_corr) + 1
        print(f"Optimal time shift detected: {optimal_shift} steps.")
        return optimal_shift

