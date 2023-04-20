import shutil
import filecmp
import pytest
from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape
from pathlib import Path
import geopandas as gpd
import pandas as pd
import os
from geopandas.testing import assert_geodataframe_equal,assert_geoseries_equal
from preprocessing.step2_mechanism_data.overflow.overflow_input import OverflowInput
from preprocessing.step2_mechanism_data.overflow.overflow_hydraring import OverflowComputationInput
from preprocessing.step2_mechanism_data.hydraring_computation import HydraRingComputation


@pytest.mark.parametrize("hring_input,gekb_shape,traject_shape,db_location",[(Path('test_data').joinpath('38-1','input','HRING_data.csv'),
                                                                  Path('test_data').joinpath('38-1','input','gekb_shape.shp'),
                                                                  Path('test_data').joinpath('38-1','reference_shape.shp'),
                                                                  Path('test_data').joinpath('38-1','input','db','2023','WBI2017_Bovenrijn_38-1_v04.sqlite'))])
def test_select_HRING_locs(hring_input,traject_shape,db_location,gekb_shape):
    #test to see if the correct locations are selected from the HRING input csv. This is done based on a shapefile with all the locations.
    #HRING_input input should have: M-value of location, and what is in HR-data.
    #read GEKB_input:
    hring_df = pd.read_csv(hring_input,index_col=0)
    gekb_shape = gpd.read_file(gekb_shape).sort_values('M_VAN').drop('OBJECTID', axis=1).reset_index(drop=True).reset_index().rename(columns={'index': 'OBJECTID'})

    overflow_input = OverflowInput(traject_shape,kind='weakest')
    #check if M-value in hring_df
    if any(hring_df.M_VALUE.isna()):
        overflow_input.get_mvalue_of_locs(hring_df,gekb_shape)
    else:
        overflow_input.hring_data = hring_df

    overflow_input.select_locs()

    overflow_input.hring_data = overflow_input.get_HRLocation(db_location, overflow_input.hring_data)

    overflow_input.verify_and_filter_columns()
    pd.testing.assert_frame_equal(overflow_input.hring_data,pd.read_csv(Path(traject_shape.parent).joinpath('HRING_data_reference.csv'),index_col=0))

@pytest.mark.parametrize("HRING_data,HRING_input_reference, db_path, results_dir, ilocs",[(Path('test_data').joinpath('38-1','HRING_data_reference.csv'),
                                                                               Path('test_data').joinpath('38-1','HRING_input_reference','waterlevel'),
                                                                               Path('test_data').joinpath('38-1','input','db'),
                                                                               Path('test_results').joinpath('38-1','HRING_input','waterlevel'),
                                                                               [0, 20, 40])])
def test_make_HRING_waterlevel_input(HRING_data,HRING_input_reference, results_dir, db_path,ilocs,
                                   config_db_path = Path(r'c:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236\config.sqlite')):
    #this test writes HRING files to the results dir, and compares them to the reference files.

    #make list of db paths
    database_paths = list(db_path.glob("*\\"))

    #clear the output dir
    if results_dir.exists(): shutil.rmtree(results_dir)

    # make output dir
    results_dir.mkdir(parents=True,exist_ok=False)

    #read locations, filter 3 locs as defined in ilocs
    HRING_data = pd.read_csv(HRING_data,index_col=0)
    HRING_data = HRING_data.iloc[ilocs]

    #initialize lists for errors
    comparison_errors_ini = []
    comparison_errors_sql = []
    #loop over all locations and databases
    for database_path in database_paths:
        results_dir.joinpath(database_path.stem).mkdir(parents=True,exist_ok=False)
        for count, location in HRING_data.iterrows():
            #make output dir
            loc_output_dir = results_dir.joinpath(database_path.stem,location.dijkvak)
            loc_output_dir.mkdir(parents=True,exist_ok=False)

            #path to reference dir
            loc_output_reference_dir = HRING_input_reference.joinpath(database_path.stem,location.dijkvak)

            #make computation object
            computation = OverflowComputationInput()
            #data from input sheet:
            computation.fill_data(location)
            #add profile data:
            computation.get_prfl(prfl_path.joinpath(location.prfl_bestand))
            #get config from hydraulic database:
            computation.get_HRING_config(database_path)
            #get critical discharge
            computation.get_critical_discharge(Path('test_data').joinpath('general','critical_discharges.csv'))
            #make sql file
            computation.make_SQL_file(loc_output_dir,Path('test_data').joinpath('general','sql_reference_overflow.sql'))
            if not filecmp.cmp(loc_output_dir.joinpath(computation.name + '.sql'),loc_output_reference_dir.joinpath(computation.name + '.sql')):
                comparison_errors_sql.append('SQL-file for {} not identical'.format(computation.name))
            #make ini file
            computation.make_ini_file(loc_output_dir,Path('test_data').joinpath('general','ini_reference_overflow.ini'),database_path,config_db_path)
            if not filecmp.cmp(loc_output_dir.joinpath(computation.name + '.ini'),loc_output_reference_dir.joinpath(computation.name + '.ini')):
                comparison_errors_ini.append('ini-file for {} and database {} not identical'.format(computation.name, database_path.stem))

    assert not comparison_errors_ini + comparison_errors_sql, f"Errors: {comparison_errors_ini + comparison_errors_sql}"

@pytest.mark.parametrize("HRING_data,HRING_input_reference, prfl_path, db_path, results_dir, ilocs",[(Path('test_data').joinpath('38-1','HRING_data_reference.csv'),
                                                                               Path('test_data').joinpath('38-1','HRING_input_reference','overflow'),
                                                                               Path('test_data').joinpath('38-1','input','prfl'),
                                                                               Path('test_data').joinpath('38-1','input','db'),
                                                                               Path('test_results').joinpath('38-1','HRING_input','overflow'),
                                                                               [0, 20, 40])])
def test_make_HRING_overflow_input(HRING_data,HRING_input_reference,prfl_path, results_dir, db_path,ilocs,
                                   config_db_path = Path(r'c:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236\config.sqlite')):
    #this test writes HRING files to the results dir, and compares them to the reference files.

    #make list of db paths
    database_paths = list(db_path.glob("*\\"))

    #clear the output dir
    if results_dir.exists(): shutil.rmtree(results_dir)

    # make output dir
    results_dir.mkdir(parents=True,exist_ok=False)

    #read locations, filter 3 locs as defined in ilocs
    HRING_data = pd.read_csv(HRING_data,index_col=0)
    HRING_data = HRING_data.iloc[ilocs]

    #initialize lists for errors
    comparison_errors_ini = []
    comparison_errors_sql = []
    #loop over all locations and databases
    for database_path in database_paths:
        results_dir.joinpath(database_path.stem).mkdir(parents=True,exist_ok=False)
        for count, location in HRING_data.iterrows():
            #make output dir
            loc_output_dir = results_dir.joinpath(database_path.stem,location.dijkvak)
            loc_output_dir.mkdir(parents=True,exist_ok=False)

            #path to reference dir
            loc_output_reference_dir = HRING_input_reference.joinpath(database_path.stem,location.dijkvak)

            #make computation object
            computation = OverflowComputationInput()
            #data from input sheet:
            computation.fill_data(location)
            #add profile data:
            computation.get_prfl(prfl_path.joinpath(location.prfl_bestand))
            #get config from hydraulic database:
            computation.get_HRING_config(database_path)
            #get critical discharge
            computation.get_critical_discharge(Path('test_data').joinpath('general','critical_discharges.csv'))
            #make sql file
            computation.make_SQL_file(loc_output_dir,Path('test_data').joinpath('general','sql_reference_overflow.sql'))
            if not filecmp.cmp(loc_output_dir.joinpath(computation.name + '.sql'),loc_output_reference_dir.joinpath(computation.name + '.sql')):
                comparison_errors_sql.append('SQL-file for {} not identical'.format(computation.name))
            #make ini file
            computation.make_ini_file(loc_output_dir,Path('test_data').joinpath('general','ini_reference_overflow.ini'),database_path,config_db_path)
            if not filecmp.cmp(loc_output_dir.joinpath(computation.name + '.ini'),loc_output_reference_dir.joinpath(computation.name + '.ini')):
                comparison_errors_ini.append('ini-file for {} and database {} not identical'.format(computation.name, database_path.stem))

    assert not comparison_errors_ini + comparison_errors_sql, f"Errors: {comparison_errors_ini + comparison_errors_sql}"

@pytest.mark.parametrize("ini_file",[(Path('test_data').joinpath('38-1', 'HRING_input_reference','2023','RW000','RW000.ini'))])
def test_run_HydraRing(ini_file):
    #path of work_dir is the same as the ini_file
    work_dir = ini_file.parent

    #run HydraRing
    HydraRingComputation().run_hydraring(Path(os.getcwd()).joinpath(ini_file))

    # move designTable.txt from work_dir to test_results\38-1\HRING_input\2023\RW000\
    shutil.move(work_dir.joinpath('designTable.txt'),
                Path(os.getcwd()).joinpath('test_results',work_dir.parts[1],'HRING_computations',*work_dir.parts[3:],'designTable.txt'))

    #remove the other files for which the name is not the same as the ini_file
    for file in work_dir.glob('*'):
        if file.stem != ini_file.stem:
            file.unlink()

    #compare the designTable.txt with the reference file
    assert filecmp.cmp(Path(os.getcwd()).joinpath('test_results',work_dir.parts[1],'HRING_computations',*work_dir.parts[3:],'designTable.txt'),
Path(os.getcwd()).joinpath('test_data',work_dir.parts[1],'HRING_computations_reference',*work_dir.parts[3:],'designTable.txt'))



    #test to verify correct run of Hydra-Ring. Note that it requires a specific version of Riskeer that should be installed locally.
#     # TODO: see if we need to add it to the repos.

def test_add_piping_tool_input():
    pass

def test_add_stability_data():
    pass

def test_add_piping_data():
    pass