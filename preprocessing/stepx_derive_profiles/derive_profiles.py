from preprocessing.stepx_derive_profiles.profile_functions import Traject
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import csv

def run(option):
    traject = Traject("38-1")
    traject_shape_path = Path(r'c:\VRM\Gegevens 38-1\shape\dijktrajecten.shp') # or False, if you want to retrieve it from NBWP
    traject.get_traject_data(NBWP_shape_path=traject_shape_path)
    traject.generate_cross_section(option, cross_section_distance=1000, # distance between cross sections
                                   foreshore_distance=50,
                                   hinterland_distance=75)

    output_path = Path(r'c:\VRM\Gegevens 38-1\profiles')

    # write traject.profiles to a csv file
    if option == "line":
        with open(output_path.joinpath('traject_profiles4_{}.csv'.format(option)), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            count = 0
            foreshore_length = 50
            for profile in traject.profiles:
                if count == 0:
                    header = ['ProfileID',
                              'x_coord_fs', 'y_coord_fs',
                              'x_coord_BUK', 'y_coord_BUK',
                              'x_coord_hl', 'y_coord_hl',
                              'm_value'] + list(np.round(profile[:, 3], 1)-foreshore_length)
                    writer.writerow(header)
                    row = [count+1,
                           traject.foreshore_coords[count].x, traject.foreshore_coords[count].y,
                           traject.break_points[count].x, traject.break_points[count].y,
                           traject.hinterland_coords[count].x, traject.hinterland_coords[count].y,
                           traject.m_values[count]] + list(np.round(profile[:, 2], 1))
                    writer.writerow(row)
                    count += 1
                else:
                    row = [count+1,
                           traject.foreshore_coords[count].x, traject.foreshore_coords[count].y,
                           traject.break_points[count].x, traject.break_points[count].y,
                           traject.hinterland_coords[count].x, traject.hinterland_coords[count].y,
                           traject.m_values[count]] + list(np.round(profile[:, 2], 1))
                    writer.writerow(row)
                    count += 1
    elif option == "point":
        with open(output_path.joinpath('traject_profiles_{}.csv'.format(option)), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            count = 0
            foreshore_length = 50
            for profile in traject.profiles:
                c_list = []
                if count == 0:
                    header = ['ProfileID',
                              'x_coord_fs', 'y_coord_fs',
                              'x_coord_hl', 'y_coord_hl',
                              'm_value', "foreshore_length"] + ["c" + str(i) for i in range(len(profile))]
                    writer.writerow(header)
                    row = [count + 1,
                           traject.foreshore_coords[count].x, traject.foreshore_coords[count].y,
                           traject.hinterland_coords[count].x, traject.hinterland_coords[count].y,
                           traject.m_values[count], foreshore_length] + list(np.round(profile, 1))
                    writer.writerow(row)
                    count += 1
                else:
                    row = [count + 1,
                           traject.foreshore_coords[count].x, traject.foreshore_coords[count].y,
                           traject.hinterland_coords[count].x, traject.hinterland_coords[count].y,
                           traject.m_values[count], foreshore_length] + list(np.round(profile, 1))
                    writer.writerow(row)
                    count += 1



if __name__ == '__main__':
    run(option="point")
