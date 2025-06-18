from preprocessing.step3_derive_general_data.profile_functions import Traject
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import csv
import time
import os
import logging


def profile_generator(traject_id: str,
                      output_path: Path,
                      foldername_output_csv: Path,
                      dx: int=25,
                      fsd: int=50,
                      hld: int=75,
                      NBPW_shape_path=False,
                      flip_traject: bool=False,
                      flip_waterside: bool=False,
                      ):
# time how long this takes
    traject = Traject(traject_id)
    logging.info(f"Start genereren profielen op basis van AHN4 voor traject {traject_id}.")

    # traject.get_traject_data(NBWP_shape_path=traject_shape_path)
    traject.get_traject_data(NBPW_shape_path)

    # in case the traject shape is oriented in the opposite direction as the vakindeling, flip it.
    # if this is the case, the user should have also used this flip function when using the vakindeling workflow.
    if flip_traject:
        traject.flip_traject()
        logging.info(f"flip_traject instelling staat aan. Traject {traject_id} wordt omgedraaid.")


    traject.generate_cross_section(cross_section_distance=dx, # distance between cross sections
                                   foreshore_distance=fsd,
                                   hinterland_distance=hld,
                                   flip_water_side=flip_waterside,
                                   )


    # loop through profiles and write each profile to a separate csv file and add a counter
    for index, profile in enumerate(traject.profiles,start=1):
        # Define the filename for the CSV
        filename = f"ahn_profielen/profile_{index:04}.csv" # Assuming filenames like 'profile_0001.csv', 'profile_0002.csv', etc. pad to 4 digits to ensure correct sorting

        # Write the profile data to the CSV file
        with open(Path(os.getcwd()).joinpath(output_path,filename), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # write x coordinates (profile[0]) on first row
            writer.writerow(list(profile[0]))
            # write z coordinates (profile[1]) on second row
            writer.writerow(np.round(list(profile[1]),2))

        logging.info(f"Profiel {index} opgeslagen als profile_{index:04}.csv")

    # write 1 file with all profile characteristics
    with open(Path(os.getcwd()).joinpath(output_path, 'traject_profiles.csv'), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        count = 0
        header = ['ProfileID',
                  'length_fs','x_coord_fs', 'y_coord_fs',
                  'length_hl', 'x_coord_hl', 'y_coord_hl',
                  'm_value', 'csv_filename']
        writer.writerow(header)
        for count, profile in enumerate(traject.profiles,start=0):
            row = [count,
                   fsd, traject.foreshore_coords[count].x, traject.foreshore_coords[count].y,
                   hld, traject.hinterland_coords[count].x, traject.hinterland_coords[count].y,
                   traject.m_values[count], f"profile_{count+1:04}.csv"]
            writer.writerow(row)
    
    logging.info(f"Alle profiel karakteristieken zijn opgeslagen in traject_profiles.csv\n")

