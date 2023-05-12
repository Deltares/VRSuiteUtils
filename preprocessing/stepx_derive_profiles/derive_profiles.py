from preprocessing.stepx_derive_profiles.profile_functions import Traject
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import csv

def run():
    traject = Traject("38-1")
    traject_shape_path = Path(r'c:\VRM\Gegevens 38-1\shape\dijktrajecten.shp') # or False, if you want to retrieve it from NBWP
    traject.get_traject_data(NBWP_shape_path=traject_shape_path)
    traject.generate_cross_section(cross_section_distance=100, # distance between cross sections
                                   foreshore_distance=50,
                                   hinterland_distance=75)


    # print(traject.break_points[0].y)

    # x_values = [i.x for i in traject.break_points]
    # y_values = [i.y for i in traject.break_points]
    # plt.figure()
    # plt.plot(x_values, y_values, 'o')
    # # [plt.plot(line.xy[0], line.xy[1], 'o', label='line') for line in traject.cross_sections]
    # plt.gca().set_aspect('equal', adjustable='box')
    # plt.show()

    output_path = Path(r'c:\VRM\Gegevens 38-1\profiles')
    # write traject.profiles to a csv file
    with open(output_path.joinpath('traject_profiles.csv'), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        count = 0
        foreshore_length = 30
        for profile in traject.profiles:
            if count == 0:
                header = ['ProfileID', 'x_coord', 'y_coord', 'm_value'] + list(np.round(profile[:, 3], 1)-foreshore_length)
                writer.writerow(header)
                row = [count+1, traject.break_points[count].x, traject.break_points[count].y, traject.m_values[count]] + list(np.round(profile[:, 2], 1))
                writer.writerow(row)
                count += 1
            else:
                row = [count+1, traject.break_points[count].x, traject.break_points[count].y, traject.m_values[count]] + list(np.round(profile[:, 2], 1))
                writer.writerow(row)
                count += 1

    # TO DO: create plot for each profile
    # TO DO: add M-value + x,y coordinate of BUK point to each plot and to csv file

if __name__ == '__main__':
    run()
