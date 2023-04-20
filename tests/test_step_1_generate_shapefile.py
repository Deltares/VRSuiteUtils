import pytest
from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape
from pathlib import Path
import geopandas as gpd
from geopandas.testing import assert_geodataframe_equal,assert_geoseries_equal
@pytest.mark.parametrize("traject,vakindeling_file",[('38-1',Path('test_data').joinpath('38-1','input','vakindeling_test.xlsx'))])
def test_generate_shapefile(traject,vakindeling_file):
    #make traject
    traject = TrajectShape(traject)

    #get base geometry
    traject.get_traject_shape_from_NBPW()

    #cut up in pieces and verify integrity
    traject.generate_vakindeling_shape(vakindeling_file)

    #load_reference
    reference_shape = gpd.read_file(vakindeling_file.parent.parent.joinpath('reference_shape.shp'))

    #compare geometry
    assert_geoseries_equal(reference_shape.geometry,traject.vakindeling_shape.geometry,check_less_precise=True)

    #compare contents
    assert_geodataframe_equal(reference_shape,traject.vakindeling_shape,check_less_precise=True)
