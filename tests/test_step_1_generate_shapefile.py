from pathlib import Path

import geopandas as gpd
import pytest
import shutil
from geopandas.testing import assert_geodataframe_equal, assert_geoseries_equal

from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape
from preprocessing.workflows.generate_vakindeling_workflow import vakindeling_main
from tests import test_data, test_results

@pytest.mark.parametrize("traject,vakindeling_file",
                         [pytest.param("38-1", test_data.joinpath("38-1", "input", "vakindeling_38-1_full.csv"))])
def test_generate_vakindeling_workflow(traject, vakindeling_file):
    # remove test results
    if test_results.joinpath(traject,"output","vakindeling").exists():
        shutil.rmtree(test_results.joinpath(traject,"output","vakindeling"))
    # make test results dir
    test_results.joinpath(traject,"output","vakindeling").mkdir(parents=True,exist_ok=True)

    vakindeling_main(traject, vakindeling_file, test_results.joinpath(traject,"output","vakindeling"))

    reference_shape = gpd.read_file(
        vakindeling_file.parent.parent.joinpath("reference_shape.geojson"),
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

    new_shape = gpd.read_file(
        test_results.joinpath(traject,"output","vakindeling",f"Vakindeling_{traject}.geojson"),
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