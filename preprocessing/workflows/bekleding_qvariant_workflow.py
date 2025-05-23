from pathlib import Path
import pandas as pd
import os
from preprocessing.step2_mechanism_data.revetments.qvariant import revetment_qvariant

def qvariant_main(traject_id: str, bekleding_path: Path, database_paths: list[Path], waterlevel_path: Path, profielen_path: Path,
                     hring_path: Path, output_path: Path):

    local_path = output_path.joinpath('temp')
    # if output_path doesnot exist, create it, with subfolder for tempfiles
    if not output_path.exists():
        local_path.mkdir(parents=True, exist_ok=False)
        print("output folder created")
    # elif output_path exists, but empty, continue
    elif not any(list(output_path.iterdir())):
        local_path.mkdir(parents=True, exist_ok=False)
        print("output folder created")
    #if anything in there: stop the script
    elif any(list(output_path.iterdir())):
        print('The output folder is not empty. Please empty the folder and run the script again.')
        exit()

    # read bekleding csv
    try:
        df = pd.read_csv(bekleding_path,
                     usecols=['doorsnede', 'dwarsprofiel','naam_hrlocatie', 'hrlocation', 'hr_koppel', 'region', 'gws',
                              'getij_amplitude', 'steentoetsfile', 'prfl', 'begin_bekleding','begin_grasbekleding', 'waterstand_stap'],dtype={'doorsnede': str, 'dwarsprofiel': str})
    except: #older format
        df = pd.read_csv(bekleding_path,
                     usecols=['doorsnede', 'dwarsprofiel','naam_hrlocatie', 'hrlocation', 'hr_koppel', 'region', 'gws',
                              'getij_amplitude', 'steentoetsfile', 'prfl','begin_grasbekleding', 'waterstand_stap'],dtype={'doorsnede': str, 'dwarsprofiel': str})
        df['begin_bekleding'] = df['gws']

    df = df.dropna(subset=['doorsnede'])  # drop rows where vaknaam is Not a Number
    df = df.reset_index(drop=True)  # reset index

    # set default Q-variant probability grid:
    this_file_path = Path(os.path.dirname(os.path.realpath(__file__)))
    _generic_data_dir = this_file_path.absolute().parent.joinpath('generic_data')
    dike_info = pd.read_csv(_generic_data_dir.joinpath('diketrajectinfo.csv'))
    p_ondergrens = float(dike_info.loc[dike_info['traject_name'] == traject_id, ['p_max']].values[0])
    p_signaleringswaarde = float(dike_info.loc[dike_info['traject_name'] == traject_id, ['p_sig']].values[0])

    p_grid = [1. / 30,
              p_ondergrens,
              p_signaleringswaarde,
              p_signaleringswaarde * (1. / 1000.)]

    # step 1: qvariant
    revetment_qvariant(df, profielen_path, database_paths, waterlevel_path, hring_path, output_path,local_path, p_grid)
