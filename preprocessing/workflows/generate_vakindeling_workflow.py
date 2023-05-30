from pathlib import Path

import geopandas as gpd
import pandas as pd

from postprocessing.plot_functions import plot_vakindeling
from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape


def main(traject_id, file_location):
    #make traject
    traject = TrajectShape(traject_id)

    #get base geometry
    traject.get_traject_shape_from_NBPW()

    #cut up in pieces and verify integrity
    traject.generate_vakindeling_shape(file_location)

    #Save to file
    traject.vakindeling_shape.to_file(file_location.parent.joinpath('Vakindeling_{}.geojson'.format(traject_id)),driver='GeoJSON')

    #Save a plot
    plot_vakindeling(traject.vakindeling_shape, file_location.parent.joinpath('Vakindeling_{}.png'.format(traject_id)))

if __name__ == '__main__':
    traject = '38-1'
    file_location = r'c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_Prioritering WSRL\Gegevens 38-1\test_workflow_vakindeling\vakindeling_38-1.csv'
    main(traject, Path(file_location))

