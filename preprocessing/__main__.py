import click
import preprocessing.api
from preprocessing.workflows.hydraring_overflow_workflow import overflow_main
from preprocessing.workflows.hydraring_waterlevel_workflow import waterlevel_main
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
import api



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
def vakindeling(config_file):
    print(f"Start genereren geojson van vakindeling met configuratie file: {config_file}")
    api.generate_vakindeling_shape(config_file)



@cli.command(
    name="overflow", help="Generates and evaluates the Hydra-Ring overflow computations."
)
@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .json bestand met alle benodigde paden en instellingen.")
def generate_and_evaluate_overflow_computations(config_file):
    
    print(f"Start overslagberekeningen met Hydra-Ring met configuratie file: {config_file}")
    
    api.generate_and_evaluate_overflow_computations(config_file)


@cli.command(
    name="waterlevel", help="Generates and evaluates the Hydra-Ring water level computations."
)
@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .txt bestand met alle benodigde paden en instellingen.")

def generate_and_evaluate_water_level_computations(config_file):
    print(f"Start waterstandberekeningen met Hydra-Ring met configuratie file: {config_file}")
    api.generate_and_evaluate_waterlevel_computations(config_file)


@cli.command(
    name="bekleding_qvariant", help="Genereert de belastinginvoer voor bekledingen. Dit is de eerste"
                                           "stap voor de bekleding sommen. Hierna volgt nog 'bekleding_gebu_zst'"
)

@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .txt bestand met alle benodigde paden en instellingen.")

def run_bekleding_qvariant(config_file):
    print(f"Start Q-variant berekeningen met configuratie file: {config_file}")
    api.run_bekleding_qvariant(config_file)



@cli.command(
    name="bekleding_gebu_zst", help="Genereert de invoer voor gras- en steenbekleding voor de VRTool. Dit is de tweede "
                                    "(en laatste) stap voor het genereren van invoer voor bekledingen."
)

@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .txt bestand met alle benodigde paden en instellingen.")

def run_gebu_zst(config_file):
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

def run_characteristic_profiles_for_traject(config_file):
    print(f"Start genereren van karakteristieke profielen op basis van AHN met configuratie file: {config_file}")
    api.get_characteristic_profiles_for_traject(config_file)


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


@cli.command(
    name="tel_gebouwen", help="Voor het afleiden van het aantal gebouwen bij ieder dijkvak vanaf 0 tot 50 meter"
                              " vanaf de teenlijn landinwaarts"
)

@click.option("--config_file",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Link naar de configuratie file. Dit is een .txt bestand met alle benodigde paden en instellingen.")

def count_buildings(config_file):
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
    uitvoer_map = parameters['output_map_bebouwing']
    gebouwen_geopackage = parameters['bag_gebouwen_geopackage']
    flip_waterkant = parameters.getboolean('flip_waterkant', fallback=False)

    if flip_waterkant == True:
        richting = -1
    else:
        richting = 1

    # print the parameters
    print("\nThe following parameters are read from the configuration file:\n")
    print(f"traject_id: {traject_id}")
    print(f"teenlijn_geojson: {teenlijn_geojson}")
    print(f"vakindeling_geojson: {vakindeling_geojson}")
    print(f"uitvoer_map: {uitvoer_map}")
    print(f"gebouwen_geopackage: {gebouwen_geopackage}")
    print(f"flip_waterkant: {flip_waterkant}")

    # run the derive_buildings_workflow
    main_bebouwing(
        traject_id,
        Path(teenlijn_geojson),
        Path(vakindeling_geojson),
        Path(uitvoer_map),
        Path(gebouwen_geopackage),
        richting
    )


@cli.command(
    name="maak_database", help="Vat alle resultaten van de preprocessing samen in een database"
)

@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .txt bestand met alle benodigde paden en instellingen.")

def create_database(config_file):
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
    output_dir = parameters['output_map_database']
    output_db_name = parameters['vrtool_database_naam']
    hr_input_csv = parameters['hr_input_csv']
    waterlevel_results_path = parameters['output_map_waterstand']
    overflow_results_path = parameters['output_map_overslag']
    piping_path = parameters.get('piping_input_csv', fallback=False)
    stability_path = parameters.get('stabiliteit_input_csv', fallback=False)
    revetment_path = parameters.get('output_map_bekleding', fallback=False)

    # print the parameters
    print("\nThe following parameters are read from the configuration file:\n")
    print(f"traject_id: {traject_id}")
    print(f"vakindeling_geojson: {vakindeling_geojson}")
    print(f"characteristic_profile_csv: {characteristic_profile_csv}")
    print(f"building_csv_path: {building_csv_path}")
    print(f"output_dir: {output_dir}")
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


