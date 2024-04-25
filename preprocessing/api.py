from preprocessing.workflows.generate_vakindeling_workflow import vakindeling_main
from preprocessing.workflows.hydraring_overflow_workflow import overflow_main
from preprocessing.workflows.hydraring_waterlevel_workflow import waterlevel_main
from preprocessing.common_functions import read_config_file
from pathlib import Path
import os

def generate_vakindeling_shape(config_file: str, results_folder: Path = None):
    """
    Generate the vakindeling shapefile based on the input vakindeling csv file.
    The vakindeling shapefile will be saved in the output folder specified in the configuration file.

    Parameters
    ----------
    config_file : str
        Path to the configuration file.
    results_folder : Path, optional
        Used for testing: Path to the folder where the results will be saved. If None, the results will be saved in the same folder as the configuration file.

    Returns
    -------
    None
    """

    mandatory_parameters = ['traject_id', 'vakindeling_csv', 'output_map_vakindeling']

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    traject_id = parameters['traject_id']
    vakindeling_csv = parameters['vakindeling_csv']

    if results_folder is None:
        output_folder_vakindeling = Path(parameters['output_map_vakindeling'])
    else: # used for testing
        output_folder_vakindeling = results_folder.joinpath(parameters['output_map_vakindeling'])
        # Recreate the output folder
        if output_folder_vakindeling.exists():
            output_folder_vakindeling.rmdir()
        output_folder_vakindeling.mkdir(parents=True, exist_ok=True)
    
    traject_shape = parameters.getboolean('traject_shapefile', fallback=False)  # set default value to False if not present
    flip = parameters.getboolean('flip_traject', fallback=False)  # set default value to False if not present

    # print the parameters
    print("The following parameters are read from the configuration file:")
    print(f"traject_id: {traject_id}")
    print(f"vakindeling_csv: {vakindeling_csv}")
    print(f"output_folder_vakindeling: {output_folder_vakindeling}")
    print(f"traject_shape: {traject_shape}")
    print(f"flip_traject: {flip}")

    # run the vakindeling workflow
    vakindeling_main(
        traject_id,
        vakindeling_csv,
        Path(output_folder_vakindeling),
        traject_shape,
        flip,
    )

def generate_and_evaluate_waterlevel_computations(config_file: str, results_folder: Path = None):
    mandatory_parameters = ['hr_input_csv', 'database_path_HR_current', 'database_path_HR_future', 'output_map_waterstand']

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    file_path = parameters['hr_input_csv']
    database_path_current = Path(parameters['database_path_HR_current'])
    database_path_future = Path(parameters['database_path_HR_future'])
    
    if results_folder is None:
        output_path = Path(parameters['output_map_waterstand'])
    else: # used for testing
        output_path = results_folder.joinpath(parameters['output_map_waterstand'])
        # Recreate the output folder
        if output_path.exists():
            output_path.rmdir()
        output_path.mkdir(parents=True, exist_ok=True)


    # print the parameters
    print("The following parameters are read from the configuration file:")
    print(f"file_path: {file_path}")
    print(f"database_path_current: {database_path_current}")
    print(f"database_path_future: {database_path_future}")
    print(f"output_path: {output_path}")

    # run the water level computations
    waterlevel_main(
        Path(file_path),
        [database_path_current, database_path_future],
        Path(os.path.dirname(os.path.realpath(__file__))).joinpath('externals', 'HydraRing-23.1.1'),
        Path(output_path),
    )

def generate_and_evaluate_overflow_computations(config_file: str, results_folder: Path = None):
    """
    Generate the overflow computations based on the input HR input csv file.
    The results will be saved in the output folder specified in the configuration file.

    Parameters
    ----------
    config_file : str
        Path to the configuration file.
    results_folder : Path, optional 
        Used for testing: Path to the folder where the results will be saved. If None, the results will be saved in the same folder as the configuration file.

    Returns
    -------
    None
    """
    
    mandatory_parameters = ['hr_input_csv', 'database_path_HR_current', 'database_path_HR_future', 'hr_profielen_dir', 'output_map_overslag']

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    file_path = parameters['hr_input_csv']
    database_path_current = Path(parameters['database_path_HR_current'])
    database_path_future = Path(parameters['database_path_HR_future'])
    
    profielen_dir = parameters['hr_profielen_dir']
    output_path = parameters['output_map_overslag']
    if results_folder is None:
        output_path = Path(parameters['output_map_overslag'])
    else: # used for testing
        output_path = results_folder.joinpath(parameters['output_map_overslag'])
        # Recreate the output folder
        if output_path.exists():
            output_path.rmdir()
        output_path.mkdir(parents=True, exist_ok=True)
    # print the parameters
    print("The following parameters are read from the configuration file:")
    print(f"file_path: {file_path}")
    print(f"database_path_current: {database_path_current}")
    print(f"database_path_future: {database_path_future}")
    print(f"profielen_dir: {profielen_dir}")
    print(f"output_path: {output_path}")

    # run the overflow computations
    overflow_main(
        Path(file_path),
        [database_path_current, database_path_future],
        Path(profielen_dir),
        Path(os.path.dirname(os.path.realpath(__file__))).joinpath('externals', 'HydraRing-23.1.1'),
        Path(output_path),
    )