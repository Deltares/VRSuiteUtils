import pandas as pd
from scipy.interpolate import interp1d
import numpy as np
from shapely.geometry import Point, LineString
import geopandas
from pathlib import Path



def derive_teenlijn(characteristic_profile_dir,
                    profile_path,
                    output_dir):

    data_profielen = pd.read_csv(profile_path)

    # create empty dataframe for the binnenteen (df_binnenteen), with columns "Names" and x_coord and y_coord and profile number
    df_binnenteen = pd.DataFrame(columns=["Name", "coordinates", "profile_number"])

    # loop through all png files in the characteristic_profile_dir
    for png_file in characteristic_profile_dir.glob('*.png'):
        # get the name of the png file and remove the extension (.png). Do this in 1 line
        profile_name = png_file.stem

        # get the profile number from the profile_name
        profile_number = int(profile_name.split("_")[1])

        # open characteristic_profile_dir.joinpath("{}.csv".format(profile_name)) as df and obtain the last value of column "X"
        # and store it in variable x_teen
        csv_file = characteristic_profile_dir.joinpath("{}.csv".format(profile_name))
        x_teen = round(pd.read_csv(csv_file)["X"].iloc[-1],2)

        # find the corresponding x_coord_fs, y_coord_fs and x_coord_hl, y_coord_fs in data_profielen[csv_filename] == csv_file_name
        # and store them in variables x_fs, y_fs, x_hl, y_hl
        x_fs = data_profielen.loc[data_profielen["csv_filename"] == "{}.csv".format(profile_name), "x_coord_fs"].iloc[0]
        y_fs = data_profielen.loc[data_profielen["csv_filename"] == "{}.csv".format(profile_name), "y_coord_fs"].iloc[0]
        x_hl = data_profielen.loc[data_profielen["csv_filename"] == "{}.csv".format(profile_name), "x_coord_hl"].iloc[0]
        y_hl = data_profielen.loc[data_profielen["csv_filename"] == "{}.csv".format(profile_name), "y_coord_hl"].iloc[0]
        length_foreshore = data_profielen.loc[data_profielen["csv_filename"] == "{}.csv".format(profile_name), "length_fs"].iloc[0]
        length_hinterland = data_profielen.loc[data_profielen["csv_filename"] == "{}.csv".format(profile_name), "length_hl"].iloc[0]
        # create a line from the foreshore to the hinterland
        line_x = interp1d([-length_foreshore, length_hinterland], [x_fs, x_hl])
        # find where the x_teen is on the line
        x_teen_coord = line_x(x_teen)
        if not np.isnan(x_teen_coord):
            # create a line from the foreshore point to the hinterland point
            line_y = interp1d([x_fs, x_hl], [y_fs, y_hl])
            # find the y_teen_coord on the line that corresponds to the x_teen_coord
            y_teen_coord = line_y(x_teen_coord)
            # add the profile name, coordinates and profile_number to the df_binnenteen using pd.concat
            df_binnenteen = pd.concat([df_binnenteen, pd.DataFrame({"Name": [profile_name],
                                                                    "coordinates": [Point(float(x_teen_coord),
                                                                                          float(y_teen_coord))],
                                                                    "profile_number": [profile_number]})])

    # sort the df_binnenteen by profile_number in ascending order
    df_binnenteen = df_binnenteen.sort_values(by="profile_number", ascending=True)

    # write a line to geojson, with LineString(df_binnenteen["coordinates"]) as geometry and with coordinatesystem EPSG:28992
    d = {"geometry": LineString(df_binnenteen["coordinates"]), "properties": {"Name": "binnenteenlijn"}}

    # write binnenteenlijn to geojson, with coordinatesystem EPSG:28992
    gdf = geopandas.GeoDataFrame(d, crs="EPSG:28992")
    gdf.to_json()
    gdf.to_file(output_dir.joinpath("teenlijn.geojson"), driver="GeoJSON")

if __name__ == "__main__":
    # Path(r'c:\VRM\Gegevens 38-1\dijkinfo')
    # characteristic_profile_dir is where the characteristic profiles (both CSV and PNG) are stored
    characteristic_profile_dir = Path(r'c:\VRM\Gegevens 38-1\dijkinfo\characteristic_profiles')
    profile_path = Path(r'c:\VRM\Gegevens 38-1\dijkinfo\traject_profiles.csv')
    output_dir = Path(r"c:\VRM\Gegevens 38-1\dijkinfo\teenlijn")
    derive_teenlijn(characteristic_profile_dir,
                    profile_path,
                    output_dir)