from pathlib import Path
import pandas as pd
import os
from preprocessing.step2_mechanism_data.revetments.qvariant import revetment_qvariant
from preprocessing.step2_mechanism_data.revetments.GEBU_prep_relatie import revetment_gebu
from preprocessing.step2_mechanism_data.revetments.ZST_prep_relatie import revetment_zst
from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape
import shutil
def bekleding_main(input_csv_path: Path, database_path: Path, waterlevel_path: Path, steentoets_path: Path, profielen_path: Path,
                     hring_path: Path, binDIKErnel: Path, output_path: Path):



    # if output_path doesnot exist, create it, with subfolders for the figures and temporary files
    if not output_path.exists():
        output_path.joinpath('figures_ZST').mkdir(parents=True, exist_ok=False)
        output_path.joinpath('figures_GEBU').mkdir(parents=True, exist_ok=False)
        output_path.joinpath('temp').mkdir(parents=True, exist_ok=False)
    # elif output_path exists, but not empty, stop the script
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

    figures_GEBU = output_path.joinpath('figures_GEBU')
    figures_ZST = output_path.joinpath('figures_ZST')
    local_path = output_path.joinpath('temp')
    # read bekleding csv
    df = pd.read_csv(input_csv_path,
                     usecols=['doorsnede', 'dwarsprofiel','naam_hrlocatie', 'locationid', 'hr_koppel', 'region', 'gws',
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
    # step 1: qvariant
    revetment_qvariant(df, profielen_path, database_path, waterlevel_path, hring_path, output_path,local_path,p_grid)

    # step 2: GEBU
    revetment_gebu(df, profielen_path, output_path, binDIKErnel, figures_GEBU, local_path, p_grid)

    # step 3: ZST
    revetment_zst(df, steentoets_path, output_path, figures_ZST, p_grid)

    # remove all files in local_path using shutil
    shutil.rmtree(local_path)



if __name__ == '__main__':

    # input paths
    input_csv = Path(r"c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_HWBP\00_testwerk\test_bekledingen\Bekleding_default.csv")
    database_path = Path(r"c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_HWBP\00_testwerk\test_bekledingen\database\WBI2017_Oosterschelde_26-3_v02")

    steentoets_path = Path(r"c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_HWBP\00_testwerk\test_bekledingen\steentoets")
    profielen_path = Path(r"c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_HWBP\00_testwerk\test_bekledingen\profielen")
    waterlevel_path = Path(r"c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_HWBP\00_testwerk\test_bekledingen\input_waterlevel")

    output_path = Path(r"c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_HWBP\00_testwerk\test_bekledingen\output_test_CLI4")

    hring_path = Path(r"c:\Repositories\VRSuite\Preprocessing\VrToolPreprocess\externals\HydraRing 23.1.1")
    bin_dikernel = Path(r"c:\Repositories\VRSuite\Preprocessing\VrToolPreprocess\externals\DiKErnel")

    
    bekleding_main(input_csv, database_path, waterlevel_path, steentoets_path, profielen_path,
                   hring_path, bin_dikernel, output_path)
