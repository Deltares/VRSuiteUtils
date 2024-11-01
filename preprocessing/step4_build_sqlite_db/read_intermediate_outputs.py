import copy

import pandas as pd
import numpy as np
import json
import warnings
import os, glob
from pathlib import Path
from itertools import pairwise

from preprocessing.step2_mechanism_data.hydraring_computation import HydraRingComputation
from preprocessing.step2_mechanism_data.revetments.project_utils.functions_integrate import issteen

def read_design_table(filename: Path):
    import re

    values = []
    count = 0
    f = open(filename, "r")
    for line in f:
        if count == 0:
            headers = re.split("  +", line)[1:]
        else:
            val = re.split("  +", line)[1:]
            val = [i.replace("\n", "") for i in val]
            val = [float(i) for i in val]
            values.append(val)
        count += 1
    data = pd.DataFrame(values, columns=headers).rename(columns={"Beta\n": "Beta"})
    f.close()
    return data

def read_json(filename: Path):
    
    with open(filename, 'r') as openfile:
        json_object = json.load(openfile)

    return json_object

def read_waterlevel_data(files_dir, use_hydraring):
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
                        if use_hydraring:
                            if (loc_file.is_file()) and (loc_file.stem.lower().startswith("designtable")) and (loc_file.suffix.lower() == ".txt"):
                                design_table = read_design_table(loc_file)
                                # for now we still have to check it, in case users have made their Hydraring calculations with the older version
                                # in new version this will automatically be checked after Hydraring calculations, and this check here becomes redundant
                                design_table = HydraRingComputation().check_and_justify_HydraRing_data(design_table, calculation_type="Waterstand",
                                                                                                    section_name=loc_dir.name, design_table_file=loc_file)
                                table_data = pd.DataFrame(
                                    {
                                        "WaterLevelLocationId": [loc_dir.name]
                                        * design_table.shape[0],
                                        "Year": [year_dir.name] * design_table.shape[0],
                                        "WaterLevel": list(design_table["Value"]),
                                        "Beta": list(design_table["Beta"]),
                                    }
                                )
                        else:
                            if (loc_file.is_file()) and (loc_file.stem.lower().startswith("designtable")) and (loc_file.suffix.lower() == ".json"):
                                design_table = read_json(loc_file)

                                table_data = pd.DataFrame(
                                    {
                                        "WaterLevelLocationId": [loc_dir.name] * len(design_table["waterlevel"]["value"]),
                                        "Year": [year_dir.name] * len(design_table["waterlevel"]["value"]),
                                        "WaterLevel": list(design_table["waterlevel"]["value"]),
                                        "Beta": list(design_table["waterlevel"]["beta"]),      
                                    }
                                )

                        waterlevel_data = pd.concat(
                            (waterlevel_data, table_data), ignore_index=True
                        )
    return waterlevel_data


def read_overflow_data(files_dir, use_hydraring):
    # create dict with dirs as keys for subdirs in files_path
    # and files as values for files in subdirs
    overflow_data = pd.DataFrame(columns=["LocationId", "Year", "CrestHeight", "Beta"])
    for year_dir in files_dir.iterdir():
        if year_dir.is_dir():
            for loc_dir in year_dir.iterdir():
                if loc_dir.is_dir():
                    for loc_file in loc_dir.iterdir():
                        if use_hydraring:
                            if (loc_file.is_file()) and (loc_file.stem.lower().startswith("designtable")) and (loc_file.suffix.lower() == ".txt"):
                                design_table = read_design_table(loc_file)
                                # for now we still have to check it, in case users have made their Hydraring calculations with the older version
                                # in new version this will automatically be checked after Hydraring calculations, and this check here becomes redundant
                                design_table = HydraRingComputation().check_and_justify_HydraRing_data(design_table, calculation_type="Overflow",
                                                                                                    section_name=loc_dir.name, design_table_file=loc_file)

                                table_data = pd.DataFrame(
                                    {
                                        "LocationId": [loc_dir.name] * design_table.shape[0],
                                        "Year": [year_dir.name] * design_table.shape[0],
                                        "CrestHeight": list(design_table["Value"]),
                                        "Beta": list(design_table["Beta"]),
                                    }
                                )
                        else:
                            if (loc_file.is_file()) and (loc_file.stem.lower().startswith("designtable")) and (loc_file.suffix.lower() == ".json"):
                                design_table = read_json(loc_file)
                                
                                table_data = pd.DataFrame(
                                    {
                                        "LocationId": [loc_dir.name] * len(design_table["overflow"]["value"]),
                                        "Year": [year_dir.name] * len(design_table["overflow"]["value"]),
                                        "CrestHeight": list(design_table["overflow"]["value"]),
                                        "Beta": list(design_table["overflow"]["beta"]),
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
    try:
        dataset = pd.read_csv(
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
    except:
        dataset = pd.read_csv(
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
        ],
        dtype={'doorsnede': str, 'scenario': int, 'stixnaam': str, 'beta':float},
    )
    return dataset
def read_revetment_data(files_dir):

    slope_part_table = {"location": list(), "slope_part": list(), "begin_part": list(), "end_part": list(), "top_layer_thickness": list(), "top_layer_type": list(), "tan_alpha": list()}
    rel_GEBU_table = {"location": list(), "year": list(), "transition_level": list(), "beta": list()}
    rel_ZST_table = {"location": list(), "slope_part": list(), "year": list(), "top_layer_thickness": list(), "beta": list()}

    revetment_jsons = glob.glob(os.path.join(files_dir, "*.json"))
    for loc_file in revetment_jsons:
        loc_file = Path(loc_file)
        with open(loc_file, "r") as openfile:
            json_object = json.load(openfile)

        #split the name: format is MECH_LOC_YEAR.json but LOC can have _ in it
        mechanism = Path(loc_file).stem.split("_")[0]
        year = Path(loc_file).stem.split("_")[-1].strip('.json')	
        location = "_".join(Path(loc_file).stem.split("_")[1:-1])

        if mechanism == "GEBU": # read data for grass revetment
            lenn = len(json_object["grasbekleding_begin"])
            rel_GEBU_table["location"] += [location] * lenn
            rel_GEBU_table["year"] += [int(year)] * lenn
            rel_GEBU_table["transition_level"] += json_object["grasbekleding_begin"]
            rel_GEBU_table["beta"] += json_object["betaFalen"]

        if mechanism == "ZST": # read data for block revetment
            if year == "2100": # slope data only one time
                for i in range(0, json_object["aantal deelvakken"]):
                    if not np.isnan(json_object["toplaagtype"][i]):
                        slope_part_table["location"] += [location]
                        slope_part_table["slope_part"] += [i]
                        slope_part_table["begin_part"] += [json_object["Zo"][i]]
                        slope_part_table["end_part"] += [json_object["Zb"][i]]
                        if "D effectief" in json_object:
                            slope_part_table["top_layer_thickness"] += [json_object["D effectief"][i]]
                        else:
                            slope_part_table["top_layer_thickness"] += [json_object["D huidig"][i]]
                        slope_part_table["top_layer_type"] += [json_object["toplaagtype"][i]]
                        slope_part_table["tan_alpha"] += [json_object["tana"][i]]

            for i in range(0, json_object["aantal deelvakken"]):
                if issteen(json_object["toplaagtype"][i]): # slope data with blok revetment
                    lenn = len(json_object[f"deelvak {i}"]["D_opt"])
                    rel_ZST_table["location"] += [location] * lenn
                    rel_ZST_table["slope_part"] += [i] * lenn
                    rel_ZST_table["year"] += [int(year)] * lenn
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
