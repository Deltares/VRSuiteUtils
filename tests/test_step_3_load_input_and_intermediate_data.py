from pathlib import Path
import pandas as pd
import geopandas as gpd
import pytest
from geopandas.testing import assert_geodataframe_equal, assert_geoseries_equal
from preprocessing.step4_build_sqlite_db.read_intermediate_outputs import *
from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape


@pytest.mark.parametrize("traject,piping_csv",[('35-1',Path('test_data').joinpath('35-1','input_files', 'default_files', 'Piping_default.csv'))])
#test reading the piping csv file
def test_read_piping_csv(traject:str, piping_csv:Path):
 
    #read the piping csv file
    df_piping = read_piping_data(piping_csv)

    #get same file from reference data
    _reference_file = piping_csv.parent.parent.parent.joinpath('reference_data','Piping_default.csv')
    df_piping_ref = pd.read_csv(_reference_file, sep = ',', lineterminator = '\n')

    #compare the content of the tables
    assert df_piping.equals(df_piping_ref), f"Files are not the same"
    
def check_if_parameterized_piping_input_works(traject:str, piping_csv:Path):
    #read the piping csv file
    df_piping = read_piping_data(piping_csv)
    #keep only the first line
    df_piping = df_piping.iloc[0:1,:]

    validate_piping_data(df_piping)

    
def check_if_double_piping_input_crashes(traject:str, piping_csv:Path):
    #read the piping csv file
    df_piping = read_piping_data(piping_csv)
    #keep only the second line
    df_piping = df_piping.iloc[1:2,:]
    #add a second line with the same values
    df_piping = pd.concat([df_piping,df_piping], ignore_index=True)
    #check if it raises an error
    with pytest.raises(ValueError):
        validate_piping_data(df_piping)
    
def check_if_direct_piping_input_works(traject:str, piping_csv:Path):
    #read the piping csv file
    df_piping = read_piping_data(piping_csv)
    #keep only the third line
    df_piping = df_piping.iloc[2:3,:]
    #add a second line with the same values
    df_piping = pd.concat([df_piping,df_piping], ignore_index=True)
    #check if it succeeds
    validate_piping_data(df_piping)
