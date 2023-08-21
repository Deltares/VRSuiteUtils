from pathlib import Path
import pandas as pd
import os
from preprocessing.step2_mechanism_data.revetments.qvariant import revetment_qvariant
from preprocessing.step2_mechanism_data.revetments.GEBU_prep_relatie import revetment_gebu
from preprocessing.step2_mechanism_data.revetments.ZST_prep_relatie import revetment_zst
from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape

def bekleding_main(bekleding_path: Path, database_path: Path, steentoets_path: Path, profielen_path: Path,
                     hring_path: Path, binDIKErnel: Path, output_path: Path):

    local_path = Path(os.path.dirname(__file__))

    # if output_path doesnot exist, create it, with subfolders for the figures
    if not output_path.exists():
        output_path.joinpath('figures_ZST').mkdir(parents=True, exist_ok=False)
        output_path.joinpath('figures_GEBU').mkdir(parents=True, exist_ok=False)
    # elif output_path exists, but not empty, stop the script
    elif output_path.exists() and len(list(output_path.iterdir())) != 0:
        #check if the length of iterdir is 2
        if len(list(output_path.iterdir())) == 2:
            #check if the stems of the two subfolders are figures_ZST and figures_GEBU (in random order)
            if 'figures_ZST' in [x.stem for x in list(output_path.iterdir())] and 'figures_GEBU' in [x.stem for x in list(output_path.iterdir())]:
                #ensure they are empty
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

    figures_GEBU = output_path.joinpath('figures_GEBU')
    figures_ZST = output_path.joinpath('figures_ZST')

    # read bekleding csv
    df = pd.read_csv(bekleding_path,
                     usecols=['vaknaam', 'dwarsprofiel','HR_locatie', 'locationid', 'region', 'gws',
                              'getij_amplitude', 'steentoetsfile', 'prfl', 'begin_grasbekleding', 'waterstand_stap'])
    df = df.dropna(subset=['vaknaam'])  # drop rows where vaknaam is Not a Number
    df = df.reset_index(drop=True)  # reset index

    #set default Q-variant probability grid:
    #get signaleringswaarde from NBPW
    traject_object = TrajectShape('30-1')
    traject_object.get_traject_shape_from_NBPW()

    p_grid = [1./30,
                   1./traject_object.ondergrens,
                   1./traject_object.signaleringswaarde,
                   1./(traject_object.signaleringswaarde/1000)]

    # run functions
    # step 1: qvariant
    revetment_qvariant(df, profielen_path, database_path, waterlevel_path, hring_path, output_path,p_grid)

    # step 2: GEBU
    revetment_gebu(df, profielen_path, output_path, binDIKErnel, figures_GEBU, local_path, p_grid)

    # step 3: ZST
    revetment_zst(df, steentoets_path, output_path, figures_ZST)

    # get the path where this script is in


    # cleanup files
    files = [local_path.parent.joinpath("step2_mechanism_data", "revetments", "project_utils", "input.json"),
             local_path.parent.joinpath("step2_mechanism_data", "revetments", "1.ini"),
             local_path.parent.joinpath("step2_mechanism_data", "revetments", "1.sql"),
             local_path.parent.joinpath("step2_mechanism_data", "revetments", "1-input.txt"),
             local_path.parent.joinpath("step2_mechanism_data", "revetments", "1-output.sqlite"),
             local_path.parent.joinpath("step2_mechanism_data", "revetments", "1-output.txt"),
             local_path.parent.joinpath("step2_mechanism_data", "revetments", "combin.sqlite"),
             local_path.parent.joinpath("step2_mechanism_data", "revetments", "designTable.txt"),
             local_path.parent.joinpath("step2_mechanism_data", "revetments", "hydraring.log")]


    # remove files
    for file in files:
        # if file exists: remove it
        if (file).exists():
            (file).unlink()


if __name__ == '__main__':

    # input paths
    input_csv = Path(r"c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_HWBP\test_bekledingen\Bekleding_default.csv")
    database_path = Path(r"c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_HWBP\test_bekledingen\database\WBI2017_Oosterschelde_26-3_v02")

    steentoets_path = Path(r"c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_HWBP\test_bekledingen\steentoets")
    profielen_path = Path(r"c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_HWBP\test_bekledingen\profielen")
    waterlevel_path = Path(r"c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_HWBP\test_bekledingen\input_waterlevel")
    # figures_gebu = Path(r"c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_HWBP\test_bekledingen\figures_GEBU_test_CLI")
    # figures_zst = Path(r"c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_HWBP\test_bekledingen\figures_ZST_test_CLI")
    output_path = Path(r"c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_HWBP\test_bekledingen\output_test_CLI")

    #these should become externals
    hring_path = Path(r"c:\Repositories\VRSuite\Preprocessing\VrToolPreprocess\externals\HydraRing 23.1.1")
    bin_dikernel = Path(r"c:\Repositories\VRSuite\Preprocessing\VrToolPreprocess\externals\DiKErnel")

    
    bekleding_main(input_csv, database_path, steentoets_path, profielen_path,
                   hring_path, bin_dikernel, output_path)
