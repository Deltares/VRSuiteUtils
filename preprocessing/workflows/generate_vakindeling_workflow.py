from pathlib import Path

import geopandas as gpd
import pandas as pd

from preprocessing.visualization.plot_functions import plot_vakindeling
from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape
from preprocessing.step1_generate_shapefile.measure_configuration import MeasureConfiguration
import logging

def vakindeling_main(traject_id: str,
                     vakindeling_csv_path: str,
                     maatregelen_configuratie_path: str,
                     vakindeling_geojson_path: str,
                     output_folder: Path,
                     traject_shape_path=False,
                     flip_traject=False,
                        ):
    # initialize logger

    # make traject
    traject = TrajectShape(traject_id)

    # get base geometry
    logging.info("Laden van de shapefile van het traject")
    traject.get_traject_shape_from_NBPW(traject_shape_path)

    if flip_traject:
        traject.flip_traject()
        logging.info("Trajectshape {} omgekeerd in de juiste richting".format(traject_id))  
    logging.info("Shape geladen voor traject {} \n".format(traject_id))

    logging.info("Opknippen van de shape op basis van de vakindeling")
    # cut up in pieces and verify integrity
    traject.generate_vakindeling_shape(vakindeling_csv_path)



    logging.info("Wegschrijven van de resultaten")
    #check if output folder exists, if not create it:
    if not output_folder.exists():
        output_folder.mkdir(parents=True,exist_ok=True)

    # Save to file
    traject.vakindeling_shape.to_file(
        output_folder.joinpath(Path(vakindeling_geojson_path).name),
        driver="GeoJSON",
    )
    logging.info(
        "Vakindeling van traject {} opgeslagen in {}".format(
            traject_id, output_folder.joinpath(Path(vakindeling_geojson_path).name)
        )
    )
    # Save a plot
    plot_vakindeling(
        traject.vakindeling_shape,
        output_folder.joinpath("Vakindeling_{}.png".format(traject_id)),
    )
    logging.info("Bijbehorende plot opgeslagen")
        
    # Generate a csv file with the configuration of measures
    measure_config = MeasureConfiguration(traject.vakindeling_shape)
    measure_config.write_to_csv(
        output_folder.joinpath(Path(maatregelen_configuratie_path).name)
    )
    logging.info("Configuratie van maatregelen opgeslagen in {}".format(
        output_folder.joinpath(Path(maatregelen_configuratie_path).name)
    ))

    logging.info("Vakindeling workflow voor traject {} is voltooid".format(traject_id))


