from preprocessing.step3_derive_general_data.profile_functions import Traject
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import csv
import time
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
    start_time = time.time()
    traject = Traject(traject_id)
    # traject_shape_path = Path(r'c:\VRM\Gegevens 38-1\shape\dijktrajecten.shp') # or False, if you want to retrieve it from NBWP
    # traject.get_traject_data(NBWP_shape_path=traject_shape_path)
    traject.get_traject_data(NBPW_shape_path)

    # in case the traject shape is oriented in the opposite direction as the vakindeling, flip it.
    # if this is the case, the user should have also used this flip function when using the vakindeling workflow.
    if flip_traject:
        traject.flip_traject()

    traject.generate_cross_section(cross_section_distance=dx, # distance between cross sections
                                   foreshore_distance=fsd,
                                   hinterland_distance=hld,
                                   flip_water_side=flip_waterside,
                                   )


    # loop through profiles and write each profile to a separate csv file and add a counter
    for index, profile in enumerate(traject.profiles,start=1):
        # Define the filename for the CSV
        filename = f"profile_{index:04}.csv" # Assuming filenames like 'profile_0001.csv', 'profile_0002.csv', etc. pad to 4 digits to ensure correct sorting

        # Write the profile data to the CSV file
        with open(output_path.joinpath(foldername_output_csv,filename), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # write x coordinates (profile[0]) on first row
            writer.writerow(list(profile[0]))
            # write z coordinates (profile[1]) on second row
            writer.writerow(np.round(list(profile[1]),2))

        # print(f"Saved profile {index + 1} to {filename}")

    # write 1 file with all profile characteristics
    with open(output_path.joinpath('traject_profiles.csv'), 'w', newline='') as csvfile:
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

    # print the total time this function runs
    # print(f"Total time: {round(time.time() - start_time,2)} seconds")

if __name__ == '__main__':
    profile_generator(traject_id="38-1",
                      output_path=Path(r'c:\VRM\Gegevens 38-1\dijkinfo'),
                      NBPW_shape_path=False,
                      flip_traject=False,
                      flip_waterside=False,
                      dx=2500,
                      # fsd=50,
                      # hld=75,
                      )
