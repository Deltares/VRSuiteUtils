from pathlib import Path

import geopandas as gpd
import pytest
import shutil
from geopandas.testing import assert_geodataframe_equal, assert_geoseries_equal

from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape
from preprocessing.workflows.generate_vakindeling_workflow import vakindeling_main
from tests import test_data, test_results

@pytest.mark.parametrize("traject,vakindeling_file,case",
                         [pytest.param("38-1", "vakindeling_38-1_full.csv", "full")])
def test_generate_vakindeling_workflow(traject, vakindeling_file, case):
    vakindeling_file_path = test_data.joinpath(traject, "input", "vakindeling", vakindeling_file)
    output_folder = test_results.joinpath(traject,"output","vakindeling", case)
    # remove test results
    if output_folder.exists():
        shutil.rmtree(output_folder)
    # make test results dir
    output_folder.mkdir(parents=True,exist_ok=True)

    vakindeling_main(traject, vakindeling_file_path, output_folder)

    reference_shape = gpd.read_file(
        test_data.joinpath(traject, "reference_results","reference_shapes", f"reference_shape_{case}.geojson"),
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
        output_folder.joinpath(f"Vakindeling_{traject}.geojson"),
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