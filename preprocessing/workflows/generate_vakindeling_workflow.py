from pathlib import Path

import geopandas as gpd
import pandas as pd

from postprocessing.plot_functions import plot_vakindeling
from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape


def vakindeling_main(traject_id: str,
                     vakindeling_csv_path: str,
                     output_folder: Path,
                     traject_shape_path=False,
                     flip_traject=False,
                        ):
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

# #
# if __name__ == "__main__":
#     traject = "38-1"
#     file_location = r"c:\VRM\test_vakindeling_workflow\Vakindeling_38-1_300623.csv"
#     output_folder = r"c:\VRM\test_vakindeling_workflow\result"
#     vakindeling_main(traject, file_location, Path(output_folder))
