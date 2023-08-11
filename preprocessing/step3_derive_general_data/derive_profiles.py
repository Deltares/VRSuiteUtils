from preprocessing.step3_derive_general_data.profile_functions import Traject
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import csv
import time
def profile_generator(traject_id: str,
                      output_path: Path,
                      NBPW_shape_path=False,
                      dx: int=25,
                      flip_traject: bool=False,
                      flip_waterside: bool=False,
                      fsd: int=50,
                      hld: int=50,
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

    # check if output_path exists, if not create it
    if not output_path.exists():
        output_path.mkdir()
        print("dijkinfo folder created")


    # check if output_path.joinpath(profiles) exists, if not create it
    foldername_output_csv = "profile_csv"
    if not output_path.joinpath(foldername_output_csv).exists():
        output_path.joinpath(foldername_output_csv).mkdir()
        print("output folder created")
    # if the directory exists, but contains files or folders, delete all files and folders
    else:
        for file in output_path.joinpath(foldername_output_csv).iterdir():
            if file.is_dir():
                for subfile in file.iterdir():
                    subfile.unlink()
                file.rmdir()
            else:
                file.unlink()
        print("output folder emptied")

    # loop through profiles and write each profile to a separate csv file and add a counter
    for index, profile in enumerate(traject.profiles):
        # Define the filename for the CSV
        filename = f"profile_{index+1}.csv"  # Assuming filenames like 'profile_1.csv', 'profile_2.csv', etc.

        # Write the profile data to the CSV file
        with open(output_path.joinpath(foldername_output_csv,filename), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # write x coordinates (profile[0]) on first row
            writer.writerow(list(profile[0]))
            # write z coordinates (profile[1]) on second row
            writer.writerow(np.round(list(profile[1]),2))

        print(f"Saved profile {index + 1} to {filename}")

    # write 1 file with all profile characteristics
    with open(output_path.joinpath('traject_profiles.csv'), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        count = 0
        header = ['ProfileID',
                  'x_coord_fs', 'y_coord_fs',
                  'x_coord_hl', 'y_coord_hl',
                  'm_value', 'csv_filename']
        writer.writerow(header)
        for profile in traject.profiles:
            row = [count + 1,
                   traject.foreshore_coords[count].x, traject.foreshore_coords[count].y,
                   traject.hinterland_coords[count].x, traject.hinterland_coords[count].y,
                   traject.m_values[count], f"profile_{count + 1}.csv"]
            writer.writerow(row)
            count += 1

    # print the total time this function runs
    print(f"Total time: {round(time.time() - start_time,2)} seconds")

if __name__ == '__main__':
    profile_generator(traject_id="38-1",
                      output_path=Path(r'c:\VRM\Gegevens 38-1\dijkinfo'),
                      NBPW_shape_path=False,
                      dx=2500,
                      flip_traject=False,
                      flip_waterside=False,
                      fsd=50,
                      hld=75,
                      )
