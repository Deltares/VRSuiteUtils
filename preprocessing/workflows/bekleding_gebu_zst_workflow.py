from pathlib import Path
import pandas as pd
import os
from preprocessing.step2_mechanism_data.revetments.GEBU_prep_relatie import revetment_gebu
from preprocessing.step2_mechanism_data.revetments.ZST_prep_relatie import revetment_zst
from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape
import shutil
def gebu_zst_main(bekleding_path: Path, steentoets_path: Path, profielen_path: Path, binDIKErnel: Path, output_path: Path):

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

    #set default Q-variant probability grid:
    #get signaleringswaarde from NBPW
    traject_object = TrajectShape('30-1')
    traject_object.get_traject_shape_from_NBPW()

    p_grid = [1./30,
                   1./traject_object.ondergrens,
                   1./traject_object.signaleringswaarde,
                   1./(traject_object.signaleringswaarde*1000)]

    # run functions
    # step 2: GEBU
    # revetment_gebu(df, profielen_path, output_path, binDIKErnel, figures_GEBU, local_path, p_grid)

    # step 3: ZST
    revetment_zst(df, steentoets_path, output_path, figures_ZST, p_grid)

    # remove all files in local_path using shutil
    shutil.rmtree(local_path)


if __name__ == '__main__':

    # input paths
    bekleding_path = Path(r"c:\vrm_test\bekleding_split_workflow\Bekleding_20230830_full_batch2.csv")
    steentoets_path = Path(r"c:\vrm_test\bekleding_split_workflow\steentoets")
    profielen_path = Path(r"c:\vrm_test\bekleding_split_workflow\PRFL")
    bindikernel = Path(__file__).parent.absolute().parent.parent.joinpath('externals', 'DiKErnel')
    output_path = Path(r"c:\vrm_test\bekleding_split_workflow\output2")

    gebu_zst_main(bekleding_path, steentoets_path, profielen_path, bindikernel, output_path)

    traject_object = TrajectShape('30-1')
    traject_object.get_traject_shape_from_NBPW()

    p_grid = [1./30,
                   1./traject_object.ondergrens,
                   1./traject_object.signaleringswaarde,
                   1./(traject_object.signaleringswaarde*1000)]