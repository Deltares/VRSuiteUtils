from pathlib import Path
import pandas as pd
import os
from preprocessing.step2_mechanism_data.revetments.GEBU_prep_relatie import revetment_gebu
from preprocessing.step2_mechanism_data.revetments.ZST_prep_relatie import revetment_zst
import shutil
def gebu_zst_main(traject_id, bekleding_path: Path, steentoets_path: Path, profielen_path: Path, binDIKErnel: Path, output_path: Path):

    # check if output_path exists:
    if output_path.exists():
        print("output folder exists. Great, we move on")
        # check if figures and temp folders exist:
        if not output_path.joinpath('figures_GEBU').exists():
            # make figures_GEBU folder
            output_path.joinpath('figures_GEBU').mkdir(parents=True, exist_ok=False)
            print("figures_GEBU folder created")
        if not output_path.joinpath('figures_ZST').exists():
            # make figures_ZST folder
            output_path.joinpath('figures_ZST').mkdir(parents=True, exist_ok=False)
            print("figures_ZST folder created")
        if not output_path.joinpath('temp').exists():
            # make temp folder
            output_path.joinpath('temp').mkdir(parents=True, exist_ok=False)
            print("temp folder created")
    else:
        print("output folder does not exist. Check if the path is correct. Refer to folder with qvariant output.")
        exit()

    figures_GEBU = output_path.joinpath('figures_GEBU')
    figures_ZST = output_path.joinpath('figures_ZST')
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

    # run functions
    # step 2: GEBU
    revetment_gebu(df, profielen_path, output_path, binDIKErnel, figures_GEBU, local_path, p_grid)

    # step 3: ZST
    revetment_zst(df, profielen_path, steentoets_path, output_path, figures_ZST, p_grid)

    # remove all files in local_path using shutil
    shutil.rmtree(local_path)


if __name__ == '__main__':

    # input paths
    traject_id = "31-1"
    bekleding_path = Path(r"c:\vrm_test\scheldestromen_bekleding\Bekleding_default.csv")
    steentoets_path = Path(r"c:\vrm_test\scheldestromen_bekleding\ZST_bestanden")
    profielen_path = Path(r"c:\vrm_test\scheldestromen_bekleding\prfl")
    bindikernel = Path(__file__).parent.absolute().parent.parent.joinpath('externals', 'DiKErnel')
    output_path = Path(r"c:\vrm_test\scheldestromen_bekleding\uitvoer_full")

    gebu_zst_main(traject_id, bekleding_path, steentoets_path, profielen_path, bindikernel, output_path)
