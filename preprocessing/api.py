from preprocessing.step0_initialize_project.create_project_structure import create_project_structure
from preprocessing.workflows.generate_vakindeling_workflow import vakindeling_main

from preprocessing.workflows.hydraring_overflow_workflow import overflow_main
from preprocessing.workflows.hydraring_waterlevel_workflow import waterlevel_main

from preprocessing.workflows.bekleding_qvariant_workflow import qvariant_main
from preprocessing.workflows.bekleding_gebu_zst_workflow import gebu_zst_main

from preprocessing.workflows.get_profiles_workflow import main_traject_profiles
from preprocessing.workflows.select_profiles_workflow import main_profiel_selectie
from preprocessing.workflows.teenlijn_workflow import main_teenlijn
from preprocessing.workflows.derive_buildings_workflow import main_bebouwing

from preprocessing.workflows.write_database_workflow import write_database_main

from preprocessing.common_functions import read_config_file
from pathlib import Path
import os


def create_project(project_folder: Path, traject_id: str):
    """
    Generates all the necessary files for a project based on a given folder directory and traject_id.

    Parameters
    ----------
    project_folder : Path, required
        The folder where the project will be created. If None, the project will not be created.
    traject_id : str, required

    Returns
    -------
    None
    """

    project_folder = Path(project_folder)

    # Check if there is not already a project_folder containing files
    if project_folder.exists():
        raise ValueError(f"Project folder bestaat al: {project_folder}. Kies een andere project folder.")

    traject_id = traject_id

    print(f"\Aanmaken project in folder: {project_folder}")
    print(f"Dijktraject: {traject_id}")

    create_project_structure(project_folder, traject_id)


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
    print("De volgende parameters zijn gelezen uit het configuratiebestand:")
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
    print("De volgende parameters zijn gelezen uit het configuratiebestand:")
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
    print("De volgende parameters zijn gelezen uit het configuratiebestand:")
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

def run_bekleding_qvariant(config_file: str, results_folder: Path = None):
    mandatory_parameters = ['traject_id',
                            'bekleding_input_csv',
                            'database_path_HR_current',
                            'database_path_HR_future',
                            'output_map_waterstand',
                            'hr_profielen_dir',
                            'output_map_bekleding']

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    traject_id = parameters['traject_id']
    input_csv = parameters['bekleding_input_csv']
    database_path_current = parameters['database_path_HR_current']
    database_path_future = parameters['database_path_HR_future']
    waterlevel_path = parameters['output_map_waterstand']
    profielen_path = parameters['hr_profielen_dir']

    if results_folder is None:
        output_path = Path(parameters['output_map_bekleding'])
        paths_to_databases = [Path(database_path_current), Path(database_path_future)]
    else: # used for testing
        paths_to_databases = [Path(database_path_current)]
        output_path = results_folder.joinpath(parameters['output_map_bekleding'])
        # Recreate the output folder
        if output_path.exists():
            output_path.rmdir()
        output_path.mkdir(parents=True, exist_ok=True)

    # print the parameters
    print("De volgende parameters zijn gelezen uit het configuratiebestand:")
    print(f"traject_id: {traject_id}")
    print(f"bekleding_input_csv: {input_csv}")
    print(f"database_path_current: {database_path_current}")
    print(f"database_path_future: {database_path_future}")
    print(f"output_map_waterstand: {waterlevel_path}")
    print(f"hr_profielen_dir: {profielen_path}")
    print(f"output_map_bekleding: {output_path}")

    # run the bekleding_qvariant workflow
    qvariant_main(
        traject_id,
        Path(input_csv),
        paths_to_databases,
        Path(waterlevel_path),
        Path(profielen_path),
        Path(os.path.dirname(os.path.realpath(__file__))).joinpath('externals', 'HydraRing-23.1.1'),
        Path(output_path),
    )

def run_gebu_zst(config_file: str, results_folder: Path = None):
    mandatory_parameters = ['traject_id', 'bekleding_input_csv', 'steentoets_map', 'hr_profielen_dir', 'output_map_bekleding']

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    traject_id = parameters['traject_id']
    input_csv = parameters['bekleding_input_csv']
    steentoets_path = parameters['steentoets_map']
    profielen_path = parameters['hr_profielen_dir']
    output_path = parameters['output_map_bekleding']
    if 'versterking_bekleding' in parameters:
        versterking_bekleding = parameters['versterking_bekleding']
    else:
        versterking_bekleding = 'uitbreiden'

    if results_folder is None:
        output_path_qvar = Path(parameters['output_map_bekleding'])
        output_path_results = Path(parameters['output_map_bekleding'])
    else: # used for testing
        output_path_results = results_folder.joinpath(parameters['output_map_bekleding'])
        # Recreate the output folder
        if output_path_results.exists():
            output_path_results.rmdir()
        output_path_results.mkdir(parents=True, exist_ok=True)
        #get Q-var from testdata
        output_path_qvar = Path(parameters['output_map_bekleding'])

    # print the parameters
    print("De volgende parameters zijn gelezen uit het configuratiebestand:")
    print(f"traject_id: {traject_id}")
    print(f"bekleding_input_csv: {input_csv}")
    print(f"steentoets_map: {steentoets_path}")
    print(f"hr_profielen_dir: {profielen_path}")
    print(f"output_map_bekleding: {output_path}")
    print(f"versterking_bekleding: {versterking_bekleding}")


    # run the bekleding_gebu_zst workflow
    gebu_zst_main(
        traject_id,
        Path(input_csv),
        Path(steentoets_path),
        Path(profielen_path),
        Path(os.path.dirname(os.path.realpath(__file__))).joinpath('externals', 'DiKErnel'),
        Path(output_path_qvar),
        Path(output_path_results),
        versterking_bekleding,
    )
    
def get_characteristic_profiles_for_traject(config_file: str, results_folder: Path = None):   
    mandatory_parameters = ['traject_id', 'output_map_profielen']

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    traject_id = parameters['traject_id']
    if results_folder is None:
        output_path = Path(parameters['output_map_profielen'])
    else: # used for testing
        output_path = results_folder.joinpath(parameters['output_map_profielen'])
        # Recreate the output folder
        if output_path.exists():
            output_path.rmdir()
        output_path.mkdir(parents=True, exist_ok=True)
    
    dx = parameters.getint('dx', fallback=25)  # set default value to 25 if not present
    voorland_lengte = parameters.getint('voorland_lengte', fallback=50)  # set default value to 50 if not present
    achterland_lengte = parameters.getint('achterland_lengte', fallback=75)  # set default value to 75 if not present
    traject_shape = parameters.getboolean('traject_shape', fallback=False)  # set default value to False if not present
    flip_traject = parameters.getboolean('flip_traject', fallback=False)  # set default value to False if not present
    flip_waterkant = parameters.getboolean('flip_waterkant', fallback=False)  # set default value to False if not present

    # print the parameters
    print("\nDe volgende parameters zijn gelezen uit het configuratiebestand:\n")
    print(f"traject_id: {traject_id}")
    print(f"output_path: {output_path.__str__}")
    print(f"dx: {dx}")
    print(f"voorland_lengte: {voorland_lengte}")
    print(f"achterland_lengte: {achterland_lengte}")
    print(f"traject_shape: {traject_shape}")
    print(f"flip_traject: {flip_traject}")
    print(f"flip_waterkant: {flip_waterkant}")

    # run the get_profiles_workflow
    main_traject_profiles(
        traject_id,
        output_path,
        dx,
        voorland_lengte,
        achterland_lengte,
        traject_shape,
        flip_traject,
        flip_waterkant,
    )

def selecteer_profiel(config_file: str, results_folder: Path = None):
    mandatory_parameters = ['vakindeling_geojson',
                            'output_map_ahn_profielen',
                            'karakteristieke_profielen_map',
                            'profiel_info_csv',
                            'output_map_representatieve_profielen']
    
    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    vakindeling_geojson = parameters['vakindeling_geojson']
    ahn_profielen = parameters['output_map_ahn_profielen']
    karakteristieke_profielen = parameters['karakteristieke_profielen_map']
    profiel_info_csv = parameters['profiel_info_csv']
    if results_folder is None:
        output_path = Path(parameters['output_map_representatieve_profielen'])
    else: # used for testing
        output_path = results_folder.joinpath(parameters['output_map_representatieve_profielen'])
        # Recreate the output folder
        if output_path.exists():
            output_path.rmdir()
        output_path.mkdir(parents=True, exist_ok=True)
    invoerbestand = parameters.get('ingevoerde_profielen', fallback=False)

    # print the parameters
    print("\nDe volgende parameters zijn gelezen uit het configuratiebestand:\n")
    print(f"vakindeling_geojson: {vakindeling_geojson}")
    print(f"ahn_profielen: {ahn_profielen}")
    print(f"karakteristieke_profielen: {karakteristieke_profielen}")
    print(f"profiel_info_csv: {profiel_info_csv}")
    print(f"uitvoer_map: {output_path}")
    print(f"invoerbestand: {invoerbestand}")

    # run the select_profiles_workflow
    main_profiel_selectie(
        Path(vakindeling_geojson),
        Path(ahn_profielen),
        Path(karakteristieke_profielen),
        Path(profiel_info_csv),
        Path(output_path),
        invoerbestand,
        "minimum"
    )

def obtain_inner_toe_line(config_file: str, results_folder: Path = None):
    mandatory_parameters = ['karakteristieke_profielen_map', 'profiel_info_csv', 'output_map_teenlijn']

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    karakteristieke_profielen_map = parameters['karakteristieke_profielen_map']
    profiel_info_csv = parameters['profiel_info_csv']
    if results_folder is None:
        output_path = Path(parameters['output_map_teenlijn'])
    else: # used for testing
        output_path = results_folder.joinpath(parameters['output_map_teenlijn'])
        # Recreate the output folder
        if output_path.exists():
            output_path.rmdir()
        output_path.mkdir(parents=True, exist_ok=True)

    # print the parameters
    print("\nDe volgende parameters zijn gelezen uit het configuratiebestand:\n")
    print(f"karakteristieke_profielen_map: {karakteristieke_profielen_map}")
    print(f"profiel_info_csv: {profiel_info_csv}")
    print(f"teenlijn_uitvoer: {output_path}")

    # run the teenlijn_workflow
    main_teenlijn(
        Path(karakteristieke_profielen_map),
        Path(profiel_info_csv),
        Path(output_path),
    )

def count_buildings(config_file: str, results_folder: Path = None):
    mandatory_parameters = ['traject_id',
                            'teenlijn_geojson',
                            'vakindeling_geojson',
                            'output_map_bebouwing',
                            'bag_gebouwen_geopackage']

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    traject_id = parameters['traject_id']
    teenlijn_geojson = parameters['teenlijn_geojson']
    vakindeling_geojson = parameters['vakindeling_geojson']
    gebouwen_geopackage = parameters['bag_gebouwen_geopackage']
    flip_waterkant = parameters.getboolean('flip_waterkant', fallback=False)
    
    if results_folder is None:
        output_path = Path(parameters['output_map_bebouwing'])
    else: # used for testing
        output_path = results_folder.joinpath(parameters['output_map_bebouwing'])
        # Recreate the output folder
        if output_path.exists():
            output_path.rmdir()
        output_path.mkdir(parents=True, exist_ok=True)

    if flip_waterkant == True:
        richting = -1
    else:
        richting = 1

    # print the parameters
    print("\nDe volgende parameters zijn gelezen uit het configuratiebestand:\n")
    print(f"traject_id: {traject_id}")
    print(f"teenlijn_geojson: {teenlijn_geojson}")
    print(f"vakindeling_geojson: {vakindeling_geojson}")
    print(f"uitvoer_map: {output_path}")
    print(f"gebouwen_geopackage: {gebouwen_geopackage}")
    print(f"flip_waterkant: {flip_waterkant}")

    # Run the derive_buildings_workflow
    main_bebouwing(
        traject_id,
        Path(teenlijn_geojson),
        Path(vakindeling_geojson),
        Path(output_path),
        Path(gebouwen_geopackage),
        richting
    )

def create_database(config_file: str, results_folder: Path = None):
    mandatory_parameters = ['traject_id',
                            'vakindeling_geojson',
                            'karakteristieke_profielen_csv',
                            'gebouwen_csv',
                            'output_map_database',
                            'vrtool_database_naam',
                            'hr_input_csv',
                            'output_map_waterstand',
                            'output_map_overslag']

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    traject_id = parameters['traject_id']
    vakindeling_geojson = parameters['vakindeling_geojson']
    characteristic_profile_csv = parameters['karakteristieke_profielen_csv']
    building_csv_path = parameters['gebouwen_csv']
    output_db_name = parameters['vrtool_database_naam']
    hr_input_csv = parameters['hr_input_csv']
    waterlevel_results_path = parameters['output_map_waterstand']
    overflow_results_path = parameters['output_map_overslag']
    piping_path = parameters.get('piping_input_csv', fallback=False)
    stability_path = parameters.get('stabiliteit_input_csv', fallback=False)
    revetment_path = parameters.get('output_map_bekleding', fallback=False)
    if len(os.listdir(revetment_path))==0: #no results present, so ignore revetment
        revetment_path = None

    if results_folder is None:
        output_path = Path(parameters['output_map_database'])
    else: # used for testing
        output_path = results_folder.joinpath(parameters['output_map_database'])
        # Recreate the output folder
        if output_path.exists():
            output_path.rmdir()
        output_path.mkdir(parents=True, exist_ok=True)

    # print the parameters
    print("\nDe volgende parameters zijn gelezen uit het configuratiebestand:\n")
    print(f"traject_id: {traject_id}")
    print(f"vakindeling_geojson: {vakindeling_geojson}")
    print(f"characteristic_profile_csv: {characteristic_profile_csv}")
    print(f"building_csv_path: {building_csv_path}")
    print(f"output_dir: {output_path}")
    print(f"output_db_name: {output_db_name}")
    print(f"hr_input_csv: {hr_input_csv}")
    print(f"waterlevel_results_path: {waterlevel_results_path}")
    print(f"overflow_results_path: {overflow_results_path}")
    print(f"piping_path: {piping_path}")
    print(f"stability_path: {stability_path}")
    print(f"revetment_path: {revetment_path}")

    # run the write_database_workflow
    write_database_main(
        traject_id,
        Path(vakindeling_geojson),
        Path(characteristic_profile_csv),
        Path(building_csv_path),
        Path(output_path),
        output_db_name,
        Path(hr_input_csv),
        Path(waterlevel_results_path),
        Path(overflow_results_path),
        piping_path,
        stability_path,
        revetment_path
    )

if __name__ == '__main__':
    #Use this structure to test api calls locally

    config_file = Path(r"c:\VRM\20240618_bekleding_renske\preprocessor.config")
    generate_and_evaluate_waterlevel_computations(str(config_file))