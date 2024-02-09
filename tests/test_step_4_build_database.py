import shutil
from pathlib import Path

import pytest
from vrtool.orm.models import *
from vrtool.orm.orm_controllers import *
from tests import test_data, test_results
from preprocessing.step4_build_sqlite_db.read_intermediate_outputs import *
from preprocessing.step4_build_sqlite_db.write_database import *
import pandas as pd

@pytest.mark.parametrize("traject,test_name,revetment", [
                                               pytest.param("38-1", "base", False, id="38-1 base case"),
                                               pytest.param("38-1", "small", False,  id="38-1 two sections"),
                                               pytest.param("38-1", "small", False,  id="38-1 D-Stability"),
                                               pytest.param("38-1", "full", False, id="38-1 volledig"),
                                                   ])
def test_make_database(traject: str, test_name: str, revetment: bool,  request: pytest.FixtureRequest):

   # remove output_path
   #get id of request
   _output_path = test_results.joinpath(request.node.name, "{}.db".format(request.node.callspec.id))
   if _output_path.parent.exists():
      shutil.rmtree(_output_path.parent)

   # get all the input data
   _generic_data_dir = test_data.parent.parent.joinpath("preprocessing","generic_data")
   _test_data_dir = test_data.joinpath(traject)
   assert _test_data_dir.exists(), "No test data available at {}".format(
      _test_data_dir
   )

   # read the vakindeling shape. This is universal for each traject we consider. Turning on and off sections is done through the vakindeling_csv
   vakindeling_shape = gpd.read_file(_test_data_dir.joinpath("reference_results","reference_shapes", f"reference_shape.geojson"))


   try:
      vakindeling_csv = pd.read_csv(_test_data_dir.joinpath("input", "vakindeling", "vakindeling_{}.csv".format(test_name)),dtype={'in_analyse':int},sep=",", lineterminator="\n")
   except:
      vakindeling_csv = pd.read_csv(_test_data_dir.joinpath("input", "vakindeling", "vakindeling_{}.csv".format(test_name)),dtype={'in_analyse':int},sep=";", lineterminator="\n")

   #reset in_analyse in vakindeling_shape based on vakindeling_csv. This is only for testdata.
   vakindeling_shape = pd.merge(vakindeling_shape.drop(columns=['in_analyse']),vakindeling_csv[['objectid','in_analyse']],on='objectid')
   vakindeling_shape.drop(columns=['kunstwerken'],inplace=True)
   # read the HR_input
   HR_input = pd.read_csv(
      _test_data_dir.joinpath("HRING_data_reference.csv")
   ).drop_duplicates(subset=["doorsnede"])
   # read the data for different mechanisms

   # read the data for waterlevels
   _intermediate_dir = _test_data_dir.joinpath("intermediate")
   waterlevel_table = read_waterlevel_data(_intermediate_dir.joinpath("Waterstand"))


   #read mechanism_data and store in dictionary. We must have overflow and stabiliteit. Others are optional
   mechanism_data = {'overslag': read_overflow_data(_intermediate_dir.joinpath("Overslag"))}
   if 'D-Stability' in test_name: 
      mechanism_data['stabiliteit'] = read_stability_data(_intermediate_dir.joinpath("STBI_data.csv"))
   else:
      mechanism_data['stabiliteit'] = read_stability_data(_intermediate_dir.joinpath("STBI_data_DStability.csv"))

   try:
      vakindeling_shape.astype({'piping': str})
      mechanism_data['piping'] = read_piping_data(_intermediate_dir.joinpath("Piping_data.csv"))
   except: #drop column
      vakindeling_shape.drop(columns=['piping'], inplace=True)            
   
   if revetment:
      try:
         vakindeling_shape.astype({'bekledingen': str})
         mechanism_data['slope_part_table'], mechanism_data['rel_GEBU_table'], mechanism_data['rel_ZST_table']  = read_revetment_data(_intermediate_dir.joinpath("Bekleding"))
      except:
         vakindeling_shape.drop(columns=['bekledingen'], inplace=True)


   # read the data for measures
   #get measure df:
   measures_per_section = pd.read_csv(_test_data_dir.joinpath("input","maatregelen.csv"),index_col=0)[request.node.callspec.id]
   measure_tables = {measure_set: read_measures_data(_generic_data_dir.joinpath(measure_set)) for measure_set in measures_per_section.unique()}
   # if revetment:
   #    measures_table = read_measures_data(_generic_data_dir.joinpath("base_measures_revetment_selectie.csv"))
   # else:
   #    measures_table = read_measures_data(_generic_data_dir.joinpath("base_measures.csv"))


   # read the data for bebouwing
   bebouwing_table = read_bebouwing_data(
      _intermediate_dir.joinpath("Bebouwing_data.csv")
   )

   # read the data for profilepoints
   profile_table = read_profile_data(_intermediate_dir.joinpath("Profielen","profielen_38-1.csv"))
   # profile_table = read_profiles_old(_intermediate_dir.joinpath("Profielen"))

   initialize_database(_output_path)
   assert _output_path.exists(), "Database file was not created."

   db_obj = open_database(_output_path)

   # diketractinfo
   fill_diketrajectinfo_table(traject=traject,length = vakindeling_shape.m_eind.max())
   # sectiondata
   fill_sectiondata_table(
      traject=traject,
      shape_file=vakindeling_shape,
      HR_input=HR_input,
      geo_input=mechanism_data['stabiliteit'][["deklaagdikte", "pleistoceendiepte"]],
   )
   # waterleveldata
   fill_buildings(buildings=bebouwing_table)

   fill_waterleveldata(waterlevel_table=waterlevel_table, shape_file=vakindeling_shape)

   fill_profiles(profile_table)

   # fill all the mechanisms
   fill_mechanisms(mechanism_data=mechanism_data, shape_file=vakindeling_shape)

   # fill measures
   for measure_set, measures_table in measure_tables.items():
      #get sections for which measure_set is relevant
      section_list = []
      fill_measures(measure_table=measures_table, list_of_sections = section_list)

   #assert that the database is equal to the reference database
   _reference_database = _test_data_dir.joinpath('reference_databases','{}_{}.db'.format(traject,test_name))
   assert _reference_database.exists(), "No reference database available at {}".format(_reference_database)

   compare_databases(_output_path, _reference_database)



