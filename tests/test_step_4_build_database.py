import shutil
from pathlib import Path

import pytest
from vrtool.orm.models import *
from vrtool.orm.orm_controllers import *
from tests import test_data, test_results
from preprocessing.step4_build_sqlite_db.read_intermediate_outputs import *
from preprocessing.step4_build_sqlite_db.write_database import *
from preprocessing.workflows.write_database_workflow import *
from preprocessing.common_functions import read_csv
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
   vakindeling_config = read_csv(_test_data_dir.joinpath("settings", "vakindeling_configuration.csv"),
                                    dtype={test_name:int}).rename(columns={test_name:'in_analyse'})

   #reset in_analyse in vakindeling_shape based on vakindeling_config. This is only for testdata.
   vakindeling_shape = pd.merge(vakindeling_shape.drop(columns=['in_analyse']),vakindeling_config[['objectid','in_analyse']],on='objectid')

   if 'kunstwerken' in vakindeling_shape.columns:  vakindeling_shape.drop(columns=['kunstwerken'],inplace=True)
   # read the HR_input
   HR_input = read_csv(
      _test_data_dir.joinpath("HRING_data_reference.csv"),
      dtype={'doorsnede':str}).drop_duplicates(subset=["doorsnede"])
   # read the data for different mechanisms

   # read the data for waterlevels
   _intermediate_dir = _test_data_dir.joinpath("intermediate")
   waterlevel_table = read_waterlevel_data(_intermediate_dir.joinpath("Waterstand"), True)


   #read mechanism_data and store in dictionary. We must have overflow and stabiliteit. Others are optional
   vakindeling_shape.astype({'overslag': str, 'stabiliteit':str})
   mechanism_data = {'overslag': read_overflow_data(_intermediate_dir.joinpath("Overslag"), True)}
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

   # # read the data for measures
   if (traject == '31-1') and (not test_name in ['full', 'mixture']):
      measures_table = read_measures_data(_generic_data_dir.joinpath("base_measures_revetment_small.csv"))
   else:
      measures_table = read_measures_data(_generic_data_dir.joinpath("base_measures_totaal.csv"))

   #read the configuration
   measure_configuration_table, measures_table = read_measures_config(_test_data_dir.joinpath("settings","configuratie_maatregelen.csv"), measures_table)

   #remove all sections that are not in analyse  in vakindeling_shape from measure_configuration_table
   #get the objectids of the vakindeling_shape that are in analyse
   in_analyse_section_ids = vakindeling_shape[vakindeling_shape['in_analyse'] == True].objectid.tolist()
   measure_configuration_table = measure_configuration_table.loc[in_analyse_section_ids]


   #small change for dstability case to make sure limited measures are considered (reduction of test runtime)
   if 'D-Stability' in request.node.callspec.id:
      #modify the configuration for section 7.
      measure_configuration_table['Grondversterking binnenwaarts D-Stability'] = measure_configuration_table['Grondversterking binnenwaarts']
      measure_configuration_table['Grondversterking binnenwaarts met stabiliteitsscherm D-Stability'] = measure_configuration_table['Grondversterking binnenwaarts met stabiliteitsscherm']
      #set for section 8 the 'D-stability' measures to False
      measure_configuration_table.loc[9, 'Grondversterking binnenwaarts D-Stability'] = False
      measure_configuration_table.loc[9, 'Grondversterking binnenwaarts met stabiliteitsscherm D-Stability'] = False
      #set for section 7 the normal measures to False
      measure_configuration_table.loc[8, 'Grondversterking binnenwaarts'] = False
      measure_configuration_table.loc[8, 'Grondversterking binnenwaarts met stabiliteitsscherm'] = False

      #modify the measure_table. Copy Grondversterking binnenwaarts and Grondversterking binnenwaarts met stabiliteitsscherm to the D-Stability measures
      measures_table.loc['Grondversterking binnenwaarts D-Stability'] = measures_table.loc['Grondversterking binnenwaarts']
      measures_table.loc['Grondversterking binnenwaarts met stabiliteitsscherm D-Stability'] = measures_table.loc['Grondversterking binnenwaarts met stabiliteitsscherm']
      # set max_inward to 5, crest step to 0.5 and max crest to 0.5
      measures_table.loc['Grondversterking binnenwaarts D-Stability', 'max_inward_reinforcement'] = 5
      measures_table.loc['Grondversterking binnenwaarts met stabiliteitsscherm D-Stability', 'max_inward_reinforcement'] = 5
      measures_table.loc['Grondversterking binnenwaarts D-Stability', 'max_crest_increase'] = 0.5
      measures_table.loc['Grondversterking binnenwaarts met stabiliteitsscherm D-Stability', 'max_crest_increase'] = 0.5
      measures_table.loc['Grondversterking binnenwaarts D-Stability', 'crest_step'] = 0.5
      measures_table.loc['Grondversterking binnenwaarts met stabiliteitsscherm D-Stability', 'crest_step'] = 0.5
   elif 'mixed' in request.node.callspec.id: #remove revetment measures for 2 sections in mixed case.
      measure_configuration_table.loc[7, 'Aanpassing bekleding'] = False
      measure_configuration_table.loc[8, 'Aanpassing bekleding'] = False

   #reset the index to start from 1 
   measure_configuration_table.index = np.arange(1, len(measure_configuration_table)+1)

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
   fill_measures(measure_table=measures_table, measure_configuration=measure_configuration_table, revetment= revetment)

   # for measure_set, measures_table in measure_tables.items():
   #    #get sections for which measure_set is relevant
   #    # section_list = vakindeling_shape[(vakindeling_shape.in_analyse == True) & (measures_per_section.values == measure_set)].vaknaam.tolist()
   #    fill_measures(measure_table=measures_table)

   #assert that the database is equal to the reference database
   _reference_database = _test_data_dir.joinpath('reference_databases','{}.db'.format(request.node.callspec.id))
   assert _reference_database.exists(), "No reference database available at {}".format(_reference_database)

   compare_databases(_output_path, _reference_database)

@pytest.mark.parametrize("traject,test_name,revetment", [
                                               pytest.param("14-1", "waterlevel", False, id="14-1 waterlevel hydranl")                                                   ])
def test_read_waterlevel_hydranl(traject: str, test_name: str, revetment: bool,  request: pytest.FixtureRequest):

   # remove output_path
   # get id of request
   _output_path = test_results.joinpath(request.node.name, "{}.db".format(request.node.callspec.id))
   if _output_path.parent.exists():
      shutil.rmtree(_output_path.parent)

   # get all the input data
   _test_data_dir = test_data.joinpath(traject)
   assert _test_data_dir.exists(), "No test data available at {}".format(
      _test_data_dir
   )

   # read the data for waterlevels
   _intermediate_dir = _test_data_dir.joinpath("decim_simple", "intermediate_results", "HR_results")
   waterlevel_table = read_waterlevel_data(_intermediate_dir.joinpath("waterlevel"), False)

   assert waterlevel_table["Beta"][0]==0.5182054462787409

@pytest.mark.parametrize("traject,test_name,revetment", [
                                               pytest.param("14-1", "overflow", False, id="14-1 overflow hydranl")                                                   ])
def test_read_overflow_hydranl(traject: str, test_name: str, revetment: bool,  request: pytest.FixtureRequest):

   # remove output_path
   # get id of request
   _output_path = test_results.joinpath(request.node.name, "{}.db".format(request.node.callspec.id))
   if _output_path.parent.exists():
      shutil.rmtree(_output_path.parent)

   # get all the input data
   _test_data_dir = test_data.joinpath(traject)
   assert _test_data_dir.exists(), "No test data available at {}".format(
      _test_data_dir
   )

   # read the data for overflow
   _intermediate_dir = _test_data_dir.joinpath("decim_simple", "intermediate_results", "HR_results")
   mechanism_data = {"overflow": read_overflow_data(_intermediate_dir.joinpath("overflow"), False)}

   assert mechanism_data["overflow"]["Beta"][0]==0.9771468439412871

@pytest.mark.parametrize("traject,test_name", [pytest.param("38-1", "base", id="38-1 base river case with direct piping")])
def test_direct_piping_input_written_to_database(traject: str, test_name: str, request: pytest.FixtureRequest):
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
   vakindeling_config = read_csv(_test_data_dir.joinpath("settings", "vakindeling_configuration.csv"),
                                    dtype={test_name:int}).rename(columns={test_name:'in_analyse'})

   #reset in_analyse in vakindeling_shape based on vakindeling_config. This is only for testdata.
   vakindeling_shape = pd.merge(vakindeling_shape.drop(columns=['in_analyse']),vakindeling_config[['objectid','in_analyse']],on='objectid')

   if 'kunstwerken' in vakindeling_shape.columns:  vakindeling_shape.drop(columns=['kunstwerken'],inplace=True)
   # read the HR_input
   HR_input = read_csv(
      _test_data_dir.joinpath("HRING_data_reference.csv"),
      dtype={'doorsnede':str}).drop_duplicates(subset=["doorsnede"])
   # read the data for different mechanisms

   # read the data for waterlevels
   _intermediate_dir = _test_data_dir.joinpath("intermediate")
   waterlevel_table = read_waterlevel_data(_intermediate_dir.joinpath("Waterstand"), True)


   #read mechanism_data and store in dictionary. We must have overflow and stabiliteit. Others are optional
   vakindeling_shape.astype({'overslag': str, 'stabiliteit':str})
   mechanism_data = {'overslag': read_overflow_data(_intermediate_dir.joinpath("Overslag"), True)}
   if 'D-Stability' in request.node.callspec.id: 
      mechanism_data['stabiliteit'] = read_stability_data(_intermediate_dir.joinpath("STBI_data_DStability.csv"))
   else:
      mechanism_data['stabiliteit'] = read_stability_data(_intermediate_dir.joinpath("STBI_data.csv"))

   try:
      vakindeling_shape.astype({'piping': str})
      # read the piping csv file
      piping_csv = _test_data_dir.joinpath("intermediate", "Piping_data.csv")
      mechanism_data['piping'] = read_and_validate_piping_data(piping_csv)
      # add the beta values
      mechanism_data['piping'].beta = 3.3
   except: #drop column
      vakindeling_shape.drop(columns=['piping'], inplace=True)            
   

   #merge the HR_input and stabiliteit input
       # merge parameters from HR_input with vakindeling_shape:
   vakindeling_shape = merge_to_vakindeling(vakindeling_shape, to_merge = HR_input[["doorsnede", "dijkhoogte", "kruindaling"]], left_key = ['overslag'], right_key = ['doorsnede'])

    # merge subsoil parameters with vakindeling if not present in vakindeling_shape
   if 'pleistoceendiepte' not in vakindeling_shape.columns:
      vakindeling_shape = merge_to_vakindeling(vakindeling_shape, to_merge = mechanism_data['stabiliteit'][["pleistoceendiepte", "deklaagdikte"]], left_key = ['stabiliteit'], right_key = ['doorsnede'])
   
   # # read the data for measures
   measures_table = read_measures_data(_generic_data_dir.joinpath("base_measures_totaal.csv"))

   #read the configuration
   measure_configuration_table, measures_table = read_measures_config(_test_data_dir.joinpath("settings","configuratie_maatregelen.csv"), measures_table)

   #remove all sections that are not in analyse  in vakindeling_shape from measure_configuration_table
   #get the objectids of the vakindeling_shape that are in analyse
   in_analyse_section_ids = vakindeling_shape[vakindeling_shape['in_analyse'] == True].objectid.tolist()
   measure_configuration_table = measure_configuration_table.loc[in_analyse_section_ids]

   #reset the index to start from 1 
   measure_configuration_table.index = np.arange(1, len(measure_configuration_table)+1)

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
   fill_measures(measure_table=measures_table, measure_configuration=measure_configuration_table)


   #assert that the database is equal to the reference database
   _reference_database = _test_data_dir.joinpath('reference_databases','{}.db'.format(request.node.callspec.id))
   assert _reference_database.exists(), "No reference database available at {}".format(_reference_database)

   compare_databases(_output_path, _reference_database)