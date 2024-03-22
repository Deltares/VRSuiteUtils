import click
from preprocessing.workflows.hydraring_overflow_workflow import overflow_main
from preprocessing.workflows.hydraring_waterlevel_workflow import waterlevel_main
from preprocessing.workflows.generate_vakindeling_workflow import vakindeling_main
from preprocessing.workflows.bekleding_qvariant_workflow import qvariant_main
from preprocessing.workflows.bekleding_gebu_zst_workflow import gebu_zst_main
from preprocessing.workflows.get_profiles_workflow import main_traject_profiles
from preprocessing.workflows.teenlijn_workflow import main_teenlijn
from preprocessing.workflows.derive_buildings_workflow import main_bebouwing
from preprocessing.workflows.select_profiles_workflow import main_profiel_selectie
from preprocessing.workflows.write_database_workflow import write_database_main
import configparser
from pathlib import Path
import os
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


@click.group()
def cli():
    pass


@cli.command(
    name="vakindeling", help="Creert een shapefile voor de vakindeling op basis van de ingegeven vakindeling CSV."
)
@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .json bestand met alle benodigde paden en instellingen.")

# write a function that reads the configuration file and runs the vakindeling workflow
def generate_vakindeling_shape(config_file):
    mandatory_parameters = ['traject_id', 'vakindeling_csv', 'output_map_vakindeling']

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    traject_id = parameters['traject_id']
    vakindeling_csv = parameters['vakindeling_csv']
    output_folder_vakindeling = Path(r"{}".format(parameters['output_map_vakindeling']))
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


@cli.command(
    name="overflow_config", help="Generates and evaluates the Hydra-Ring overflow computations."
)
@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .json bestand met alle benodigde paden en instellingen.")

def generate_and_evaluate_overflow_computations_config(config_file):
    mandatory_parameters = ['hr_input_csv', 'database_path_HR_current', 'database_path_HR_future', 'hr_profielen_dir', 'output_map_overslag']

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    file_path = parameters['hr_input_csv']
    database_path_current = parameters['database_path_HR_current']
    database_path_future = parameters['database_path_HR_future']
    profielen_dir = parameters['hr_profielen_dir']
    output_path = parameters['output_map_overslag']

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
        [Path(database_path_current), Path(database_path_future)],
        Path(profielen_dir),
        Path(os.path.dirname(os.path.realpath(__file__))).joinpath('externals', 'HydraRing-23.1.1'),
        Path(output_path),
    )


@cli.command(
    name="waterlevel_config", help="Generates and evaluates the Hydra-Ring water level computations."
)
@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .txt bestand met alle benodigde paden en instellingen.")

def generate_and_evaluate_water_level_computations_config(config_file):
    mandatory_parameters = ['hr_input_csv', 'database_path_HR_current', 'database_path_HR_future', 'output_map_waterstand']

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    file_path = parameters['hr_input_csv']
    database_path_current = parameters['database_path_HR_current']
    database_path_future = parameters['database_path_HR_future']
    output_path = parameters['output_map_waterstand']

    # print the parameters
    print("The following parameters are read from the configuration file:")
    print(f"file_path: {file_path}")
    print(f"database_path_current: {database_path_current}")
    print(f"database_path_future: {database_path_future}")
    print(f"output_path: {output_path}")

    # run the water level computations
    waterlevel_main(
        Path(file_path),
        [Path(database_path_current), Path(database_path_future)],
        Path(os.path.dirname(os.path.realpath(__file__))).joinpath('externals', 'HydraRing-23.1.1'),
        Path(output_path),
    )

@cli.command(
    name="bekleding_qvariant_config", help="Genereert de belastinginvoer voor bekledingen. Dit is de eerste"
                                           "stap voor de bekleding sommen. Hierna volgt nog 'bekleding_gebu_zst'"
)

@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .txt bestand met alle benodigde paden en instellingen.")

def run_bekleding_qvariant_config(config_file):
    mandatory_parameters = ['traject_id',
                            'bekleding_input_csv',
                            'database_path_bekleding',
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
    database_path = parameters['database_path_bekleding']
    waterlevel_path = parameters['output_map_waterstand']
    profielen_path = parameters['hr_profielen_dir']
    output_path = parameters['output_map_bekleding']

    # print the parameters
    print("The following parameters are read from the configuration file:")
    print(f"traject_id: {traject_id}")
    print(f"bekleding_input_csv: {input_csv}")
    print(f"database_path_bekleding: {database_path}")
    print(f"output_map_waterstand: {waterlevel_path}")
    print(f"hr_profielen_dir: {profielen_path}")
    print(f"output_map_bekleding: {output_path}")

    # run the bekleding_qvariant workflow
    qvariant_main(
        traject_id,
        Path(input_csv),
        Path(database_path),
        Path(waterlevel_path),
        Path(profielen_path),
        Path(os.path.dirname(os.path.realpath(__file__))).joinpath('externals', 'HydraRing-23.1.1'),
        Path(output_path),
    )


@cli.command(
    name="bekleding_gebu_zst_config", help="Genereert de invoer voor gras- en steenbekleding voor de VRTool. Dit is de tweede "
                                    "(en laatste) stap voor het genereren van invoer voor bekledingen."
)

@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .txt bestand met alle benodigde paden en instellingen.")

def run_gebu_zst_config(config_file):
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

    # print the parameters
    print("The following parameters are read from the configuration file:")
    print(f"traject_id: {traject_id}")
    print(f"bekleding_input_csv: {input_csv}")
    print(f"steentoets_map: {steentoets_path}")
    print(f"hr_profielen_dir: {profielen_path}")
    print(f"output_map_bekleding: {output_path}")

    # run the bekleding_gebu_zst workflow
    gebu_zst_main(
        traject_id,
        Path(input_csv),
        Path(steentoets_path),
        Path(profielen_path),
        Path(os.path.dirname(os.path.realpath(__file__))).joinpath('externals', 'DiKErnel'),
        Path(output_path),
    )


@cli.command(
    name="genereer_profielen", help="Voor het selecteren van karakteristieke profielen voor een gegeven dijktraject"
)

@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .txt bestand met alle benodigde paden en instellingen.")

def obtain_the_AHN_profiles_for_traject(config_file):
    mandatory_parameters = ['traject_id', 'output_map_profielen']

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    traject_id = parameters['traject_id']
    output_folder = parameters['output_map_profielen']
    dx = parameters.getint('dx', fallback=25)  # set default value to 25 if not present
    voorland_lengte = parameters.getint('voorland_lengte', fallback=50)  # set default value to 50 if not present
    achterland_lengte = parameters.getint('achterland_lengte', fallback=75)  # set default value to 75 if not present
    traject_shape = parameters.getboolean('traject_shape', fallback=False)  # set default value to False if not present
    flip_traject = parameters.getboolean('flip_traject', fallback=False)  # set default value to False if not present
    flip_waterkant = parameters.getboolean('flip_waterkant', fallback=False)  # set default value to False if not present

    # print the parameters
    print("\nThe following parameters are read from the configuration file:\n")
    print(f"traject_id: {traject_id}")
    print(f"output_folder: {output_folder}")
    print(f"dx: {dx}")
    print(f"voorland_lengte: {voorland_lengte}")
    print(f"achterland_lengte: {achterland_lengte}")
    print(f"traject_shape: {traject_shape}")
    print(f"flip_traject: {flip_traject}")
    print(f"flip_waterkant: {flip_waterkant}")

    # run the get_profiles_workflow
    main_traject_profiles(
        traject_id,
        Path(output_folder),
        dx,
        voorland_lengte,
        achterland_lengte,
        traject_shape,
        flip_traject,
        flip_waterkant,
    )

@cli.command(
    name="selecteer_profiel", help="Selecteer per dijkvak een profiel"
)

@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .txt bestand met alle benodigde paden en instellingen.")

def selecteer_profiel(config_file):
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
    uitvoer_map = parameters['output_map_representatieve_profielen']
    invoerbestand = parameters.get('ingevoerde_profielen', fallback=False)

    # print the parameters
    print("\nThe following parameters are read from the configuration file:\n")
    print(f"vakindeling_geojson: {vakindeling_geojson}")
    print(f"ahn_profielen: {ahn_profielen}")
    print(f"karakteristieke_profielen: {karakteristieke_profielen}")
    print(f"profiel_info_csv: {profiel_info_csv}")
    print(f"uitvoer_map: {uitvoer_map}")
    print(f"invoerbestand: {invoerbestand}")

    # run the select_profiles_workflow
    main_profiel_selectie(
        Path(vakindeling_geojson),
        Path(ahn_profielen),
        Path(karakteristieke_profielen),
        Path(profiel_info_csv),
        Path(uitvoer_map),
        invoerbestand,
        "minimum"
    )


@cli.command(
    name="genereer_teenlijn", help="Voor het afleiden van de teenlijn van een dijktraject"
)

@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .txt bestand met alle benodigde paden en instellingen.")

def obtain_inner_toe_line(config_file):
    mandatory_parameters = ['karakteristieke_profielen_map', 'profiel_info_csv', 'output_map_teenlijn']

    try:
        parameters = read_config_file(config_file, mandatory_parameters)
    except ValueError as e:
        print(f"Error reading configuration: {e}")
        return

    # Accessing parameters
    karakteristieke_profielen_map = parameters['karakteristieke_profielen_map']
    profiel_info_csv = parameters['profiel_info_csv']
    teenlijn_map = parameters['output_map_teenlijn']

    # print the parameters
    print("\nThe following parameters are read from the configuration file:\n")
    print(f"karakteristieke_profielen_map: {karakteristieke_profielen_map}")
    print(f"profiel_info_csv: {profiel_info_csv}")
    print(f"teenlijn_map: {teenlijn_map}")

    # run the teenlijn_workflow
    main_teenlijn(
        Path(karakteristieke_profielen_map),
        Path(profiel_info_csv),
        Path(teenlijn_map),
    )


@cli.command(name="tel_gebouwen", help="Voor het afleiden van het aantal gebouwen bij ieder dijkvak vanaf 0 tot 50 meter"
                                       " vanaf de teenlijn landinwaarts"
)
@click.option("--traject_id",
              type=str,
              nargs=1,
              required=True,
              help="Hier geef je aan om welk traject het gaat. Dit is een string, bijvoorbeeld '38-1'")
@click.option("--teenlijn_geojson",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Hier geef je het pad naar de GeoJSON van de gegenereerde teenlijn. Deze GeoJSON zou teenlijn.geojson"
                   " moeten heten, tenzij de gebruiker de naam heeft aangepast.")
@click.option("--vakindeling_geojson",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Hier geef je het pad naar de GeoJSON van de gegenereerde vakindeling.")
@click.option("--uitvoer_map",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Hier geef je de het pad naar de map waar de uitvoer naartoe moet worden geschreven.")
@click.option("--gebouwen_geopackage",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Hier geef je de het pad naar de geopackage van de BAG. Dit bestand is te downloaden via "
                    "https://service.pdok.nl/lv/bag/atom/bag.xml. Dit is nodig, omdat de BAG het niet toelaat alle "
                   "objecten vanuit het script te downloaden. Het aantal objecten is gelimiteerd tot 1000.")
@click.option("--flip_waterkant",
              type=bool,
              nargs=1,
              default=False,
              help="Standaard wordt hier aangenomen dat het water aan de rechterkant van het traject loopt als je de "
                   "nummering van de vakken volgt. Als het water aan de linkerkant loopt, moet hier True worden "
                   "ingevuld. Default is False. Instelling is identiek aan die bij de workflow voor het genereren van profielen.")

def tel_alle_gebouwen(
    traject_id, teenlijn_geojson, vakindeling_geojson, uitvoer_map, gebouwen_geopackage, flip_waterkant
):
    if flip_waterkant == True:
        richting = -1
    else:
        richting = 1
    main_bebouwing(
        traject_id,
        Path(teenlijn_geojson),
        Path(vakindeling_geojson),
        Path(uitvoer_map),
        Path(gebouwen_geopackage),
        richting
    )


@cli.command(name="maak_database", help="Vat alle resultaten van de preprocessing samen in een database")

@click.option("--traject_id",
              type=str,
              nargs=1,
              required=True,
              help="Hier geef je aan om welk traject het gaat. Dit is een string, bijvoorbeeld '38-1'")
@click.option("--vakindeling_geojson",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Hier geef je het pad naar de GeoJSON van de gegenereerde vakindeling.")
@click.option("--characteristic_profile_csv",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Hier geef je het pad naar de csv van de gegenereerde karakteristieke profielen.")
@click.option("--building_csv_path",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Hier geef je het pad naar de csv van de gegenereerde gebouwen.")
@click.option("--output_dir",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Hier geef je het pad naar de map waar de uitvoer naartoe moet worden geschreven.")
@click.option("--output_db_name",
                type=str,
                nargs=1,
                required=True,
                help="Hier geef je de naam van de database die wordt aangemaakt.")
@click.option("--hr_input_csv",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Hier geef je het pad naar de csv van de gegenereerde HR input.")
@click.option("--waterlevel_results_path",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Hier geef je het pad naar de csv van de gegenereerde waterstandresultaten.")
@click.option("--overflow_results_path",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Hier geef je het pad naar de csv van de gegenereerde overstromingsresultaten.")
@click.option("--piping_path",
                nargs=1,
                required=False,
                help="Hier geef je het pad naar de csv van de gegenereerde pipingresultaten.")
@click.option("--stability_path",
                nargs=1,
                required=False,
                help="Hier geef je het pad naar de csv van de gegenereerde stabiliteitsresultaten.")
@click.option("--revetment_path",
                nargs=1,
                required=False,
                help="Hier geef je het pad naar de csv van de gegenereerde bekledingsresultaten.")

def maak_database(traject_id,
                    vakindeling_geojson,
                    characteristic_profile_csv,
                    building_csv_path,
                    output_dir,
                    output_db_name,
                    hr_input_csv,
                    waterlevel_results_path,
                    overflow_results_path,
                    piping_path,
                    stability_path,
                    revetment_path,
                    ):
        write_database_main(traject_id,
                    Path(vakindeling_geojson),
                    Path(characteristic_profile_csv),
                    Path(building_csv_path),
                    Path(output_dir),
                    output_db_name,
                    Path(hr_input_csv),
                    Path(waterlevel_results_path),
                    Path(overflow_results_path),
                    piping_path,
                    stability_path,
                    revetment_path
                    )


if __name__ == "__main__":
    cli()


