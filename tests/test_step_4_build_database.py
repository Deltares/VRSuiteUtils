import shutil
from pathlib import Path

import pytest
from vrtool.orm.models import *
from vrtool.orm.orm_controllers import *
from tests import test_data, test_results
from preprocessing.step4_build_sqlite_db.read_intermediate_outputs import *
from preprocessing.step4_build_sqlite_db.write_database import *
from preprocessing.workflows.write_database_workflow import *
import pandas as pd

@pytest.mark.parametrize("traject,test_name,revetment", [
                                               pytest.param("38-1", "base", False, id="38-1 base river case"),
                                               pytest.param("38-1", "small", False,  id="38-1 two river sections"),
                                               pytest.param("38-1", "small", False,  id="38-1 D-Stability"),
                                               pytest.param("38-1", "full", False, id="38-1 full"),
                                               pytest.param("31-1", "base", True, id="31-1 base coastal case"),
                                               pytest.param("31-1", "mixture", True, id="31-1 mixed coastal case"),
                                               pytest.param("31-1", "small", True, id="31-1 two coastal sections"),
                                               pytest.param("31-1", "full", True, id="31-1 full"),
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

   # read the vakindeling shape. This is universal for each traject we consider. Turning on and off sections is done through the vakindeling_config
   vakindeling_shape = gpd.read_file(_test_data_dir.joinpath("reference_results","reference_shapes", f"reference_shape.geojson"))
   vakindeling_config = pd.read_csv(_test_data_dir.joinpath("settings", "vakindeling_configuration.csv"),
                                    dtype={test_name:int},sep=",").rename(columns={test_name:'in_analyse'})

   #reset in_analyse in vakindeling_shape based on vakindeling_config. This is only for testdata.
   vakindeling_shape = pd.merge(vakindeling_shape.drop(columns=['in_analyse']),vakindeling_config[['objectid','in_analyse']],on='objectid')

   if 'kunstwerken' in vakindeling_shape.columns:  vakindeling_shape.drop(columns=['kunstwerken'],inplace=True)
   # read the HR_input
   HR_input = pd.read_csv(
      _test_data_dir.joinpath("HRING_data_reference.csv"),
      dtype={'doorsnede':str}).drop_duplicates(subset=["doorsnede"])
   # read the data for different mechanisms

   # read the data for waterlevels
   _intermediate_dir = _test_data_dir.joinpath("intermediate")
   waterlevel_table = read_waterlevel_data(_intermediate_dir.joinpath("Waterstand"))


   #read mechanism_data and store in dictionary. We must have overflow and stabiliteit. Others are optional
   vakindeling_shape.astype({'overslag': str, 'stabiliteit':str})
   mechanism_data = {'overslag': read_overflow_data(_intermediate_dir.joinpath("Overslag"))}
   if 'D-Stability' in request.node.callspec.id: 
      mechanism_data['stabiliteit'] = read_stability_data(_intermediate_dir.joinpath("STBI_data_DStability.csv"))
   else:
      mechanism_data['stabiliteit'] = read_stability_data(_intermediate_dir.joinpath("STBI_data.csv"))

   try:
      vakindeling_shape.astype({'piping': str})
      mechanism_data['piping'] = read_piping_data(_intermediate_dir.joinpath("Piping_data.csv"))
   except: #drop column
      vakindeling_shape.drop(columns=['piping'], inplace=True)            
   
   if revetment:
      try:
         vakindeling_shape.astype({'bekledingen': str})
         if (test_name == 'mixture') & (traject == '31-1'):
            vakindeling_shape.loc[vakindeling_shape.objectid.isin([7, 8]),'bekledingen'] = None
         mechanism_data['slope_part_table'], mechanism_data['rel_GEBU_table'], mechanism_data['rel_ZST_table']  = read_revetment_data(_intermediate_dir.joinpath("Bekleding"))
      except:
         vakindeling_shape.drop(columns=['bekledingen'], inplace=True)

   #merge the HR_input and stabiliteit input
       # merge parameters from HR_input with vakindeling_shape:
   vakindeling_shape = merge_to_vakindeling(vakindeling_shape, to_merge = HR_input[["doorsnede", "dijkhoogte", "kruindaling"]], left_key = ['overslag'], right_key = ['doorsnede'])

    # merge subsoil parameters with vakindeling if not present in vakindeling_shape
   if 'pleistoceendiepte' not in vakindeling_shape.columns:
      vakindeling_shape = merge_to_vakindeling(vakindeling_shape, to_merge = mechanism_data['stabiliteit'][["pleistoceendiepte", "deklaagdikte"]], left_key = ['stabiliteit'], right_key = ['doorsnede'])
   
   # read the data for measures
   #get measure df:
   measures_per_section = pd.read_csv(_test_data_dir.joinpath("settings","maatregelen.csv"),index_col=0)[request.node.callspec.id]
   measure_tables = {measure_set: read_measures_data(_generic_data_dir.joinpath(measure_set)) for measure_set in measures_per_section.dropna().unique()}
   # if revetment:
   #    measures_table = read_measures_data(_generic_data_dir.joinpath("base_measures_revetment_selectie.csv"))
   # else:
   #    measures_table = read_measures_data(_generic_data_dir.joinpath("base_measures.csv"))


   # read the data for bebouwing
   bebouwing_table = read_bebouwing_data(
      _intermediate_dir.joinpath("Bebouwing_data.csv")
   )

   # read the data for profilepoints
   profile_table = read_profile_data(_intermediate_dir.joinpath("Profielen","profielen_{}.csv".format(traject)))
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
      section_list = vakindeling_shape[(vakindeling_shape.in_analyse == True) & (measures_per_section.values == measure_set)].vaknaam.tolist()
      fill_measures(measure_table=measures_table, list_of_sections = section_list)

   #assert that the database is equal to the reference database
   _reference_database = _test_data_dir.joinpath('reference_databases','{}.db'.format(request.node.callspec.id))
   assert _reference_database.exists(), "No reference database available at {}".format(_reference_database)

   compare_databases(_output_path, _reference_database)



