from pathlib import Path

import geopandas as gpd
import pandas as pd

from preprocessing.visualization.plot_functions import plot_vakindeling
from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape
from preprocessing.step1_generate_shapefile.measure_configuration import MeasureConfiguration

def vakindeling_main(traject_id: str,
                     vakindeling_csv_path: str,
                     output_folder: Path,
                     traject_shape_path=False,
                     flip_traject=False,
                        ):
    _generic_data_dir = Path(__file__).absolute().parent.parent.joinpath('generic_data')

    # make traject
    traject = TrajectShape(traject_id)

    # get base geometry
    traject.get_traject_shape_from_NBPW(traject_shape_path)

    if flip_traject:
        traject.flip_traject()
    # cut up in pieces and verify integrity
    traject.generate_vakindeling_shape(vakindeling_csv_path)

    #check if output folder exists, if not create it:
    if not output_folder.exists():
        output_folder.mkdir(parents=True,exist_ok=True)

    # Save to file
    traject.vakindeling_shape.to_file(
        Path(output_folder).joinpath(f"Vakindeling_{traject_id}.geojson"),
        driver="GeoJSON",
    )

    # Save a plot
    plot_vakindeling(
        traject.vakindeling_shape,
        Path(output_folder).joinpath("Vakindeling_{}.png".format(traject_id)),
    )
    # Generate a csv file with the configuration of measures
    measure_config = MeasureConfiguration(traject.vakindeling_shape)
    measure_config.write_to_csv(
        output_folder.joinpath(f"configuratie_maatregelen.csv")
    )

