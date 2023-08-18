from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
import shutil
def main_profiel_selectie(
        vakindeling_geojson: Path,
        ahn_profielen: Path,
        karakteristieke_profielen: Path,
        profiel_info_csv: Path,
        uitvoer_map: Path,
        invoerbestand: Path,
        selectiemethode: str):
    #make sure uitvoer_map does not exist: delete and recreate
    if uitvoer_map.exists():
        warnings.warn("uitvoer_map already exists. Deleting and recreating")
        #remove with shutil.rmtree
        shutil.rmtree(uitvoer_map)
    use_file = False
    uitvoer_map.mkdir()
    #load vakindeling_geojson
    vakindeling = gpd.read_file(vakindeling_geojson)

    #load profiel info
    profiel_info = pd.read_csv(profiel_info_csv)

    #check if invoerbestand is False or a Path that exists
    if invoerbestand is not False:
        #load invoerbestand
        try:
            #vaknaam as index with dtype str
            custom_profiles = pd.read_csv(Path(invoerbestand),index_col=0, dtype={'vaknaam':str},header=[0,1])
            custom_profiles.index = custom_profiles.index.astype(str)
            use_file = True
        except:
            raise FileNotFoundError(f'Could not find invoerbestand {invoerbestand}')


    #for each vak in vakindeling
    for vak in vakindeling.itertuples():
        if vak.in_analyse == 0: #skip vakken die niet worden beschouwd
            continue

        #select profielen based on geometry
        available_profiles = profiel_info.loc[(profiel_info.m_value > vak.m_start) & (profiel_info.m_value < vak.m_eind)].copy()
        #drop non-existent profiles
        for idx, row in available_profiles.iterrows():
            if not karakteristieke_profielen.joinpath(row.csv_filename.split('.')[0] + '.png').exists():
                available_profiles.drop(index=idx, inplace=True)

        #select characteristic profile
        if use_file and vak.vaknaam in custom_profiles.index:
            #if a profile is given in invoerbestand then use that one
            characteristic_profile = profile_from_file(custom_profiles.loc[vak.vaknaam])
        else:
            characteristic_profile = select_profile(available_profiles, karakteristieke_profielen, vak.vaknaam, selectiemethode)

        #store result
        if characteristic_profile is not None:
            characteristic_profile.to_csv(uitvoer_map.joinpath(vak.vaknaam + '.csv'), index=True)
            #plot aggregated profile, and AHN data
            plot_profile(characteristic_profile, vak.vaknaam, available_profiles.csv_filename, ahn_profielen, uitvoer_map)
        else:
            plot_profile(None, vak.vaknaam, available_profiles.csv_filename, ahn_profielen, uitvoer_map)
            warnings.warn(f'No profile found for vak {vak.vaknaam}')

def profile_from_file(profile):
    #profile is a row from the custom_profiles dataframe
    #drop the nans
    profile = profile.dropna()
    #output df has profile index level_1 as index, and level 2 as columns
    idx = profile.index.get_level_values(0).unique().tolist()
    cols = profile.index.get_level_values(1).unique().tolist()
    characteristic_profile = pd.DataFrame(index=idx, columns=cols)
    for index, row in profile.items():

        characteristic_profile.loc[index] = row
    #make sure BUK.X = 0
    characteristic_profile.X = characteristic_profile.X - characteristic_profile.loc['BUK'].X
    return characteristic_profile
def plot_profile(profile, vaknaam : str, profile_names, ahn_path : Path, output_path : Path):

    fig, ax = plt.subplots()
    #plot ahn_profiles
    for profile_name in profile_names:
        ahn_profile = pd.read_csv(ahn_path.joinpath(profile_name),header=None).transpose()
        ax.plot(ahn_profile[0], ahn_profile[1], color='grey', alpha=0.5)
    #plot aggregated profile
    if profile is not None:
        ax.plot(profile.X, profile.Z, color='black')
    ax.set_title(vaknaam)
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Z [m+NAP]')
    # ax.set_aspect('equal')
    plt.savefig(output_path.joinpath(vaknaam + '.png'),dpi=300)
    plt.close()

def compute_slope(point1, point2):
    #point1 and point2 are tuples of x,y coordinates
    #compute slope between point1 and point2
    slope = (point2[1] - point1[1]) / (point2[0] - point1[0])
    if isinstance(slope, pd.Series):
        return slope.item()
    else:
        return slope

def select_BUT(profile):
    possible_points = profile.loc[profile.name.str.contains('outer_slope')].iloc[::-1]
    start_point = 'BUK'
    if possible_points.empty:
        warnings.warn("No outer slope points found in profile. Use 1:3 slope with deltaZ = 4 meters")
        BUT = profile.loc[profile.name == 'BUK']
        BUT.X = BUT.X - 12
        BUT.Z = BUT.Z - 4
    elif possible_points.shape[0] == 1:
        BUT = possible_points
    else:
        piecewise_slopes = []
        cumulated_slopes = []
        for point in possible_points.itertuples():
            #compute piecewise and cumulated slope between start_point and point
            piecewise_slopes.append(compute_slope((profile.loc[profile.name == start_point].X, profile.loc[profile.name == start_point].Z), (point.X, point.Z)))
            cumulated_slopes.append(compute_slope((profile.loc[profile.name == 'BUK'].X, profile.loc[profile.name == 'BUK'].Z), (point.X, point.Z)))
            start_point = point.name
        #filter points based on slope, the last point where the slope is 80% of the first part is assumed to be the BUT
        possible_points = possible_points.loc[np.array(cumulated_slopes) > 0.9*piecewise_slopes[0]]
        #
        # TODO develop a more advanced rationale for selecting the outer slope point
        BUT = possible_points.iloc[-1]
    return BUT.squeeze()
def select_inner_slope_points(profile):
    #select inner slope points BIT, BBL and EBL
    possible_points = profile.loc[profile.name.str.contains('inner_slope')]
    BIK = profile.loc[profile.name == 'BIK']
    #Is BIK correct, or are there points with similar Z in possible_points
    possible_alternative_BIK = possible_points.loc[BIK.Z.item() - possible_points.Z < 2]
    if (len(possible_alternative_BIK) >0) and (len(possible_points) > 1):
        #change the BIK to last point in possible_alternative_BIK, but adjust the height in accordance with the slope
        #simplistic approach for tuimelkades
        #the new_BIK is the last in possible_alternative_BIK but may not be the same as the last in possible_points
        if possible_alternative_BIK.index[-1] < max(possible_points.index):
            new_BIK = possible_alternative_BIK.iloc[-1].copy()
            point_idx = possible_points.loc[possible_points.name == new_BIK['name']].index + 1
        else:
            new_BIK = possible_alternative_BIK.iloc[-2].copy()
            point_idx = possible_points.loc[possible_points.name == new_BIK['name']].index + 1
        tan_inner = compute_slope((new_BIK.X, new_BIK.Z), (possible_points.loc[point_idx].X.item(), possible_points.loc[point_idx].Z.item()))
        dZ = BIK.Z - new_BIK.Z
        new_BIK.X = new_BIK.X + dZ.item() / tan_inner
        new_BIK.Z = new_BIK.Z + dZ.item()
        #check that new_BIk has larger X than old BIK
        if new_BIK.X < BIK.X.item():
            BIK = BIK.squeeze()
        else:
            BIK = new_BIK.squeeze()

    #a berm should be at least 2 meters lower than the BIK
    possible_berm_points = possible_points.loc[possible_points.Z < BIK.Z.item() - 2]
    if possible_berm_points.shape[0] <= 1:
        #no berm, only BIT


        BIT = possible_points.iloc[-1]
        BBL = None
        EBL = None
    elif possible_berm_points.shape[0] == 2:
        #2 points: we should determine what is the BIT, and whether the first point should be considered as a BBL/EBL (insteek)
        #determine difference in Z, if less than 1.5 meter, take the first point as BIT and no berm
        if possible_berm_points.iloc[0].Z - possible_berm_points.iloc[1].Z < 1.5:
            BIT = possible_berm_points.iloc[0]
            BBL = None
            EBL = None
        else:
            #we have a berm, so we have BIT, BBL and EBL
            BIT = possible_berm_points.iloc[1]
            BBL = possible_berm_points.iloc[0]
            EBL = possible_berm_points.iloc[0]
    elif possible_berm_points.shape[0] == 0:
        pass
    else:
        #we might have a berm, so we have BIT, BBL and EBL
        #if the slope between BIK and BBL is larger than that between the first and second point of possible_berm_points, then we have found the BBL
        first_slope = compute_slope((BIK.X, BIK.Z), (possible_berm_points.iloc[0].X, possible_berm_points.iloc[0].Z))
        second_slope = compute_slope((possible_berm_points.iloc[0].X, possible_berm_points.iloc[0].Z), (possible_berm_points.iloc[1].X, possible_berm_points.iloc[1].Z))
        if abs(first_slope) > abs(second_slope):
            BBL = possible_berm_points.iloc[0]
            EBL = possible_berm_points.iloc[1]
            remaining_points = possible_berm_points.iloc[2:]
            if remaining_points.shape[0]>1:
                #more than 2 points, so pick a sensible BIT
                pass
            else:
                BIT = remaining_points.iloc[0]
        else:
            #in this case the slope becomes steeper, so we have not found the berm yet. We should look further if possible
            #we assume that the last point is the BIT and there is noe EBL and BBL.
            #TODO shoudl this be more sophisticated?
            BIT = possible_berm_points.iloc[-1]
            BBL = None
            EBL = None
    return BIK, BIT, BBL, EBL
def define_characteristic_points(profile):
    #define characteristic points BUT, BIT, EBL, BBL
    characteristic_points = {}
    #Buitenteen BUT
    characteristic_points['BUT'] = select_BUT(profile)
    characteristic_points['BIK'], characteristic_points['BIT'],characteristic_points['BBL'],characteristic_points['EBL'] = select_inner_slope_points(profile)
    characteristic_points['BUK'] = profile.loc[profile.name == 'BUK']
    if characteristic_points['BBL'] is None or characteristic_points['EBL'] is None:
        #drop them from dict
        characteristic_points.pop('BBL')
        characteristic_points.pop('EBL')
    for point in characteristic_points.keys():
        characteristic_points[point] = characteristic_points[point].squeeze().to_dict()

    #build a dataframe with the characteristic points
    characteristic_profile = pd.DataFrame.from_dict(characteristic_points).transpose()

    #correct X coordinates such that BUK is at X=0
    characteristic_profile.X = characteristic_profile.X - characteristic_profile.loc['BUK'].X

    #order points as BUT, BUK, BIK, BBL, EBL, BIT (if present)
    if 'EBL' in characteristic_profile.index:
        characteristic_profile = characteristic_profile.reindex(['BUT', 'BUK', 'BIK', 'BBL', 'EBL', 'BIT'])
    else:
        characteristic_profile = characteristic_profile.reindex(['BUT', 'BUK', 'BIK', 'BIT'])
    return characteristic_profile

def filter_characteristic_profiles(characteristic_profiles, selectiemethode):
    #selectiemethode is nog nader in te vullen. Voor nu werken we o.b.v. mediane waarden.
    import matplotlib.pyplot as plt
    # for profile in characteristic_profiles:
    #     plt.plot(profile.X, profile.Z)
    # plt.plot(filtered_profile.X, filtered_profile.Z, '--or')
    # plt.show()
    filtered_profile = pd.DataFrame(columns=['X','Z'])
    all_characteristic_points = pd.concat(characteristic_profiles,
                                          keys = range(0,len(characteristic_profiles))).reset_index().set_index('level_1').rename(columns={'level_0':'Profielnummer'})
    profielnummers = list(range(0,len(characteristic_profiles)))
    outer_slope = np.empty((len(profielnummers),1))
    z_BUT = np.empty((len(profielnummers),1))
    #compute outer slope for each profielnummer
    for profiel in profielnummers:
        profile_points = all_characteristic_points.loc[all_characteristic_points.Profielnummer == profiel]
        outer_slope[profiel,0] = compute_slope((profile_points.loc['BUK'].X, profile_points.loc['BUK'].Z),
                        (profile_points.loc['BUT'].X, profile_points.loc['BUT'].Z))
        z_BUT[profiel,0] = profile_points.loc['BUT'].Z

    #buitentalud: mediane Z met mediane slope tussen BUT en BUK
    outer_slope = np.median(outer_slope)
    z_BUT = np.median(z_BUT)
    z_BUK = np.median(all_characteristic_points.loc['BUK'].Z)
    x_BUK = np.median(all_characteristic_points.loc['BUK'].X)
    x_BUT = x_BUK - (z_BUK - z_BUT) / outer_slope
    filtered_profile.loc['BUT',['X','Z']] = [x_BUT, z_BUT]
    filtered_profile.loc['BUK',['X','Z']] = [x_BUK, z_BUK]

    #binnenkruinlijn:
    #z is gelijk aan BUK
    #x is mediane BIK.X
    filtered_profile.loc['BIK',['X','Z']] = [np.median(all_characteristic_points.loc['BIK'].X), z_BUK]

    #binnentalud:
    inner_slope = np.empty((len(profielnummers),1))
    #mediane slope tussen BIK en BBL of BIT als BBL niet bestaat
    for profiel in profielnummers:
        profile_points = all_characteristic_points.loc[all_characteristic_points.Profielnummer == profiel]
        if 'BBL' in profile_points.index:
            inner_slope[profiel,0] = compute_slope((profile_points.loc['BIK'].X, profile_points.loc['BIK'].Z),
                        (profile_points.loc['BBL'].X, profile_points.loc['BBL'].Z))
        else:
            inner_slope[profiel,0] = compute_slope((profile_points.loc['BIK'].X, profile_points.loc['BIK'].Z),
                        (profile_points.loc['BIT'].X, profile_points.loc['BIT'].Z))
    inner_slope = np.median(inner_slope)
    z_BIT = np.median(all_characteristic_points.loc['BIT'].Z)

    #als er helemaal nergens een berm zit, leidt dan direct BIT af a.d.h.v. de mediane slope tussen BIK en BIT
    if 'BBL' not in all_characteristic_points.index:
        x_BIT = filtered_profile.loc['BIK','X'] +  (z_BIT - filtered_profile.loc['BIK','Z'])/inner_slope
        # z_BIT = z_BUK - inner_slope * (x_BUK - np.median(all_characteristic_points.loc['BIK'].X))
        filtered_profile.loc['BIT',['X','Z']] = [x_BIT, z_BIT]
    else:
        #als er profielen zijn met een berm laten we het afhangen van de mediane X van BIT of er nog een berm tussen moet worden gevoegd
        #eerst de x_BIT als er geen berm tussen zit, obv de mediane slope tussen BIK en BIT
        x_BIT_no_berm = filtered_profile.loc['BIK','X'] +  (z_BIT - filtered_profile.loc['BIK','Z'])/inner_slope
        #dan de werkelijke x_BIT
        x_BIT = np.median(all_characteristic_points.loc['BIT'].X)
        #verschil is de berm lengte
        berm_lengte = x_BIT - x_BIT_no_berm
        #case 1: berm_lengte groter dan 2 meter:
        if berm_lengte > 2:
            #de bermhoogte:
            z_BBL = np.median(all_characteristic_points.loc[['BBL']].Z)
            z_EBL = np.median(all_characteristic_points.loc[['EBL']].Z)
            #TODO schuine berm o.b.v. talud tussen EBL en BBL
            #de x van BBL o.b.v. de slope vanaf de BIK:
            x_BBL = filtered_profile.loc['BIK','X'] + (z_BBL - filtered_profile.loc['BIK','Z'])/inner_slope
            x_EBL = x_BBL + berm_lengte
            filtered_profile.loc['BBL',['X','Z']] = [x_BBL, z_BBL]
            filtered_profile.loc['EBL',['X','Z']] = [x_EBL, z_EBL]
            #mediane z_BIT voor profielen met een EBL
            profielnummers_met_berm = all_characteristic_points.loc[['EBL']]['Profielnummer'].values
            z_BIT = np.median(all_characteristic_points.loc[all_characteristic_points.Profielnummer.isin(profielnummers_met_berm)].loc['BIT'].Z)
            x_BIT = np.median(all_characteristic_points.loc[all_characteristic_points.Profielnummer.isin(profielnummers_met_berm)].loc['BIT'].X)
            filtered_profile.loc['BIT',['X','Z']] = [x_BIT, z_BIT]
        else:
            #geen berm, geen EBL BBL, BIT is gewoon BIT o.b.v. werkelijke BIT
            filtered_profile.loc['BIT',['X','Z']] = [x_BIT, z_BIT]
    # hoe breed is de basis?
    # hoe breed is de kruin?
    # hoe steil is het bovenste en onderste binnentalud?
    # moet er een berm in?

    return filtered_profile
def select_profile(available_profiles, karakteristieke_profielen, section, selectiemethode):
    profiles = []
    if available_profiles.empty:
        warnings.warn("No profiles found in available_profiles")
        return None
    # elif available_profiles.shape[0] == 1:
    #     #only one profile found, use that one
    #     profiles.append(pd.read_csv(karakteristieke_profielen / f"{available_profiles.csv_filename.item()}"))
    #     warnings.warn(f"Slechts 1 profiel gevonden voor dijkvak {section}, dit profiel wordt gebruikt")
    #     characteristic_profile = define_characteristic_points(profiles[0])
    else:
        characteristic_profiles = []
        for idx, profile in available_profiles.iterrows():
            profiles.append(pd.read_csv(karakteristieke_profielen / f"{profile.csv_filename}"))
            characteristic_profiles.append(define_characteristic_points(profiles[-1]))
        #read all profiles from csv files

    if len(profiles) > 1:
        characteristic_profile = filter_characteristic_profiles(characteristic_profiles, selectiemethode)

    else:
        characteristic_profile = characteristic_profiles[0]

    return characteristic_profile

