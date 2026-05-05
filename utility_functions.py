from datetime import datetime
import pandas as pd
from pandas import Timedelta


def clean_time(data, name_of_time_column, time_interval='100ms'):
    """
    Change timestamps to ISO-Format and make them equidistant by resampling.
    :param data: The DataFrame containing the time column.
    :param time_interval: The desired fixed time interval for resampling (default is 100ms).
    """
    # Change time from interval since start to ISO-Timestamp
    starttime = datetime.now()
    data[name_of_time_column] = [starttime + Timedelta(seconds=x) for x in data.time]

    data.columns = [x if 'der(' not in x else x.replace('(', '_').replace(')', '') for x in data.columns]

    # Set the time column as the DataFrame index
    data.set_index(name_of_time_column, inplace=True)

    # Resample the DataFrame to the desired time interval and fill missing values forward
    data_resampled = data.resample(time_interval).first().ffill()

    # Reset the index to keep the time column as a regular column
    data_resampled.reset_index(inplace=True)

    return data_resampled
