from pathlib import Path
import geopandas as gpd
import pandas as pd
import warnings
def main_profiel_selectie(
        vakindeling_geojson: Path,
        karakteristieke_profielen: Path,
        profiel_info_csv: Path,
        uitvoer_map: Path,
        invoerbestand: Path,
        selectiemethode: str):
    #load vakindeling_geojson
    vakindeling = gpd.read_file(vakindeling_geojson)

    #load profiel info
    profiel_info = pd.read_csv(profiel_info_csv)

    if invoerbestand:
        #load invoerbestand
        invoerbestand = pd.read_csv(invoerbestand)


    #for each vak in vakindeling
    for vak in vakindeling.itertuples():
        #select profielen
        if invoerbestand:
            #if a profile is given in invoerbestand then use that one
            pass    #TODO develop this
        else:
            #select profielen based on geometry
            available_profiles = profiel_info.loc[(profiel_info.m_value > vak.m_start) & (profiel_info.m_value < vak.m_eind)]
            select_profile(available_profiles, karakteristieke_profielen, vak.vaknaam, selectiemethode)
        #save profielen to file

def compute_slope(point1, point2):
    #point1 and point2 are tuples of x,y coordinates
    #compute slope between point1 and point2
    slope = (point2[1] - point1[1]) / (point2[0] - point1[0])
    return slope

def select_BUT(profile):
    possible_points = profile.loc[profile.name.str.contains('outer_slope')]
    start_point = 'BUK'
    if possible_points.empty:
        warnings.warn("No outer slope points found in profile. Use 1:3 slope with deltaZ = 4 meters")
        BUT = profile.loc[profile.name == 'BUK']
        BUT.X = BUT.X - 12
        BUT.Z = BUT.Z - 4
    elif possible_points.shape[0] == 1:
        BUT = possible_points
    else:
        slopes = []
        for point in possible_points.itertuples():
            #compute piecewise slope between start_point and point
            slopes.append(compute_slope((profile.loc[profile.name == start_point].X, profile.loc[profile.name == start_point].Z), (point.X, point.Z)))
            start_point = point.name
        #for now we take the first point (always)
        # TODO develop a more advanced rationale for selecting the outer slope point
        BUT = possible_points.iloc[0]
    return BUT
def select_inner_slope_points(profile):
    #select inner slope points BIT, BBL and EBL
    possible_points = profile.loc[profile.name.str.contains('inner_slope')]
    BIK = profile.loc[profile.name == 'BIK']
    #Is BIK correct, or are there points with similar Z in possible_points
    possible_alternative_BIK = possible_points.loc[BIK.Z.item() - possible_points.Z < 2]
    if len(possible_alternative_BIK) >0:
        #change the BIK to last point in possible_alternative_BIK, but adjust the height in accordance with the slope
        #TODO this is relevant in case of a tuimelkade. But the approach is very simplistic!
        new_BIK = possible_alternative_BIK.iloc[-1]
        point_idx = possible_points.loc[possible_points.name == new_BIK['name']].index + 1
        tan_inner = compute_slope((new_BIK.X, new_BIK.Z), (possible_points.loc[point_idx].X.item(), possible_points.loc[point_idx].Z.item()))
        dZ = BIK.Z - new_BIK.Z
        new_BIK.Z = new_BIK.Z + dZ.item()
        new_BIK.X = new_BIK.X + dZ.item() / tan_inner
        BIK = new_BIK

    #a berm should be at least 2 meters lower than the BIK
    possible_berm_points = possible_points.loc[possible_points.Z < BIK.Z - 2]
    if possible_berm_points.shape[0]== 1:
        #no berm, only BIT
        BIT = possible_berm_points.iloc[0]
        BBL = None
        EBL = None
    elif possible_berm_points.shape[0] == 2:
        #only 1 point, so no berm, which one is BIT?
        #TODO hier verder
        pass
    else:
        #we have a berm, so we have BIT, BBL and EBL
        #TODO hier verder
        pass

    return BIK, BIT, BBL, EBL
def define_characteristic_points(profile):
    #define characteristic points BUT, BIT, EBL, BBL
    characteristic_points = {}
    #Buitenteen BUT
    characteristic_points['BUT'] = select_BUT(profile)
    characteristic_points['BIK'], characteristic_points['BIT'],characteristic_points['BBL'],characteristic_points['EBL'] = select_inner_slope_points(profile)
    characteristic_points['BUK'] = profile.loc[profile.name == 'BUK'].squeeze()
    if characteristic_points['BBL'] is None or characteristic_points['EBL'] is None:
        #drop them from dict
        characteristic_points.pop('BBL')
        characteristic_points.pop('EBL')
    for point in characteristic_points.keys():
        characteristic_points[point] = characteristic_points[point].to_dict()

    #build a dataframe with the characteristic points
    characteristic_profile = pd.DataFrame.from_dict(characteristic_points).transpose()
    return characteristic_profile
def select_profile(available_profiles, karakteristieke_profielen, section, selectiemethode):
    profiles = []
    if available_profiles.empty:
        warnings.warn("No profiles found in available_profiles")
    elif available_profiles.shape[0] == 1:
        #only one profile found, use that one
        profiles.append(pd.read_csv(karakteristieke_profielen / f"{available_profiles.csv_filename.item()}"))
        warnings.warn(f"Slechts 1 profiel gevonden voor dijkvak {section}, dit profiel wordt gebruikt")
        characteristic_profile = define_characteristic_points(profiles[0])
    else:
        #read all profiles from csv files
        pass

        if selectiemethode == "minimum":
            #take profile with narrowest base
            pass
        elif selectiemethode == "median":
            pass
        elif selectiemethode == "gemiddeld":
            pass
        else:
            raise ValueError(f"selectiemethode {selectiemethode} is not known")

