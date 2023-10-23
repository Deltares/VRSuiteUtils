from pathlib import Path
import pandas as pd
import os
from preprocessing.step2_mechanism_data.revetments.qvariant import revetment_qvariant

def qvariant_main(traject_id: str, bekleding_path: Path, database_path: Path, waterlevel_path: Path, profielen_path: Path,
                     hring_path: Path, output_path: Path):

    # if output_path doesnot exist, create it, with subfolders for the figures and temporary files
    if not output_path.exists():
        output_path.joinpath('figures_ZST').mkdir(parents=True, exist_ok=False)
        output_path.joinpath('figures_GEBU').mkdir(parents=True, exist_ok=False)
        output_path.joinpath('temp').mkdir(parents=True, exist_ok=False)
        print("output folders created")
    # elif output_path exists, but not empty, stop the script
    elif output_path.exists() and len(list(output_path.iterdir())) == 0:
        output_path.joinpath('figures_ZST').mkdir(parents=True, exist_ok=False)
        output_path.joinpath('figures_GEBU').mkdir(parents=True, exist_ok=False)
        output_path.joinpath('temp').mkdir(parents=True, exist_ok=False)
        print("output folders created")
    elif output_path.exists() and len(list(output_path.iterdir())) != 0:
        #check if the length of iterdir is 3
        if len(list(output_path.iterdir())) == 3:
            #check if the stems of the two subfolders are figures_ZST and figures_GEBU (in random order)
            if 'figures_ZST' in [x.stem for x in list(output_path.iterdir())] and 'figures_GEBU' in [x.stem for x in list(output_path.iterdir())] and 'temp' in [x.stem for x in list(output_path.iterdir())]:
                #ensure figures folders are empty (temporary folder can be filled)
                if len(list(output_path.joinpath('figures_ZST').iterdir())) == 0 and len(list(output_path.joinpath('figures_GEBU').iterdir())) == 0:
                    pass
                else:
                    print('The output folder is not empty. Please empty the folder and run the script again.')
                    exit()
            else:
                print('The output folder is not empty. Please empty the folder and run the script again.')
                exit()
        else:
            print('The output folder is not empty. Please empty the folder and run the script again.')
            exit()

    local_path = output_path.joinpath('temp')
    # read bekleding csv
    df = pd.read_csv(bekleding_path,
                     usecols=['doorsnede', 'dwarsprofiel','naam_hrlocatie', 'hrlocation', 'hr_koppel', 'region', 'gws',
                              'getij_amplitude', 'steentoetsfile', 'prfl', 'begin_grasbekleding', 'waterstand_stap'],dtype={'doorsnede': str, 'dwarsprofiel': str})
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
    revetment_qvariant(df, profielen_path, database_path, waterlevel_path, hring_path, output_path,local_path, p_grid)


if __name__ == '__main__':

    # input paths
    traject_id = "31-1"
    bekleding_path = Path(r"c:\vrm_test\scheldestromen_bekleding\Bekleding_default.csv")
    database_path = Path(r"c:\vrm_test\scheldestromen_bekleding\Databases\V3_WBI2017")
    profielen_path = Path(r"c:\vrm_test\scheldestromen_bekleding\prfl")
    waterlevel_path = Path(r"c:\vrm_test\scheldestromen_bekleding\waterlevel_20230925")
    output_path = Path(r"c:\vrm_test\scheldestromen_bekleding\uitvoer_full")
    hring_path = Path(os.path.dirname(os.path.realpath(__file__))).parent.parent.joinpath('externals', 'HydraRing-23.1.1')

    qvariant_main(traject_id, bekleding_path, database_path, waterlevel_path, profielen_path, hring_path, output_path)
