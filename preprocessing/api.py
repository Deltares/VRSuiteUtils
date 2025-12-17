from preprocessing.step0_initialize_project.create_project_structure import create_project_structure
from preprocessing.workflows.generate_vakindeling_workflow import vakindeling_main

from preprocessing.workflows.hydraring_overflow_workflow import overflow_main
from preprocessing.workflows.hydraring_waterlevel_workflow import waterlevel_main
from preprocessing.workflows.hydranl_overflow_workflow import overflow_hydranl_main
from preprocessing.workflows.hydranl_waterlevel_workflow import waterlevel_hydranl_main

from preprocessing.workflows.bekleding_qvariant_workflow import qvariant_main
from preprocessing.workflows.bekleding_gebu_zst_workflow import gebu_zst_main

from preprocessing.workflows.get_profiles_workflow import main_traject_profiles
from preprocessing.workflows.select_profiles_workflow import main_profiel_selectie
from preprocessing.workflows.teenlijn_workflow import main_teenlijn
from preprocessing.workflows.derive_buildings_workflow import main_bebouwing

from preprocessing.workflows.write_database_workflow import write_database_main

from preprocessing.common_functions import read_config_file
from preprocessing import hydraring_bin_dir, dikernel_bin_dir
from pathlib import Path
import os
from vrtool.vrtool_logger import VrToolLogger
import logging

from datetime import datetime
import shutil

def _initialize_log_file(log_dir: Path | None, workflow_name: str):
    # Logging dir.
    if log_dir is None:
        log_dir = Path.cwd()

    # Define logging filename and initialize handler
    _current_date = datetime.today().strftime("%Y%m%d_%H%M")
    _log_file = Path(log_dir).joinpath(f"{workflow_name}.log")
    VrToolLogger.init_file_handler(_log_file, logging_level=logging.INFO)
    VrToolLogger.init_console_handler(logging_level=logging.INFO)
    logging.info(f"Start logging {workflow_name} vanuit %s", str(_log_file))

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

    print(f"Aanmaken project in folder: {project_folder}")
    print(f"Dijktraject: {traject_id}")

    create_project_structure(project_folder, traject_id)


def generate_vakindeling_shape(config_file: Path, results_folder: Path = None):
    """
    Generate the vakindeling shapefile based on the input vakindeling csv file.
    The vakindeling shapefile will be saved in the output folder specified in the configuration file.

    Parameters
    ----------
    config_file : Path
        Path to the configuration file.
    results_folder : Path, optional
        Used for testing: Path to the folder where the results will be saved. If None, the results will be saved in the same folder as the configuration file.

    Returns
    -------
    None
    """
    config_file = config_file if isinstance(config_file, Path) else Path(config_file)
    mandatory_parameters = ['traject_id', 'vakindeling_csv', 'output_map_vakindeling']

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    _parent_dir = config_file.parent
    traject_id = parameters['traject_id']
    vakindeling_csv = _parent_dir.joinpath(parameters['vakindeling_csv'])

    if results_folder is None:
        output_folder_vakindeling = _parent_dir.joinpath(parameters['output_map_vakindeling'])
    else: # used for testing
        output_folder_vakindeling = results_folder.joinpath(parameters['output_map_vakindeling'])
        # Recreate the output folder
        if output_folder_vakindeling.exists():
            output_folder_vakindeling.rmdir()
        output_folder_vakindeling.mkdir(parents=True, exist_ok=True)

    # get traject_shape from parameters. This is either a FALSE or none (or nothing filled in), or a pathname
    try: 
        traject_shape = parameters.getboolean('traject_shapefile', fallback=False)
    except:
        traject_shape = str(parameters['traject_shapefile'])
    flip = parameters.getboolean('flip_traject', fallback=False)  # set default value to False if not present

    #initialize log file
    _initialize_log_file(output_folder_vakindeling, "vakindeling")
    logging.info("Start logging vakindeling \n ")
    # print the parameters
    logging.info("De volgende parameters zijn gelezen uit het configuratiebestand:")
    logging.info(f" traject_id:                     {traject_id}")
    logging.info(f" vakindeling_csv:                {vakindeling_csv}")
    logging.info(f" output_folder_vakindeling:      {output_folder_vakindeling}")
    logging.info(f" traject_shape:                  {traject_shape}")
    logging.info(f" flip_traject:                   {flip} \n")

    # run the vakindeling workflow
    vakindeling_main(
        traject_id,
        vakindeling_csv,
        output_folder_vakindeling,
        traject_shape,
        flip,
    )

def generate_and_evaluate_waterlevel_computations(config_file: Path, results_folder: Path = None):
    mandatory_parameters = ['hr_input_csv', 'database_path_HR_current', 'database_path_HR_future', 'output_map_waterstand']
    config_file = config_file if isinstance(config_file, Path) else Path(config_file)

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    _parent_dir = config_file.parent
    file_path = _parent_dir.joinpath(parameters['hr_input_csv'])
    database_path_current = _parent_dir.joinpath(parameters['database_path_HR_current'])
    database_path_future = _parent_dir.joinpath(parameters['database_path_HR_future'])

    if results_folder is None:
        output_path = _parent_dir.joinpath(parameters['output_map_waterstand'])
    else: # used for testing
        output_path = results_folder.joinpath(parameters['output_map_waterstand'])
        # Recreate the output folder
        if output_path.exists():
            output_path.rmdir()
        output_path.mkdir(parents=True, exist_ok=True)

    _initialize_log_file(output_path, "waterstandsberekeningen")
    # print the parameters
    logging.info("De volgende parameters zijn gelezen uit het configuratiebestand:")
    logging.info(f" file_path:                  {file_path}")
    logging.info(f" database_path_current:      {database_path_current}")
    logging.info(f" database_path_future:       {database_path_future}")
    logging.info(f" output_path:                {output_path}\n")

    # run the water level computations
    waterlevel_main(
        file_path,
        [database_path_current, database_path_future],
        hydraring_bin_dir,
        output_path,
    )

def generate_and_evaluate_overflow_computations(config_file: Path, results_folder: Path = None):
    """
    Generate the overflow computations based on the input HR input csv file.
    The results will be saved in the output folder specified in the configuration file.

    Parameters
    ----------
    config_file : Path
        Path to the configuration file.
    results_folder : Path, optional 
        Used for testing: Path to the folder where the results will be saved. If None, the results will be saved in the same folder as the configuration file.

    Returns
    -------
    None
    """
    config_file = config_file if isinstance(config_file, Path) else Path(config_file)
    mandatory_parameters = ['hr_input_csv', 'database_path_HR_current', 'database_path_HR_future', 'hr_profielen_dir', 'output_map_overslag']

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    _parent_dir = config_file.parent
    file_path = _parent_dir.joinpath(parameters['hr_input_csv'])
    database_path_current = _parent_dir.joinpath(parameters['database_path_HR_current'])
    database_path_future = _parent_dir.joinpath(parameters['database_path_HR_future'])

    profielen_dir = _parent_dir.joinpath(parameters['hr_profielen_dir'])
    output_path = _parent_dir.joinpath(parameters['output_map_overslag'])
    if results_folder is None:
        output_path = _parent_dir.joinpath(parameters['output_map_overslag'])
    else: # used for testing
        output_path = results_folder.joinpath(parameters['output_map_overslag'])
        # Recreate the output folder
        if output_path.exists():
            output_path.rmdir()
        output_path.mkdir(parents=True, exist_ok=True)
    
    _initialize_log_file(output_path, "overslagberekeningen")
    logging.info("De volgende parameters zijn gelezen uit het configuratiebestand:")
    logging.info(f" file_path:               {file_path}")
    logging.info(f" database_path_current:   {database_path_current}")
    logging.info(f" database_path_future:    {database_path_future}")
    logging.info(f" profielen_dir:           {profielen_dir}")
    logging.info(f" output_path:             {output_path}\n")

    # run the overflow computations
    overflow_main(
        file_path,
        [database_path_current, database_path_future],
        profielen_dir,
        hydraring_bin_dir,
        output_path,
    )

def evaluate_hydranl_waterlevel_computations(config_file: Path, results_folder: Path = None, correct_uncer: bool = True, decim_type: str = 'decim_simple'):
    mandatory_parameters = ['hr_input_csv', 'hnl_results_dir', 'output_map_waterstand']
    config_file = config_file if isinstance(config_file, Path) else Path(config_file)

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    _parent_dir = config_file.parent
    file_path = _parent_dir.joinpath(parameters['hr_input_csv'])
    work_dir_path = _parent_dir.joinpath(parameters['hnl_results_dir'])

    if results_folder is None:
        output_path = _parent_dir.joinpath(parameters['output_map_waterstand'])
    else: # used for testing
        output_path = results_folder.joinpath(parameters['output_map_waterstand'])
        # Recreate the output folder
        if output_path.exists():
            output_path.rmdir()
        output_path.mkdir(parents=True, exist_ok=True)

    # print the parameters
    _initialize_log_file(output_path, "waterstandberekeningen_hydranl")
    logging.info("De volgende parameters zijn gelezen uit het configuratiebestand:")
    logging.info(f" file_path:          {file_path}")
    logging.info(f" work_dir_path:      {work_dir_path}")
    logging.info(f" output_path:        {output_path}\n")

    # run the water level computations
    waterlevel_hydranl_main(
        file_path,
        work_dir_path,
        output_path,
        correct_uncer,
        decim_type
    )

def evaluate_hydranl_overflow_computations(config_file: Path, results_folder: Path = None, correct_uncer: bool = True, decim_type: str = 'decim_simple', q_crit: int = 1):
    mandatory_parameters = ['hr_input_csv', 'hnl_results_dir', 'output_map_overslag']
    config_file = config_file if isinstance(config_file, Path) else Path(config_file)
    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    _parent_dir = config_file.parent
    file_path = _parent_dir.joinpath(parameters['hr_input_csv'])
    work_dir_path = _parent_dir.joinpath(parameters['hnl_results_dir'])

    if results_folder is None:
        output_path = _parent_dir.joinpath(parameters['output_map_overslag'])
    else: # used for testing
        output_path = results_folder.joinpath(parameters['output_map_overslag'])
        # Recreate the output folder
        if output_path.exists():
            output_path.rmdir()
        output_path.mkdir(parents=True, exist_ok=True)

    # print the parameters
    _initialize_log_file(output_path, "overslagberekeningen_hydranl")
    logging.info("De volgende parameters zijn gelezen uit het configuratiebestand:")
    logging.info(f" file_path:          {file_path}")
    logging.info(f" work_dir_path:      {work_dir_path}")
    logging.info(f" output_path:        {output_path}\n")

    # run the water level computations
    overflow_hydranl_main(
        file_path,
        work_dir_path,
        output_path,
        correct_uncer,
        decim_type,
        q_crit
    )

def run_bekleding_qvariant(config_file: Path, results_folder: Path = None):

    mandatory_parameters = ['traject_id',
                            'bekleding_input_csv',
                            'database_path_HR_current',
                            'database_path_HR_future',
                            'output_map_waterstand',
                            'hr_profielen_dir',
                            'output_map_bekleding']
    config_file = config_file if isinstance(config_file, Path) else Path(config_file)
    _parent_dir = config_file.parent
    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    traject_id = parameters['traject_id']
    input_csv = _parent_dir.joinpath(parameters['bekleding_input_csv'])
    database_path_current = _parent_dir.joinpath(parameters['database_path_HR_current'])
    database_path_future = _parent_dir.joinpath(parameters['database_path_HR_future'])
    waterlevel_path = _parent_dir.joinpath(parameters['output_map_waterstand'])
    profielen_path = _parent_dir.joinpath(parameters['hr_profielen_dir'])

    if results_folder is None:
        output_path = _parent_dir.joinpath(parameters['output_map_bekleding'])
        paths_to_databases = [database_path_current, database_path_future]
    else: # used for testing
        paths_to_databases = [database_path_current]
        output_path = results_folder.joinpath(parameters['output_map_bekleding'])
        # Recreate the output folder
        if output_path.exists():
            output_path.rmdir()
        output_path.mkdir(parents=True, exist_ok=True)

    # print the parameters
    _initialize_log_file(output_path, "Bekleding Q-variant")
    logging.info("De volgende parameters zijn gelezen uit het configuratiebestand:")
    logging.info(f" traject_id:              {traject_id}")
    logging.info(f" bekleding_input_csv:     {input_csv}")
    logging.info(f" database_path_current:   {database_path_current}")
    logging.info(f" database_path_future:    {database_path_future}")
    logging.info(f" output_map_waterstand:   {waterlevel_path}")
    logging.info(f" hr_profielen_dir:        {profielen_path}")
    logging.info(f" output_map_bekleding:    {output_path}\n")

    # run the bekleding_qvariant workflow
    qvariant_main(
        traject_id,
        input_csv,
        paths_to_databases,
        waterlevel_path,
        profielen_path,
        hydraring_bin_dir,
        output_path,
    )

def run_gebu_zst(config_file: Path, results_folder: Path = None):

    mandatory_parameters = ['traject_id', 'bekleding_input_csv', 'steentoets_map', 'hr_profielen_dir', 'output_map_bekleding']
    config_file = config_file if isinstance(config_file, Path) else Path(config_file)

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    _config_dir = config_file.parent
    traject_id = parameters['traject_id']
    input_csv = _config_dir.joinpath(parameters['bekleding_input_csv'])
    steentoets_path = _config_dir.joinpath(parameters['steentoets_map'])
    profielen_path = _config_dir.joinpath(parameters['hr_profielen_dir'])
    output_path = _config_dir.joinpath(parameters['output_map_bekleding'])
    if 'versterking_bekleding' in parameters:
        versterking_bekleding = parameters['versterking_bekleding']
    else:
        versterking_bekleding = 'uitbreiden'

    if results_folder is None:
        output_path_qvar = _config_dir.joinpath(parameters['output_map_bekleding'])
        output_path_results = _config_dir.joinpath(parameters['output_map_bekleding'])
    else: # used for testing
        output_path_results = results_folder.joinpath(parameters['output_map_bekleding'])
        # Recreate the output folder
        if output_path_results.exists():
            output_path_results.rmdir()
        output_path_results.mkdir(parents=True, exist_ok=True)
        #get Q-var from testdata
        output_path_qvar = Path(parameters['output_map_bekleding'])

    # print the parameters
    _initialize_log_file(output_path, "Bekleding Q-variant")

    logging.info("De volgende parameters zijn gelezen uit het configuratiebestand:")
    logging.info(f" traject_id:              {traject_id}")
    logging.info(f" bekleding_input_csv:     {input_csv}")
    logging.info(f" steentoets_map:          {steentoets_path}")
    logging.info(f" hr_profielen_dir:        {profielen_path}")
    logging.info(f" output_map_bekleding:    {output_path}")
    logging.info(f" versterking_bekleding:   {versterking_bekleding}\n")

    # run the bekleding_gebu_zst workflow
    gebu_zst_main(
        traject_id,
        input_csv,
        steentoets_path,
        profielen_path,
        dikernel_bin_dir,
        output_path_qvar,
        output_path_results,
        versterking_bekleding,
    )
    
def get_characteristic_profiles_for_traject(config_file: str, results_folder: Path = None):   
    mandatory_parameters = ['traject_id', 'output_map_profielen']
    config_file = config_file if isinstance(config_file, Path) else Path(config_file)

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return



    # Accessing parameters
    _parent_dir = config_file.parent
    traject_id = parameters['traject_id']
    if results_folder is None:
        output_path = _parent_dir.joinpath(parameters['output_map_profielen'])
    else: # used for testing
        output_path = results_folder.joinpath(parameters['output_map_profielen'])
        # Recreate the output folder
        if output_path.exists():
            output_path.rmdir()
        output_path.mkdir(parents=True, exist_ok=True)
    
    dx = parameters.getint('dx', fallback=25)  # set default value to 25 if not present
    voorland_lengte = parameters.getint('voorland_lengte', fallback=50)  # set default value to 50 if not present
    achterland_lengte = parameters.getint('achterland_lengte', fallback=75)  # set default value to 75 if not present
    # get traject_shape from parameters. This is either a FALSE or none (or nothing filled in), or a pathname
    try: 
        traject_shape = parameters.getboolean('traject_shapefile', fallback=False)
    except:
        traject_shape = str(parameters['traject_shapefile'])
    flip_traject = parameters.getboolean('flip_traject', fallback=False)  # set default value to False if not present
    flip_waterkant = parameters.getboolean('flip_waterkant', fallback=False)  # set default value to False if not present

    # initialize log file
    _initialize_log_file(output_path, "get_characteristic_profiles")
    
    # print the parameters
    logging.info("\nDe volgende parameters zijn gelezen uit het configuratiebestand:\n")
    logging.info(f" traject_id:          {traject_id}")
    logging.info(f" output_path:         {output_path.__str__}")
    logging.info(f" dx:                  {dx}")
    logging.info(f" voorland_lengte:     {voorland_lengte}")
    logging.info(f" achterland_lengte:   {achterland_lengte}")
    logging.info(f" traject_shape:       {traject_shape}")
    logging.info(f" flip_traject:        {flip_traject}")
    logging.info(f" flip_waterkant:      {flip_waterkant}\n")

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

def selecteer_profiel(config_file: Path, results_folder: Path = None):
    mandatory_parameters = ['vakindeling_geojson',
                            'output_map_ahn_profielen',
                            'karakteristieke_profielen_map',
                            'profiel_info_csv',
                            'output_map_representatieve_profielen']
    config_file = config_file if isinstance(config_file, Path) else Path(config_file)
    
    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    _parent_dir = config_file.parent
    vakindeling_geojson = _parent_dir.joinpath(parameters['vakindeling_geojson'])
    ahn_profielen = _parent_dir.joinpath(parameters['output_map_ahn_profielen'])
    karakteristieke_profielen = _parent_dir.joinpath(parameters['karakteristieke_profielen_map'])
    profiel_info_csv = _parent_dir.joinpath(parameters['profiel_info_csv'])
    if results_folder is None:
        output_path = _parent_dir.joinpath(parameters['output_map_representatieve_profielen'])
    else: # used for testing
        output_path = results_folder.joinpath(parameters['output_map_representatieve_profielen'])
        # Recreate the output folder
        if output_path.exists():
            shutil.rmtree(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
    invoerbestand = parameters.get('ingevoerde_profielen', fallback=False)

    # initialize log file
    _initialize_log_file(output_path, "selectie_profielen")
    # print the parameters
    logging.info("\nDe volgende parameters zijn gelezen uit het configuratiebestand:\n")
    logging.info(f" vakindeling_geojson:             {vakindeling_geojson}")
    logging.info(f" ahn_profielen:                   {ahn_profielen}")
    logging.info(f" karakteristieke_profielen:       {karakteristieke_profielen}")
    logging.info(f" profiel_info_csv:                {profiel_info_csv}")
    logging.info(f" uitvoer_map:                     {output_path}")
    logging.info(f" invoerbestand:                   {invoerbestand}\n")
 
    # run the select_profiles_workflow
    main_profiel_selectie(
        vakindeling_geojson,
        ahn_profielen,
        karakteristieke_profielen,
        profiel_info_csv,
        output_path,
        invoerbestand,
        "minimum"
    )

def obtain_inner_toe_line(config_file: Path, results_folder: Path = None):
    mandatory_parameters = ['karakteristieke_profielen_map', 'profiel_info_csv', 'output_map_teenlijn']
    config_file = config_file if isinstance(config_file, Path) else Path(config_file)

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    _parent_dir = config_file.parent
    karakteristieke_profielen_map = _parent_dir.joinpath(parameters['karakteristieke_profielen_map'])
    profiel_info_csv = _parent_dir.joinpath(parameters['profiel_info_csv'])
    if results_folder is None:
        output_path = _parent_dir.joinpath(parameters['output_map_teenlijn'])
    else: # used for testing
        output_path = results_folder.joinpath(parameters['output_map_teenlijn'])
        # Recreate the output folder
        if output_path.exists():
            shutil.rmdir()
        output_path.mkdir(parents=True, exist_ok=True)

    # initialize log file
    _initialize_log_file(output_path, "teenlijn_bepaling")
    # print the parameters
    logging.info("\nDe volgende parameters zijn gelezen uit het configuratiebestand:\n")
    logging.info(f" karakteristieke_profielen_map:   {karakteristieke_profielen_map}")
    logging.info(f" profiel_info_csv:                {profiel_info_csv}")
    logging.info(f" teenlijn_uitvoer:                {output_path}\n")

    # run the teenlijn_workflow
    main_teenlijn(
        karakteristieke_profielen_map,
        profiel_info_csv,
        output_path,
    )

def count_buildings(config_file: Path, results_folder: Path = None):
    mandatory_parameters = ['traject_id',
                            'teenlijn_geojson',
                            'vakindeling_geojson',
                            'output_map_bebouwing',
                            'bag_gebouwen_geopackage']
    config_file = config_file if isinstance(config_file, Path) else Path(config_file)

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    _parent_dir = config_file.parent
    traject_id = parameters['traject_id']
    teenlijn_geojson = _parent_dir.joinpath(parameters['teenlijn_geojson'])
    vakindeling_geojson = _parent_dir.joinpath(parameters['vakindeling_geojson'])
    gebouwen_geopackage = _parent_dir.joinpath(parameters['bag_gebouwen_geopackage'])
    flip_waterkant = parameters.getboolean('flip_waterkant', fallback=False)
    
    if results_folder is None:
        output_path = _parent_dir.joinpath(parameters['output_map_bebouwing'])
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

    # initialize log file
    _initialize_log_file(output_path, "bepaling_bebouwing")

    # print the parameters
    logging.info("\nDe volgende parameters zijn gelezen uit het configuratiebestand:\n")
    logging.info(f" traject_id:          {traject_id}")
    logging.info(f" teenlijn_geojson:    {teenlijn_geojson}")
    logging.info(f" vakindeling_geojson: {vakindeling_geojson}")
    logging.info(f" uitvoer_map:         {output_path}")
    logging.info(f" gebouwen_geopackage: {gebouwen_geopackage}")
    logging.info(f" flip_waterkant:      {flip_waterkant}\n")

    # Run the derive_buildings_workflow
    main_bebouwing(
        traject_id,
        teenlijn_geojson,
        vakindeling_geojson,
        output_path,
        gebouwen_geopackage,
        richting
    )

def create_database(config_file: Path, results_folder: Path = None):
    mandatory_parameters = ['traject_id',
                            'vakindeling_geojson',
                            'karakteristieke_profielen_csv',
                            'gebouwen_csv',
                            'output_map_database',
                            'vrtool_database_naam',
                            'hr_input_csv',
                            'output_map_waterstand',
                            'output_map_overslag']
    config_file = config_file if isinstance(config_file, Path) else Path(config_file)

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    _parent_dir = config_file.parent
    traject_id = parameters['traject_id']
    vakindeling_geojson = _parent_dir.joinpath(parameters['vakindeling_geojson'])
    measure_configuration = _parent_dir.joinpath(parameters['maatregelen_configuratie'])
    characteristic_profile_csv = _parent_dir.joinpath(parameters['karakteristieke_profielen_csv'])
    building_csv_path = _parent_dir.joinpath(parameters['gebouwen_csv'])
    output_db_name = parameters['vrtool_database_naam']
    hr_input_csv = _parent_dir.joinpath(parameters['hr_input_csv'])
    waterlevel_results_path = _parent_dir.joinpath(parameters['output_map_waterstand'])
    overflow_results_path = _parent_dir.joinpath(parameters['output_map_overslag'])
    piping_path = _parent_dir.joinpath(parameters.get('piping_input_csv', fallback=False))
    stability_path = _parent_dir.joinpath(parameters.get('stabiliteit_input_csv', fallback=False))
    revetment_path = _parent_dir.joinpath(parameters.get('output_map_bekleding', fallback=False))
    use_hydraring = parameters.getboolean('gebruik_hydraring', fallback=True)  # set default value to True if not present
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
    # initialize log file
    _initialize_log_file(output_path, "write_database")
    
    # print the parameters
    logging.info("\nDe volgende parameters zijn gelezen uit het configuratiebestand:\n")
    logging.info(f" traject_id:                  {traject_id}")
    logging.info(f" vakindeling_geojson:         {vakindeling_geojson}")
    logging.info(f" measure_configuration:       {measure_configuration}")
    logging.info(f" characteristic_profile_csv:  {characteristic_profile_csv}")
    logging.info(f" building_csv_path:           {building_csv_path}")
    logging.info(f" output_dir:                  {output_path}")
    logging.info(f" output_db_name:              {output_db_name}")
    logging.info(f" hr_input_csv:                {hr_input_csv}")
    logging.info(f" waterlevel_results_path:     {waterlevel_results_path}")
    logging.info(f" overflow_results_path:       {overflow_results_path}")
    logging.info(f" piping_path:                 {piping_path}")
    logging.info(f" stability_path:              {stability_path}")
    logging.info(f" revetment_path:              {revetment_path}")
    logging.info(f" gebruik_hydraring:           {use_hydraring}\n")

    # run the write_database_workflow
    write_database_main(
        traject_id,
        vakindeling_geojson,
        characteristic_profile_csv,
        building_csv_path,
        output_path,
        output_db_name,
        hr_input_csv,
        waterlevel_results_path,
        overflow_results_path,
        piping_path,
        stability_path,
        revetment_path,
        measure_configuration,
        use_hydraring=use_hydraring,
    )

if __name__ == '__main__':
    #Use this structure to test api calls locally but do not commit any changes.
    create_database(r'c:\Repositories\VRSuiteUtils\tests\test_data\31-1_v2\preprocessor.config', 
                                                results_folder=Path(r'c:\Repositories\VRSuiteUtils\tests\test_data\31-1_v2\test'))
