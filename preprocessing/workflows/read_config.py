
import configparser
from pathlib import Path
import re

def read_config_file(file_path, mandatory_parameters):
    config = configparser.ConfigParser()

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


mandatory_parameters = ['traject_id', 'vakindeling_csv', 'output_map_vakindeling']
config_file = Path(r"c:/vrm_test/database_7_2/input.txt")
try:
    parameters = read_config_file(config_file, mandatory_parameters)
except ValueError as e:
    print(f"Error reading configuration: {e}")

# print each parameter and its value
for param, value in parameters.items():
    print(f"{param}: {value}")
