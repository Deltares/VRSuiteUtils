import pandas as pd
from vrtool.probabilistic_tools.hydra_ring_scripts import read_design_table
def read_waterlevel_data(files_path):
    # create dict with dirs as keys for subdirs in files_path
    # and files as values for files in subdirs
    waterlevel_data = pd.DataFrame(columns=['WaterLevelLocationId','Year','WaterLevel','Beta'])
    for year_dir in files_path.iterdir():
        if year_dir.is_dir():
            for loc_file in year_dir.iterdir():
                if loc_file.is_file():
                    design_table = read_design_table(loc_file)
                    table_data = pd.DataFrame({'WaterLevelLocationId': [loc_file.stem.split('_')[1]] * design_table.shape[0],
                                  'Year': [year_dir.name] * design_table.shape[0],
                                  'WaterLevel': list(design_table['Value']),
                                  'Beta': list(design_table['Beta'])})
                    waterlevel_data = pd.concat((waterlevel_data, table_data),ignore_index=True)
    return waterlevel_data


def read_overflow_data(files_path):
    # create dict with dirs as keys for subdirs in files_path
    # and files as values for files in subdirs
    overflow_data = pd.DataFrame(columns=['LocationId','Year','WaterLevel','Beta'])
    for year_dir in files_path.iterdir():
        if year_dir.is_dir():
            for loc_file in year_dir.iterdir():
                if loc_file.is_file():
                    design_table = read_design_table(loc_file)
                    table_data = pd.DataFrame({'LocationId': [loc_file.stem] * design_table.shape[0],
                                  'Year': [year_dir.name] * design_table.shape[0],
                                  'CrestHeight': list(design_table['Value']),
                                  'Beta': list(design_table['Beta'])})
                    overflow_data = pd.concat((overflow_data,table_data),ignore_index=True)
    overflow_data = overflow_data.set_index('LocationId')
    return overflow_data

def read_piping_data(file_path):
    return pd.read_csv(file_path,index_col=0,usecols = ['dwarsprofiel','scenario','scenariokans','wbn','polderpeil','d_wvp','d70','d_cover','h_exit',
                                                        'r_exit','l_voor','l_achter','k','gamma_sat','kwelscherm','dh_exit','pf_s'], dtype={'dwarsprofiel': str,'scenario':int})

def read_stability_data(file_path):
    return pd.read_csv(file_path,index_col=0,usecols=['doorsnede', 'scenario', 'scenarionaam', 'scenariokans', 'SF', 'beta',
                                                      'stixnaam','deklaagdikte', 'pleistoceendiepte'])
def read_bebouwing_data(file_path):
    return pd.read_csv(file_path,index_col=0)

def read_measures_data(file_path):
    return pd.read_csv(file_path,index_col=0)

def read_profilepoints_data(files_path):
    profile_data = pd.DataFrame(columns=['ProfileName','CharacteristicPoint','x','z'])
    for profile_file in files_path.iterdir():
        profile_name = profile_file.stem
        profile = pd.read_csv(profile_file,index_col=0)
        profile_points = pd.DataFrame({'ProfileName': [profile_name] * profile.shape[0],
                                  'CharacteristicPoint': list(profile.index),
                                  'x': list(profile.x),
                                  'z': list(profile.z)})
        profile_data = pd.concat((profile_data,profile_points),ignore_index=True)
    return profile_data
    # return pd.read_csv(file_path,index_col=0)