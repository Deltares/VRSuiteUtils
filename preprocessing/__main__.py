import click
from preprocessing.workflows.hydraring_overflow_workflow import overflow_main
from preprocessing.workflows.hydraring_waterlevel_workflow import waterlevel_main
from pathlib import Path


@click.group()
def cli():
    pass


@cli.command(
    name="overflow", help="Generates and evalutes the Hydraring overflow data."
)
@click.option("--work_dir",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Dit is de werkmap, waarin je de resultaten van de overslagsommen wilt uitvoeren. Belangrijk is dat"
                   "deze map voorafgaand aan het runnen van het script al een map met de profielen bevat. Deze map met "
                   "profielen moet de naam 'prfl' hebben. Naast de profielenmap, moet de map leeg zijn")
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
@click.option("--file_name",
              type=str,
              nargs=1,
              required=True,
              help="Link naar de HR_default.csv.")
def generate_and_evaluate_waterlevel_computations(
    work_dir, database_paths, hydraring_path, file_name
):
    overflow_main(
        Path(work_dir),
        list(map(Path, database_paths)),
        Path(hydraring_path),
        file_name,
    )

@cli.command(
    name="waterlevel", help="Generates and evalutes the Hydraring waterlevel data."
)
@click.option("--work_dir",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Dit is de werkmap, waarin je de resultaten van de waterstandsommen wilt uitvoeren. Belangrijk is dat"
                   "deze map leeg is")
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
@click.option("--file_name",
              type=str,
              nargs=1,
              required=True,
              help="Link naar de HR_default.csv.")
def generate_and_evaluate_water_level_computations(
    work_dir, database_paths, hydraring_path, file_name
):
    waterlevel_main(
        Path(work_dir),
        list(map(Path, database_paths)),
        Path(hydraring_path),
        file_name,
    )


if __name__ == "__main__":
    cli()
