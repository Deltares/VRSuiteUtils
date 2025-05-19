import click
import preprocessing.api as api
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
# import api



@click.group()
def cli():
    pass

@cli.command(
    name="maak_project", help="Maakt een project folder structuur aan voor de VRM."
)

@click.option("--project_folder",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de folder waar het project moet worden aangemaakt.")

@click.option("--traject_id",
                type=str,
                nargs=1,
                required=True,
                help="Traject ID van het project.")

def create_project(project_folder, traject_id):
    print(f"Start aanmaken project folder structuur voor traject {traject_id} in folder: {project_folder}")
    api.create_project(project_folder, traject_id)


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
    name="overflow Hydra-NL", help="Processes the Hydra-NL overflow computation results."
)
@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .txt bestand met alle benodigde paden en instellingen.")
def evaluate_hydra_nl_overflow (config_file):
    print(f"Start waterstandberekeningen met Hydra-Ring met configuratie file: {config_file}")
    api.evaluate_hydranl_overflow_computations(config_file)

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
    name="waterlevel Hydra-NL", help="Processes the Hydra-NL water level computation results."
)
@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .txt bestand met alle benodigde paden en instellingen.")
def evaluate_hydra_nl_waterlevel (config_file):
    print(f"Start waterstandberekeningen met Hydra-Ring met configuratie file: {config_file}")
    api.evaluate_hydranl_waterlevel_computations(config_file)

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
    print(f"Start gras- en steenbekleding berekeningen met configuratie file: {config_file}")
    api.run_gebu_zst(config_file)



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
    print(f"Start selecteren van karakteristieke profielen per dijkvak met configuratie file: {config_file}")
    api.selecteer_profiel(config_file)

@cli.command(
    name="genereer_teenlijn", help="Voor het afleiden van de teenlijn van een dijktraject"
)

@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .txt bestand met alle benodigde paden en instellingen.")

def obtain_inner_toe_line(config_file):
    print(f"Start genereren van de teenlijn met configuratie file: {config_file}")
    api.obtain_inner_toe_line(config_file)

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
    print(f"Start tellen van gebouwen met configuratie file: {config_file}")
    api.count_buildings(config_file)

@cli.command(
    name="maak_database", help="Vat alle resultaten van de preprocessing samen in een database"
)

@click.option("--config_file",
                type=click.Path(),
                nargs=1,
                required=True,
                help="Link naar de configuratie file. Dit is een .txt bestand met alle benodigde paden en instellingen.")

def create_database(config_file):
    print(f"Start maken van database met configuratie file: {config_file}")
    api.create_database(config_file)





if __name__ == "__main__":
    cli()


