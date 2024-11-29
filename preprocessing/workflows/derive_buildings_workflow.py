from pathlib import Path

from preprocessing.step3_derive_general_data.derive_bebouwing import count_buildings_per_vak


def main_bebouwing(
    traject_name: str,
    teenlijn_geojson: Path,
    vakindeling_geojson: Path,
    output_dir: Path,
    all_buildings_filename: Path,
        richting: bool,
    ):

    # check if output_path exists, if not create it
    if not output_dir.exists():
        output_dir.mkdir()
        print("teenlijn folder created")

    count_buildings_per_vak(
        traject_name,
        teenlijn_geojson,
        vakindeling_geojson,
        output_dir,
        all_buildings_filename,
    direction_parameter=richting)
