from pathlib import Path

import geopandas as gpd
import pytest
from geopandas.testing import assert_geodataframe_equal, assert_geoseries_equal

from preprocessing.step1_generate_shapefile.traject_shape import TrajectShape
from tests import test_data, test_results

@pytest.mark.parametrize(
    "traject,vakindeling_file",
    [("38-1", test_data.joinpath("38-1", "input", "vakindeling_38-1.csv"))],
)
def test_generate_shapefile(traject, vakindeling_file):
    # make traject
    traject = TrajectShape(traject)

    # get base geometry
    traject.get_traject_shape_from_NBPW(
        NBWP_shape_path=test_data.joinpath("general", "dijktrajecten.shp")
    )

    # cut up in pieces and verify integrity
    traject.generate_vakindeling_shape(vakindeling_file)
    # traject.vakindeling_shape.to_file(vakindeling_file.parent.parent.joinpath('reference_shape.geojson'),driver='GeoJSON')
    # load_reference
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

    # compare geometry
    assert_geoseries_equal(
        reference_shape.geometry,
        traject.vakindeling_shape.geometry,
        check_less_precise=True,
    )

    # compare contents
    assert_geodataframe_equal(
        reference_shape,
        traject.vakindeling_shape,
        check_less_precise=True,
        check_dtype=False,
    )
