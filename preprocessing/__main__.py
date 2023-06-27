import click
from preprocessing.workflows.hydraring_overflow_workflow import main
from pathlib import Path


@click.group()
def cli():
    pass


@cli.command(
    name="overflow", help="Generates and evalutes the Hydraring overflow data."
)
@click.option("--work_dir", type=click.Path(), nargs=1, required=True)
@click.option("--database_paths", type=click.Path(), multiple=True, required=True)
@click.option("--hydraring_path", type=click.Path(), nargs=1, required=True)
@click.option("--file_name", type=str, nargs=1, required=True)
def generate_and_evaluate_hydraring_computations(
    work_dir, database_paths, hydraring_path, file_name
):
    main(
        Path(work_dir),
        list(
            map(Path(database_paths)),
            Path(hydraring_path),
            file_name,
        ),
    )


if __name__ == "__main__":
    cli()
