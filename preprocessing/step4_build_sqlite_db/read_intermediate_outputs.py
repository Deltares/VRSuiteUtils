import copy

import pandas as pd
import numpy as np
import json
import warnings
from vrtool.probabilistic_tools.hydra_ring_scripts import read_design_table


def read_waterlevel_data(files_dir):
    # create dict with dirs as keys for subdirs in files_path
    # and files as values for files in subdirs
    # files should be in the following structure: year_directory\location_directory\location_file.txt
    waterlevel_data = pd.DataFrame(
        columns=["WaterLevelLocationId", "Year", "WaterLevel", "Beta"]
    )
    for year_dir in files_dir.iterdir():
        if year_dir.is_dir():
            for loc_dir in year_dir.iterdir():
                if loc_dir.is_dir():
                    for loc_file in loc_dir.iterdir():
                        if (loc_file.is_file()) and (loc_file.stem.lower().startswith("designtable")) and (loc_file.suffix.lower() == ".txt"):
                            design_table = read_design_table(loc_file)
                            table_data = pd.DataFrame(
                                {
                                    "WaterLevelLocationId": [loc_dir.stem]
                                    * design_table.shape[0],
                                    "Year": [year_dir.name] * design_table.shape[0],
                                    "WaterLevel": list(design_table["Value"]),
                                    "Beta": list(design_table["Beta"]),
                                }
                            )
                            waterlevel_data = pd.concat(
                                (waterlevel_data, table_data), ignore_index=True
                            )
    return waterlevel_data


def read_overflow_data(files_dir):
    # create dict with dirs as keys for subdirs in files_path
    # and files as values for files in subdirs
    overflow_data = pd.DataFrame(columns=["LocationId", "Year", "CrestHeight", "Beta"])
    for year_dir in files_dir.iterdir():
        if year_dir.is_dir():
            for loc_dir in year_dir.iterdir():
                if loc_dir.is_dir():
                    for loc_file in loc_dir.iterdir():
                        if (loc_file.is_file()) and (loc_file.stem.lower().startswith("designtable")) and (loc_file.suffix.lower() == ".txt"):
                            design_table = read_design_table(loc_file)
                            table_data = pd.DataFrame(
                                {
                                    "LocationId": [loc_dir.stem] * design_table.shape[0],
                                    "Year": [year_dir.name] * design_table.shape[0],
                                    "CrestHeight": list(design_table["Value"]),
                                    "Beta": list(design_table["Beta"]),
                                }
                            )
                            overflow_data = pd.concat(
                                (overflow_data, table_data), ignore_index=True
                            )
    overflow_data = overflow_data.set_index("LocationId")
    return overflow_data


def read_piping_data(file_path):
    return pd.read_csv(
        file_path,
        index_col=0,
        usecols=[
            "doorsnede",
            "scenario",
            "scenariokans",
            "wbn",
            "polderpeil",
            "d_wvp",
            "d70",
            "d_cover",
            "h_exit",
            "r_exit",
            "l_voor",
            "l_achter",
            "k",
            "gamma_sat",
            "kwelscherm",
            "dh_exit",
            "pf_s",
        ],
        dtype={"doorsnede": str, "scenario": int},
    )


def read_stability_data(file_path):
    return pd.read_csv(
        file_path,
        index_col=0,
        usecols=[
            "doorsnede",
            "scenario",
            "scenarionaam",
            "scenariokans",
            "SF",
            "beta",
            "stixnaam",
            "deklaagdikte",
            "pleistoceendiepte",
        ],
        dtype={'doorsnede': str, 'scenario': int, 'stixnaam': str, 'beta':float, 'deklaagdikte': float, 'pleistoceendiepte': float},
    )

def read_revetment_data(files_dir):

    slope_part_table = {"location": list(), "slope_part": list(), "begin_part": list(), "end_part": list(), "top_layer_thickness": list(), "top_layer_type": list(), "tan_alpha": list()}
    rel_GEBU_table = {"location": list(), "year": list(), "transition_level": list(), "beta": list()}
    rel_ZST_table = {"location": list(), "slope_part": list(), "year": list(), "top_layer_thickness": list(), "beta": list()}

    for year_dir in files_dir.iterdir():
        if year_dir.is_dir():
            for loc_file in year_dir.iterdir():
                if loc_file.is_file():

                    location = str(loc_file.name.split("_")[1])
                    with open(loc_file, "r") as openfile:
                        json_object = json.load(openfile)
                    
                    if "GEBU" in loc_file.name: # read data for grass revetment
                        lenn = len(json_object["grasbekleding_begin"])
                        rel_GEBU_table["location"] += [location] * lenn
                        rel_GEBU_table["year"] += [int(year_dir.name)] * lenn
                        rel_GEBU_table["transition_level"] += json_object["grasbekleding_begin"]
                        rel_GEBU_table["beta"] += json_object["betaFalen"]

                    if "ZST" in loc_file.name: # read data for block revetment
                        if "2025" in loc_file.name: # slope data only one time
                            slope_part_table["location"] += [location] * json_object["aantal deelvakken"]
                            slope_part_table["slope_part"] += list(np.arange(0, json_object["aantal deelvakken"], 1))
                            slope_part_table["begin_part"] += json_object["Zo"]
                            slope_part_table["end_part"] += json_object["Zb"]
                            slope_part_table["top_layer_thickness"] += json_object["D huidig"]
                            slope_part_table["top_layer_type"] += json_object["toplaagtype"]
                            slope_part_table["tan_alpha"] += json_object["tana"]

                        for i in range(0, json_object["aantal deelvakken"]):
                            if json_object["toplaagtype"][i]>=26.0 and json_object["toplaagtype"][i]<=27.9: # slope data with blok revetment
                                lenn = len(json_object[f"deelvak {i}"]["D_opt"])
                                rel_ZST_table["location"] += [location] * lenn
                                rel_ZST_table["slope_part"] += [i] * lenn
                                rel_ZST_table["year"] += [int(year_dir.name)] * lenn
                                rel_ZST_table["top_layer_thickness"] += json_object[f"deelvak {i}"]["D_opt"]
                                rel_ZST_table["beta"] += json_object[f"deelvak {i}"]["betaFalen"]

    return slope_part_table, rel_GEBU_table, rel_ZST_table

def read_bebouwing_data(file_path):
    return pd.read_csv(file_path, index_col=0)


def read_measures_data(file_path):
    return pd.read_csv(file_path, index_col=0)

def adjust_inner_toe(BIK, BIT, min_kerende_hoogte):
    current_slope = (BIK.Z - BIT.Z) / (BIT.X - BIK.X)
    new_BIT = copy.deepcopy(BIT)
    new_BIT.Z = BIK.Z - min_kerende_hoogte
    new_BIT.X = BIT.X + min_kerende_hoogte/current_slope
    return new_BIT
def read_profile_data(file_path, min_kerende_hoogte = 2.01):
    """reads a single csv file with profiles for each section into a dataframe"""
    profile_df = pd.read_csv(file_path,index_col=0, header = [0,1])
    kerende_hoogte = np.subtract(profile_df[('BIK','Z')], profile_df[('BIT','Z')])
    for count, row in profile_df.iterrows():
        if kerende_hoogte.loc[count] <=2.0:
            #TODO temporary fix to enable running for sections with low lerende hog
            if np.isnan(row[('EBL','Z')]):
                new_BIT = adjust_inner_toe(row.BIK, row.BIT, min_kerende_hoogte)
                profile_df.loc[count,('BIT','X')] = new_BIT.X
                profile_df.loc[count,('BIT','Z')] = new_BIT.Z
                warnings.warn('Kerende hoogte voor profiel {} is kleiner dan 2m. BIT is aangepast zodat deze gelijk is aan 2 meter'.format(count))
    return profile_df

def read_profiles_old(files_dir):
    "Deprecated file format still used for tests"
    profile_data = pd.DataFrame(
        columns=["vaknaam", "CharacteristicPoint", "x", "z"]
    )
    for profile_file in files_dir.iterdir():
        profile_name = profile_file.stem
        profile = pd.read_csv(profile_file, index_col=0)
        profile_points = pd.DataFrame(
            {
                "vaknaam": [profile_name] * profile.shape[0],
                "CharacteristicPoint": list(profile.index),
                "x": list(profile.x),
                "z": list(profile.z),
            }
        )
        profile_data = pd.concat((profile_data, profile_points), ignore_index=True)
    return profile_data
    # return pd.read_csv(file_path,index_col=0)
