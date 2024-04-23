from preprocessing.workflows.generate_vakindeling_workflow import vakindeling_main
from preprocessing.common_functions import read_config_file
from pathlib import Path

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