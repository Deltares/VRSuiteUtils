import configparser
import re
import os


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