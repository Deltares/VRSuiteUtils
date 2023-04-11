import pytest
from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape
from pathlib import Path
import geopandas as gpd
import pandas as pd
from geopandas.testing import assert_geodataframe_equal,assert_geoseries_equal
from preprocessing.step2_mechanism_data.overflow import OverflowInput
@pytest.mark.parametrize("hring_input,gekb_shape,traject_shape,db_location",[(Path('test_data').joinpath('38-1','input','HRING_data.csv'),
                                                                  Path('test_data').joinpath('38-1','input','gekb_shape.shp'),
                                                                  Path('test_data').joinpath('38-1','reference_shape.shp'),
                                                                  Path('test_data').joinpath('38-1','input','db','2023','WBI2017_Bovenrijn_38-1_v04.sqlite'))])


def test_select_HRING_locs(hring_input,traject_shape,db_location,gekb_shape):
    #HRING input should have: M-value of location, and what is in HR-data.
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

    overflow_input.get_HRLocation(db_location)

    overflow_input.verify_and_filter_columns()
    pd.testing.assert_frame_equal(overflow_input.hring_data,pd.read_csv(Path(traject_shape.parent).joinpath('HRING_data_reference.csv'),index_col=0))
    # overflow_input.hring_data.to_csv(Path('test_data','38-1','HRING_data_reference2.csv'))

def test_make_HRING_overflow_input():
    pass

def test_add_piping_tool_input():
    pass

def test_add_stability_data():
    pass

def test_add_piping_data():
    pass