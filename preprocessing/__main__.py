import click
from preprocessing.workflows.hydraring_overflow_workflow import main
from pathlib import Path


@click.group()
def cli():
    pass


@cli.command(
    name="overflow", help="Generates and evalutes the Hydraring overflow data."
)
@click.argument("work_dir", type=click.Path(exists=True), nargs=1)
@click.argument("database_paths", type=click.Path(exists=True), nargs=2)
@click.argument("hydraring_path", type=click.Path(exists=True), nargs=1)
@click.argument("file_name", type=str, nargs=1)
def generate_and_evaluate_hydraring_computations(**kwargs):
    main(
        Path(kwargs["work_dir"]),
        list(
            map(Path(kwargs["database_paths"])),
            Path(kwargs["hydraring_path"]),
            kwargs["file_name"],
        ),
    )


if __name__ == "__main__":
    cli()