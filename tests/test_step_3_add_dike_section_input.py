import pytest
from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape
from pathlib import Path
import geopandas as gpd
from geopandas.testing import assert_geodataframe_equal,assert_geoseries_equal

# @pytest.mark.parametrize("traject,traject_shape",[('38-1',Path('test_data').joinpath('38-1','reference.shp'))])
def test_derive_toe_from_AHN():
    pass

def test_verify_toe_from_shape():
    pass

def test_get_profile_from_AHN():
    pass

def read_profile_from_file():
    pass

def get_buildings_from_BAG():
    pass

def get_measures_from_file():
    pass


