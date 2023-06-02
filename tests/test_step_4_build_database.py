import shutil
from pathlib import Path

import pytest
from vrtool.orm.models import *
from vrtool.orm.orm_controllers import *
from tests import test_data, test_results
from preprocessing.step4_build_sqlite_db.read_intermediate_outputs import *
from preprocessing.step4_build_sqlite_db.write_database import *
import pandas as pd

@pytest.mark.parametrize("traject,test_name", [pytest.param("38-1", "no_housing", id="38-1 no_housing"),
                                               pytest.param("38-1", "overflow_no_housing", id="38-1 overflow no_housing"),
                                               pytest.param("38-1", "full", id="38-1 volledig"),])
def test_make_database(traject: str, test_name: str, request: pytest.FixtureRequest):
   # remove output_path
   _output_path = test_results.joinpath(request.node.name, "{}_{}.db".format(traject,test_name))
   if _output_path.parent.exists():
      shutil.rmtree(_output_path.parent)

   # get all the input data
   # read the vakindeling shape
   _test_data_dir = test_data.joinpath(traject)
   assert _test_data_dir.exists(), "No test data available at {}".format(
      _test_data_dir
   )

   shapefile = gpd.read_file(_test_data_dir.joinpath("reference_shape.geojson"))

   vakindeling_csv = pd.read_csv(_test_data_dir.joinpath("input", "vakindeling_{}_{}.csv".format(traject,test_name)),dtype={'in_analyse':int})
   #reset in_analyse in shapefile based on vakindeling_csv. This is only for testdata.
   shapefile = pd.merge(shapefile.drop(columns=['in_analyse']),vakindeling_csv[['objectid','in_analyse']],on='objectid')

   # read the HR_input
   HR_input = pd.read_csv(
      _test_data_dir.joinpath("HRING_data_reference.csv")
   ).drop_duplicates(subset=["doorsnede"])
   # read the data for different mechanisms

   # read the data for waterlevels
   _intermediate_dir = _test_data_dir.joinpath("intermediate")
   waterlevel_table = read_waterlevel_data(_intermediate_dir.joinpath("Waterstand"))

   # read the data for overflow
   overflow_table = read_overflow_data(_intermediate_dir.joinpath("Overslag"))

   # read the data for piping
   piping_table = read_piping_data(_intermediate_dir.joinpath("Piping_data.csv"))

   # read the data for stability
   stability_table = read_stability_data(_intermediate_dir.joinpath("STBI_data.csv"))

   # read the data for bebouwing
   bebouwing_table = read_bebouwing_data(
      _intermediate_dir.joinpath("Bebouwing_data.csv")
   )

   # read the data for measures
   measures_table = read_measures_data(_intermediate_dir.joinpath("base_measures.csv"))

   # read the data for profilepoints
   profile_table = read_profilepoints_data(_intermediate_dir.joinpath("Profielen"))

   initialize_database(_output_path)
   assert _output_path.exists(), "Database file was not created."

   db_obj = open_database(_output_path)

   # diketractinfo
   fill_diketrajectinfo_table(traject=traject)
   # sectiondata
   fill_sectiondata_table(
      traject=traject,
      shape_file=shapefile,
      HR_input=HR_input,
      geo_input=stability_table[["deklaagdikte", "pleistoceendiepte"]],
   )
   # waterleveldata
   fill_buildings(buildings=bebouwing_table)

   fill_waterleveldata(waterlevel_table=waterlevel_table, shape_file=shapefile)

   fill_profilepoints(profile_points=profile_table, shape_file=shapefile)

   # fill all the mechanisms
   fill_mechanisms(overflow_table=overflow_table,piping_table=piping_table,stability_table=stability_table, shape_file=shapefile)

   # fill measures
   fill_measures(measure_table=measures_table)

   #assert that the database is equal to the reference database
   _reference_database = _test_data_dir.joinpath('reference_databases','{}_{}.db'.format(traject,test_name))
   assert _reference_database.exists(), "No reference database available at {}".format(_reference_database)

   compare_databases(_output_path, _reference_database)



