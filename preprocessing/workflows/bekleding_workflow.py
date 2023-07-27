from pathlib import Path
import pandas as pd

from preprocessing.step2_mechanism_data.revetments.qvariant import revetment_qvariant
from preprocessing.step2_mechanism_data.revetments.GEBU_prep_relatie import revetment_gebu
from preprocessing.step2_mechanism_data.revetments.ZST_prep_relatie import revetment_zst


def bekleding_main(bekleding_path: Path, database_path: Path, steentoets_path: Path, profielen_path: Path,
                     figures_GEBU: Path, figures_ZST: Path, hring_path: Path, binDIKErnel: Path, output_path: Path):

    # if output_path doesnot exist, create it
    if not output_path.exists():
        output_path.mkdir()
    # elif output_path exists, but not empty, stop the script
    elif output_path.exists() and len(list(output_path.iterdir())) != 0:
        print('The output folder is not empty. Please empty the folder and run the script again.')
        exit()

    # if figures_GEBU doesnot exist, create it
    if not figures_GEBU.exists():
        figures_GEBU.mkdir()
    # elif figures_GEBU exists, but not empty, stop the script
    elif figures_GEBU.exists() and len(list(figures_GEBU.iterdir())) != 0:
        print('The figure folder is not empty. Please empty the figures_GEBU folder and run the script again.')
        exit()

    # if figures_ZST doesnot exist, create it
    if not figures_ZST.exists():
        figures_ZST.mkdir()
    # elif figures_ZST exists, but not empty, stop the script
    elif figures_ZST.exists() and len(list(figures_ZST.iterdir())) != 0:
        print('The figure folder is not empty. Please empty the figures_ZST folder and run the script again.')
        exit()

    # read bekleding csv
    df = pd.read_csv(bekleding_path,
                     usecols=['vaknaam', 'dwarsprofiel', 'signaleringswaarde', 'ondergrens', 'faalkansbijdrage',
                              'lengte_effectfactor', 'locationid', 'hrdatabase_folder', 'hrdatabase', 'region', 'gws',
                              'getij_amplitude', 'steentoetsfile', 'prfl', 'begin_grasbekleding', 'qvar_p1', 'qvar_p2',
                              'qvar_p3', 'qvar_p4', 'qvar_stap'])
    df = df.dropna(subset=['vaknaam'])  # drop rows where vaknaam is Not a Number
    df = df.reset_index(drop=True)  # reset index

    # run functions
    # step 1: qvariant
    revetment_qvariant(df, profielen_path, database_path, hring_path, output_path)

    # step 2: GEBU
    revetment_gebu(df, profielen_path, output_path, binDIKErnel, figures_GEBU)

    # step 3: ZST
    revetment_zst(df, steentoets_path, output_path, figures_ZST)

    # cleanup files
    files = [Path.cwd().parent.joinpath("step2_mechanism_data", "revetments", "project_utils", "input.json"),
             Path.cwd().parent.joinpath("step2_mechanism_data", "revetments", "1.ini"),
             Path.cwd().parent.joinpath("step2_mechanism_data", "revetments", "1.sql"),
             Path.cwd().parent.joinpath("step2_mechanism_data", "revetments", "1-input.txt"),
             Path.cwd().parent.joinpath("step2_mechanism_data", "revetments", "1-output.sqlite"),
             Path.cwd().parent.joinpath("step2_mechanism_data", "revetments", "1-output.txt"),
             Path.cwd().parent.joinpath("step2_mechanism_data", "revetments", "combin.sqlite"),
             Path.cwd().parent.joinpath("step2_mechanism_data", "revetments", "designTable.txt"),
             Path.cwd().parent.joinpath("step2_mechanism_data", "revetments", "hydraring.log")]

    # remove files
    for file in files:
        # if file exists: remove it
        if (file).exists():
            (file).unlink()


if __name__ == '__main__':

    # input paths
    bekleding_path = Path(r'c:\VRM\test_revetments\Bekleding_default.csv')
    database_path = Path(r'c:\VRM\test_revetments\database')
    steentoets_path = Path(r'c:\VRM\test_revetments\steentoets')
    profielen_path = Path(r'c:\VRM\test_revetments\profielen')
    figures_GEBU = Path(r'c:\VRM\test_revetments\figures_GEBU_test')
    figures_ZST = Path(r'c:\VRM\test_revetments\figures_ZST_test')
    hring_path = Path(
        "c:/Program Files (x86)/BOI/Riskeer 21.1.1.2/Application/Standalone/Deltares/HydraRing-20.1.3.10236")
    binDIKErnel = Path('c:/VRM/test_revetments/bin_DiKErnel')
    output_path = Path(r'c:\VRM\test_revetments\output_test')

    bekleding_main(bekleding_path, database_path, steentoets_path, profielen_path,
                   figures_GEBU, figures_ZST, hring_path, binDIKErnel, output_path)
