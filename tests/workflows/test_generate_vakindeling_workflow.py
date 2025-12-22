from pathlib import Path
import preprocessing.api as api
import geopandas as gpd
import pandas as pd
import pytest
import shutil
from geopandas.testing import assert_geodataframe_equal, assert_geoseries_equal
from pandas.testing import assert_frame_equal

from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape
from preprocessing.workflows.generate_vakindeling_workflow import vakindeling_main
from tests import test_data, test_results
from preprocessing.common_functions import read_config_file, read_csv

@pytest.mark.parametrize("project_folder,config_name",
                         [pytest.param("31-1_v2", "preprocessor.config", id = '31-1'),
                          pytest.param("31-1_v2", "preprocessor_minder_vakken.config", id = '31-1 vakken uit'),
                          pytest.param("35-1", "preprocessor.config", id = '35-1'),])
def test_generate_vakindeling_workflow(project_folder:str, config_name: str, request: pytest.FixtureRequest):
    #specify the output path for results:
    _output_path = test_results.joinpath(request.node.name)
    if _output_path.exists():
        shutil.rmtree(_output_path, ignore_errors=True)
    
    #run the vakindeling workflow to generate the geojson
    api.generate_vakindeling_shape(test_data.joinpath(project_folder, config_name), _output_path)
    
    #get the relative paths from the config
    _output_geojson = read_config_file(test_data.joinpath(project_folder, config_name), ['vakindeling_geojson'])['vakindeling_geojson']
    _maatregel_config_path = read_config_file(test_data.joinpath(project_folder, config_name), ['maatregelen_configuratie'])['maatregelen_configuratie']
    #read the generated vakindeling shapefile
    new_shape = gpd.read_file(
       _output_path.joinpath(_output_geojson),
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
    reference_shape = gpd.read_file(test_data.joinpath(project_folder, _output_geojson),
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

    # compare dataframe for configuratie_maatregelen.csv
    assert_frame_equal(
        read_csv(test_data.joinpath(project_folder, _maatregel_config_path), index_col=0),
        read_csv(_output_path.joinpath(_maatregel_config_path), index_col=0),
        check_dtype=False,
    )
    