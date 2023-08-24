import click
from preprocessing.workflows.hydraring_overflow_workflow import overflow_main
from preprocessing.workflows.hydraring_waterlevel_workflow import waterlevel_main
from preprocessing.workflows.generate_vakindeling_workflow import vakindeling_main
from preprocessing.workflows.bekleding_workflow import bekleding_main
from pathlib import Path
import os

@click.group()
def cli():
    pass

@cli.command(
    name="vakindeling", help="Creert een shapefile voor de vakindeling op basis van de ingegeven vakindeling CSV."
)
@click.option("--traject_id",
              type=str,
              nargs=1,
              required=True,
              help="Hier geef je aan om welk traject het gaat. Dit is een string, bijvoorbeeld '38-1'.")
@click.option("--vakindeling_csv",
              type=str,
              nargs=1,
              required=True,
              help="Link naar de CSV met de vakindeling ")
@click.option("--output_folder",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Link naar de map met de Hydraring executable 'MechanismComputation.exe'. Deze executable is meestal"
              " te vinden in: "
                   "'c:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236'")
@click.option("--traject_shape",
              type=str,
              nargs=1,
              required=False,
              help="Link naar de trajectshapefile. Let op: voer deze alleen in als de gebruikte shapefile afwijkt van"
                   " de shapefile in het NBPW. Als je deze optie niet gebruikt, wordt de shapefile uit het NBPW "
                   "gebruikt.")
@click.option("--flip",
              type=bool,
              nargs=1,
              required=False,
              help="Soms staat de shapefile in het NBPW in de tegenovergestelde richting van je vakindeling. Met andere"
                   "woorden: de vakindeling begint aan de 'verkeerde' kant van de shapefile. Als dit het geval is, kan"
                   "de shapefile worden omgedraaid door deze optie op True te zetten.")
def generate_vakindeling_shape(
    traject_id, vakindeling_csv, output_folder, traject_shape, flip
):
    vakindeling_main(
        traject_id,
        vakindeling_csv,
        Path(output_folder),
        traject_shape,
        flip,
    )

########################################################################################################################
@cli.command(
    name="overflow", help="Generates and evalutes the Hydraring overflow data."
)
@click.option("--file_name",
              type=str,
              nargs=1,
              required=True,
              help="Link naar de HR_default.csv.")

@click.option("--database_paths",
              type=click.Path(),
              multiple=True,
              required=True,
              help="Link naar de map met de Hydraulische database. "
                   "Omdat er zowel een map voor de situatie huidig, als voor 2100 is,"
                   "moet deze optie twee keer worden opgegeven. Dus:"
                   "--database_paths <pad naar de database voor huidige situatie> --database_paths <pad naar database "
                   "voor de 2100 situatie>.")

@click.option("--profielen_dir",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Link naar de map met alle profielen.")

@click.option("--hydraring_path",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Link naar de map met de Hydraring executable 'MechanismComputation.exe'. Deze executable is meestal"
              " te vinden in: "
                   "'c:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236'")

@click.option("--output_path",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Dit is de werkmap, waarin je de resultaten van de overslagsommen wilt uitvoeren. Belangrijk is dat"
                   "deze map voorafgaand aan het runnen leeg moet zijn.")

def generate_and_evaluate_waterlevel_computations(
    file_name, database_paths, profielen_dir, hydraring_path, output_path
):
    overflow_main(
        file_name,
        list(map(Path, database_paths)),
        Path(profielen_dir),
        Path(hydraring_path),
        Path(output_path),
    )

@cli.command(
    name="waterlevel", help="Generates and evalutes the Hydraring waterlevel data."
)
@click.option("--file_name",
              type=str,
              nargs=1,
              required=True,
              help="Link naar de HR_default.csv.")

@click.option("--database_paths",
              type=click.Path(),
              multiple=True,
              required=True,
              help="Link naar de map met de Hydraulische database. "
                   "Omdat er zowel een map voor de situatie huidig, als voor 2100 is,"
                   "moet deze optie twee keer worden opgegeven. Dus:"
                   "--database_paths <pad naar de database voor huidige situatie> --database_paths <pad naar database "
                   "voor de 2100 situatie>")

@click.option("--hydraring_path",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Link naar de map met de Hydraring executable 'MechanismComputation.exe'. Deze executable is meestal"
              " te vinden in: "
                   "'c:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236'")

@click.option("--output_path",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Dit is de werkmap, waarin je de resultaten van de waterstandsommen wilt uitvoeren. Belangrijk is dat"
                   "deze map voorafgaand aan het runnen leeg moet zijn.")

def generate_and_evaluate_water_level_computations(
        file_name, database_paths, hydraring_path, output_path
):
    waterlevel_main(
        file_name,
        list(map(Path, database_paths)),
        Path(hydraring_path),
        Path(output_path),
    )

########################################################################################################################


@cli.command(
    name="bekleding", help="Genereert de input data voor bekleding voor de VRTool"
)
@click.option("--input_csv",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Dit is het pad naar het CSV bestand dat de invoer voor bekledingen bevat. Een standaard format voor"
                   "dit bestand is te vinden in de VRTool repository: "
                   "'preprocessing/default_files/Bekleding_default.csv'")
@click.option("--database_path",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Link naar de map met de Hydraulische database(s).")

@click.option("--waterlevel_path",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Link naar het bestand met resultaten van de waterstandsberekeningen.")
@click.option("--steentoets_path",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Link naar de map met de steentoetsfiles.")
@click.option("--profielen_path",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Link naar de map met de profielen.")
@click.option("--output_path",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Uitvoermap. Hier worden de resultaten naartoe geschreven, die invoer zijn voor de database. Als"
                   "deze map nog niet bestaat, wordt deze automatisch aangemaakt. Echter, als deze map al bestaat, maar"
                   "niet leeg is, zal het script automatisch stoppen.")

def generate_bekleding_som(
        input_csv, database_path, steentoets_path, waterlevel_path, profielen_path, output_path
):
    print(Path(os.path.dirname(os.path.realpath(__file__))).parent)
    bekleding_main(
        Path(input_csv),
        Path(database_path),
        Path(waterlevel_path),
        Path(steentoets_path),
        Path(profielen_path),
        Path(os.path.dirname(os.path.realpath(__file__))).parent.joinpath('externals','HydraRing-23.1.1'),
        Path(os.path.dirname(os.path.realpath(__file__))).parent.joinpath('externals','DiKErnel'),
        Path(output_path),
    )
########################################################################################################################

if __name__ == "__main__":
    cli()
