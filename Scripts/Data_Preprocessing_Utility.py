import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler
import plotly.graph_objects as go
from scipy.signal import medfilt

import Config
import sensor_simvar_mapping



def load_and_label_data(filepath, mapping_df):
    # Load the data
    dataframe = pd.read_csv(filepath)
    
    time_columns = ['time', 'Timestamps', 'Server Time', 'Session Time Stamps']
    time_columns = list(set(time_columns) & set(dataframe.columns))
    
    data_columns = list(set(dataframe.columns) - set(time_columns))
    
    analogue_sensors_column = mapping_df[
        (mapping_df['Role'] == 'Sensor') &
        (mapping_df['Binary_or_Analogue'] == 'analogue') &
        (mapping_df['Sensor_OPCUA_Node_ID'].isin(dataframe.columns))
    ]['Sensor_OPCUA_Node_ID'].tolist()

    analogue_level_sensors_column = mapping_df[
        (mapping_df['Role'] == 'Sensor') &
        (mapping_df['Binary_or_Analogue'] == 'analogue') &
        (mapping_df['Type_of_Sensor_or_Actuator'] == 'level') &
        (mapping_df['Sensor_OPCUA_Node_ID'].isin(dataframe.columns)) 
    ]['Sensor_OPCUA_Node_ID'].tolist()
        
    binary_sensors_column = mapping_df[
        (mapping_df['Role'] == 'Sensor') &
        (mapping_df['Binary_or_Analogue'] == 'binary') &
        (mapping_df['Sensor_OPCUA_Node_ID'].isin(dataframe.columns))
    ]['Sensor_OPCUA_Node_ID'].tolist()

    actuators_column = mapping_df[
        (mapping_df['Role'] == 'Actuator') &
        (mapping_df['Sensor_OPCUA_Node_ID'].isin(dataframe.columns))
    ]['Sensor_OPCUA_Node_ID'].tolist()
    
    return dataframe, time_columns, data_columns, analogue_sensors_column, analogue_level_sensors_column, binary_sensors_column, actuators_column



def reduce_noise(dataframe, columns_to_smooth, window_size, threshold):
    # Create a copy of the dataframe to avoid modifying the original dataframe
    smoothed_dataframe = dataframe.copy()
    
    # Iterate over the columns to smooth
    for column in columns_to_smooth:
        # Apply a rolling mean to smooth the values in the column
        #smoothed_dataframe[column] = dataframe[column].rolling(window_size, min_periods=1, center=True).mean()
        # Calculate the rolling mean and the rolling standard deviation for each value in the column
        rolling_mean = dataframe[column].rolling(window=window_size, center=True).mean()
        rolling_std = dataframe[column].rolling(window=window_size, center=True).std()
        
        # Calculate the z-score for each value in the column
        z_scores = np.abs((dataframe[column] - rolling_mean) / rolling_std)
        
        # Replace the values that are above the threshold with the rolling mean
        smoothed_dataframe[column] = dataframe[column].mask(z_scores > threshold, rolling_mean)
        
    
    return smoothed_dataframe



def flatten_outliers_in_dataframe(df, columns, kernel_size=5, threshold=3):
    """
    Flatten outliers in specified columns of a DataFrame characterized by sudden drops or spikes using a median filter.

    Parameters:
    df (pd.DataFrame): The input DataFrame.
    columns (list of str): The columns to process.
    kernel_size (int): The size of the kernel for the median filter. This parameter specifies the size of the window used for the median filter. 
    The median filter smooths the time series by replacing each point with the median of the points in a window centered around it.
    It should be a positive odd integer (e.g., 3, 5, 7, etc.). 
    The kernel size must be odd to ensure that the window is symmetric around the center point.
    threshold (float): The threshold for detecting outliers.
    This parameter sets the sensitivity for detecting outliers. 
    An outlier is identified if the absolute difference between the original time series and the median-filtered series exceeds this threshold value.

    Returns:
    pd.DataFrame: The DataFrame with flattened outliers in specified columns.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("df must be a pandas DataFrame")
    if not isinstance(columns, list) or not all(isinstance(col, str) for col in columns):
        raise ValueError("columns must be a list of strings")
    if not isinstance(kernel_size, int) or kernel_size <= 0:
        raise ValueError("kernel_size must be a positive integer")
    if not isinstance(threshold, (int, float)) or threshold <= 0:
        raise ValueError("threshold must be a positive number")
    
    df_copy = df.copy()
    
    for column in columns:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        # Convert column to numpy array
        time_series = df[column].values
        
        # Apply median filter to the time series
        filtered_series = medfilt(time_series, kernel_size=kernel_size)
        
        # Detect outliers
        difference = np.abs(time_series - filtered_series)
        outliers = difference > threshold
        
        # Replace outliers with the median filtered values
        denoised_series = np.copy(time_series)
        denoised_series[outliers] = filtered_series[outliers]
        
        # Update the DataFrame
        df_copy[column] = denoised_series
    
    return df_copy


def scale_dataframe(df, feature_range=(-1, 1)):
    """
    Scale all columns in a DataFrame to a specified range.

    Parameters:
    df (pd.DataFrame): The input DataFrame.
    feature_range (tuple): Desired range of transformed data (default is (-1, 1)).

    Returns:
    pd.DataFrame: The DataFrame with scaled values.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("df must be a pandas DataFrame")
    if not isinstance(feature_range, tuple) or len(feature_range) != 2:
        raise ValueError("feature_range must be a tuple of two elements")

    scaler = MinMaxScaler(feature_range=feature_range)
    scaled_values = scaler.fit_transform(df.values)
    scaled_df = pd.DataFrame(scaled_values, columns=df.columns)

    return scaled_df


def plot_data(dataframe, time_column, title='Sensor Data Over Time', x_title='Time', y_title='Sensor Value'):
    # Plot the data
    fig = go.Figure()
    for column in dataframe.columns:
        if column != time_column:
            fig.add_trace(go.Scatter(x=dataframe[time_column], y=dataframe[column], mode='lines', name=column))
    
    fig.update_layout(height=800, title=title, xaxis_title= x_title, yaxis_title=y_title)
    fig.show()  
        
    
def main():
    
    #load mapping information
    mapping_df = sensor_simvar_mapping.create_mapping_table()
    
    # Load the data
    dataframe, time_columns, data_columns, analogue_sensors_columns, analogue_level_sensors_columns, binary_sensors_column, actuators_column = load_and_label_data(Config.path_to_current_dataset, mapping_df)
    
    dataframe = dataframe.drop(columns='Server Time')
    #plot analogue sensor data before noise reduction
    plot_data(dataframe, 'Session Time Stamps', title='Sensor Data Before Noise Reduction')
    
    # Remove outliers in Level sensor data
    dataframe = flatten_outliers_in_dataframe(dataframe, analogue_level_sensors_columns, kernel_size=5, threshold=3)
    plot_data(dataframe, 'Session Time Stamps', title='Sensor Data After Flattening Outliers in Level Sensors')
    # Reduce noise in the data
    dataframe = reduce_noise(dataframe, analogue_sensors_columns, window_size=10, threshold=1.5)
    
    #plot data after noise reduction
    plot_data(dataframe, 'Session Time Stamps', title='Sensor Data After Noise Reduction')
    
    # Scale the data
    scaled_dataframe = scale_dataframe(dataframe)
    
    # Plot the scaled data
    plot_data(scaled_dataframe, 'Session Time Stamps', title='Scaled Sensor Data')
    
    
    
if __name__ == '__main__':
    main()