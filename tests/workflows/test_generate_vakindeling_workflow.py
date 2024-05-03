from pathlib import Path
import preprocessing.api as api
import geopandas as gpd
import pytest
import shutil
from geopandas.testing import assert_geodataframe_equal, assert_geoseries_equal

from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape
from preprocessing.workflows.generate_vakindeling_workflow import vakindeling_main
from tests import test_data, test_results
from preprocessing.common_functions import read_config_file

@pytest.mark.parametrize("project_folder",
                         [pytest.param("31-1_v2", id = '31-1')])
def test_generate_vakindeling_workflow(project_folder:str,  request: pytest.FixtureRequest):
    #specify the output path for results:
    _output_path = test_results.joinpath(request.node.name)
    if _output_path.exists():
        shutil.rmtree(_output_path)
    
    #run the vakindeling workflow to generate the geojson
    api.generate_vakindeling_shape(test_data.joinpath(project_folder, "preprocessor.config"), _output_path)
    
    #get the relative path from the config
    _output_file = read_config_file(test_data.joinpath(project_folder, "preprocessor.config"), ['vakindeling_geojson'])['vakindeling_geojson']

    #read the generated vakindeling shapefile
    new_shape = gpd.read_file(
       _output_path.joinpath(_output_file),
        dtype={
            "objectid": int,
            "vaknaam": str,
            "m_start": float,
            "m_eind": float,
            "in_analyse": int,
            "van_dp": str,
            "tot_dp": str,
            "stabiliteit": str,
            "piping": str,
            "overslag": str,
            "bekledingen": object,
            "kunstwerken": object,
        },
    )    
    #read the reference shapefile
    reference_shape = gpd.read_file(test_data.joinpath(project_folder, _output_file),
        dtype={
            "objectid": int,
            "vaknaam": str,
            "m_start": float,
            "m_eind": float,
            "in_analyse": int,
            "van_dp": str,
            "tot_dp": str,
            "stabiliteit": str,
            "piping": str,
            "overslag": str,
            "bekledingen": object,
            "kunstwerken": object,
        },)

    # compare geometry
    assert_geoseries_equal(
        reference_shape.geometry,
        new_shape.geometry,
        check_less_precise=True,
    )

    # compare contents
    assert_geodataframe_equal(
        reference_shape,
        new_shape,
        check_less_precise=True,
        check_dtype=False,
    )