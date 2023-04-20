from pathlib import Path
import pandas as pd
import os

from preprocessing.common_functions import check_string_in_list
from preprocessing.step2_mechanism_data.hydraring_computation import HydraRingComputation
from preprocessing.step2_mechanism_data.waterlevel.waterlevel_hydraring import WaterlevelComputationInput
from preprocessing.step2_mechanism_data.overflow.overflow_input import OverflowInput


def main(work_dir,database_paths,
         config_db_path = Path(r'c:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236\config.sqlite')):
    '''This is the main function of the workflow.
    It can be used to generate and evaluate Hydra-Ring computations for waterlevel for a given dataset'''

    #read HRING reference csv
    hring_data = pd.read_csv(work_dir.joinpath('GEKB_data.csv'),index_col=0)

    #ensure presence of HRLocation column, otherwise get it from the database
    if 'HRLocation' not in hring_data.columns:
        hrd_path = [pad for pad in database_paths[0].glob('*.sqlite') if not check_string_in_list(pad.name, ['.config', 'hlcd'])][0]
    hring_data = OverflowInput.get_HRLocation(hrd_path, hring_data)

    #we can now loop over all the locations and databases to generate the Hydra-Ring input files.
    for database_path in database_paths:
        for count, location in hring_data.iterrows():
            #make output dir
            loc_output_dir = work_dir.joinpath(database_path.stem,location.dijkvak)
            if loc_output_dir.exists():
                loc_output_dir.rmdir()
            loc_output_dir.mkdir(parents=True,exist_ok=False)
            #make computation object
            computation = WaterlevelComputationInput()
            #data from input sheet:
            computation.fill_data(location)
            #get config from hydraulic database:
            computation.get_HRING_config(database_path)
            #make sql file. Make sure that range is adjusted for 2100
            if '2100' not in str(database_path):
                computation.make_SQL_file(loc_output_dir,Path(os.getcwd()).parent.parent.joinpath('tests','test_data','general','sql_reference_waterlevel.sql'))
            else:
                computation.make_SQL_file(loc_output_dir,Path(os.getcwd()).parent.parent.joinpath('tests','test_data','general','sql_reference_waterlevel.sql'),t_2100=True)
            #make ini file:
            computation.make_ini_file(loc_output_dir,Path(os.getcwd()).parent.parent.joinpath('tests','test_data','general','ini_reference_waterlevel.ini'),database_path,config_db_path)
            #run Hydra-Ring
            HydraRingComputation().run_hydraring(computation.ini_path)









if __name__ == '__main__':
    # MAIN SETTINGS:
    # working directory:
    work_dir = Path(r'c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_HWBP\test_waterstand')
    # location of Hydra-Ring config:
    # ...

    # list of paths to databases to be considered
    database_paths = [Path(r'c:\Users\klerk_wj\OneDrive - Stichting Deltares\00_Projecten\11_VR_HWBP\test_waterstand\2023')]
    main(work_dir,database_paths)