from pathlib import Path
import pandas as pd
import os
from preprocessing.step2_mechanism_data.revetments.GEBU_prep_relatie import revetment_gebu
from preprocessing.step2_mechanism_data.revetments.ZST_prep_relatie import revetment_zst
from preprocessing.step2_mechanism_data.revetments.revetment_slope import RevetmentSlope


import shutil

def ensure_folders_exist(output_path: Path):
    #these folders will be used for output
    figures_GEBU = output_path.joinpath('figures_GEBU')
    figures_ZST = output_path.joinpath('figures_ZST')
    local_path = output_path.joinpath('temp')

    if not output_path.exists():
        print("output folder does not exist. Check if the path is correct. Refer to folder with qvariant output.")
        exit()
    #for path in list of figures_GEBU, figures_ZST and local_path, check if they exist. If not, create them.
    for output_folder in [figures_GEBU, figures_ZST, local_path]:
        if not output_folder.exists():
            output_folder.mkdir(parents=True, exist_ok=False)
        else:
            #remove and recreate the folder.
            shutil.rmtree(output_folder)
            output_folder.mkdir(parents=True, exist_ok=False)

def make_p_grid(traject_id: str):
    # set default Q-variant probability grid:
    dike_info = pd.read_csv(Path(__file__).parent.parent.joinpath('generic_data','diketrajectinfo.csv'))
    p_ondergrens = float(dike_info.loc[dike_info['traject_name'] == traject_id, ['p_max']].values[0])
    p_signaleringswaarde = float(dike_info.loc[dike_info['traject_name'] == traject_id, ['p_sig']].values[0])

    return [1. / 30,
              p_ondergrens,
              p_signaleringswaarde,
              p_signaleringswaarde * (1. / 1000.)]

def initialize_gebu_zst(output_path: Path, bekleding_path: Path, traject_id: str):
    # ensure output folders exist:
    ensure_folders_exist(output_path)

    # read bekleding csv
    df = pd.read_csv(bekleding_path,
                     usecols=['doorsnede', 'dwarsprofiel','naam_hrlocatie', 'hrlocation', 'hr_koppel', 'region', 'gws',
                              'getij_amplitude', 'steentoetsfile', 'prfl', 'begin_grasbekleding', 'waterstand_stap'],dtype={'doorsnede': str, 'dwarsprofiel': str})
    df = df.dropna(subset=['doorsnede'])  # drop rows where vaknaam is Not a Number
    df = df.reset_index(drop=True)  # reset index

    # make p_grid
    p_grid = make_p_grid(traject_id)

    return df, p_grid

def gebu_zst_main(traject_id, bekleding_path: Path, steentoets_path: Path, profielen_path: Path, binDIKErnel: Path, qvar_path: Path, output_path: Path):
    
    evaluate_years = [2023, 2100]
    
    # initialize folders & read bekleding csv
    df, p_grid = initialize_gebu_zst(output_path, bekleding_path, traject_id)

    # make cross sections
    cross_sections = [RevetmentSlope(profielen_path, data = row) for index, row in df.iterrows()]

    # run functions
    # step 2: GEBU
    revetment_gebu(cross_sections, qvar_path, output_path, binDIKErnel, output_path.joinpath('temp'), p_grid, evaluate_years)

    # step 3: ZST
    #add Steentoets data to cross_sections where available
    [cross_section.add_steentoets(steentoets_path) for cross_section in cross_sections if hasattr(cross_section, 'steentoetsfile')]
    
    #run the ZST computation
    revetment_zst(cross_sections, qvar_path, output_path, output_path.joinpath('figures_ZST'), p_grid, evaluate_years)

    # remove all files in local_path using shutil
    shutil.rmtree(output_path.joinpath('temp'))

