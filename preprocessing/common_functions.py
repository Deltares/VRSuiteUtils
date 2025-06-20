import configparser
import re
import os

import logging
import pandas as pd


def read_csv(file_path, **kwargs):
    """ Reads a CSV file with automatic line separator detection."""
    df = pd.read_csv(file_path, sep=None, engine='python', **kwargs)
    df.columns = df.columns.str.encode('ascii', 'ignore').str.decode('ascii') # only allow ascii characters in column names

    if len(df.columns) == 1: 
        log_and_raise_error(f"Fout bij inlezen van CSV-bestand {file_path}: bij inlezen is slechts 1 kolom gevonden. Controleer de scheidingstekens.", ValueError) 
    
    if 'doorsnede' in df.columns: #drop empty rows in doorsnede column
        df = df.dropna(subset=['doorsnede'])
    
    return df

def log_and_raise_error(message, error_type=Exception):
    """
    Logs an error message and raises an exception of the specified type.
    
    :param message: The error message to log and raise.
    :param error_type: The type of exception to raise (default is Exception).
    """
    logging.error(f"{error_type}: {message}")  
    raise error_type(message)

def check_string_in_list(str, list_vals):
    for item in list_vals:
        if item in str:
            return True
    return False

def read_config_file(file_path, mandatory_parameters):
    config = configparser.ConfigParser()
    # Change working dir to the folder of the configuration file
    os.chdir(os.path.dirname(file_path))

    # Read the configuration file line by line
    with open(file_path, 'r') as f:
        for line in f:
            # Use regular expression to match parameter, value, and comment
            match = re.match(r"^\s*([^#]+?)\s*=\s*([^#]+?)\s*(?:#.*)?$", line)
            if match:
                param, value = map(str.strip, match.groups())
                config['DEFAULT'][param] = value

    # Check if mandatory parameters are present
    for param in mandatory_parameters:
        if param not in config['DEFAULT']:
            raise ValueError(f"'{param}' is missing in the configuration file.")

    return config['DEFAULT']