import shutil
from pathlib import Path

import pytest
from vrtool.orm.models import *
from vrtool.orm.orm_controllers import *

from preprocessing.step4_build_sqlite_db.read_intermediate_outputs import *
from preprocessing.step4_build_sqlite_db.write_database import *


@pytest.mark.parametrize("traject",[pytest.param('38-1', id="Traject 38-1")])
def test_make_database(traject: str):
   # remove output_path
   _output_path = Path('test_results').joinpath(traject,'Database','test.db')
   if _output_path.parent.exists():
      shutil.rmtree(_output_path.parent)

   #get all the input data
   #read the vakindeling shape
   _test_data_dir = Path("test_data").joinpath(traject)
   assert _test_data_dir.exists(), "No test data available at {}".format(_test_data_dir)

   shapefile = gpd.read_file(_test_data_dir.joinpath('reference_shape.geojson'))
   #read the HR_input
   HR_input = pd.read_csv(_test_data_dir.joinpath('HRING_data_reference.csv')).drop_duplicates(subset=['doorsnede'])
   #read the data for different mechanisms

    #read the data for waterlevels
   _intermediate_dir = _test_data_dir.joinpath('intermediate')
   waterlevel_table = read_waterlevel_data(_intermediate_dir.joinpath('Waterstand'))

    #read the data for overflow
   overflow_table = read_overflow_data(_intermediate_dir.joinpath('Overslag'))

    #read the data for piping
   piping_table = read_piping_data(_intermediate_dir.joinpath('Piping_data.csv'))

   #read the data for stability
   stability_table = read_stability_data(_intermediate_dir.joinpath('STBI_data.csv'))

   #read the data for bebouwing
   bebouwing_table = read_bebouwing_data(_intermediate_dir.joinpath('Bebouwing_data.csv'))

   #read the data for measures
   measures_table = read_measures_data(_intermediate_dir.joinpath('base_measures.csv'))

   #read the data for profilepoints
   profile_table = read_profilepoints_data(_intermediate_dir.joinpath('Profielen'))

   initialize_database(_output_path)

   db_obj = open_database(_output_path)

   #diketractinfo
   fill_diketrajectinfo_table(traject=traject)
   #sectiondata
   fill_sectiondata_table(traject=traject,shape_file=shapefile, HR_input=HR_input, geo_input = stability_table[['deklaagdikte','pleistoceendiepte']])
   #waterleveldata
   fill_buildings(buildings=bebouwing_table)

   fill_waterleveldata(waterlevel_table=waterlevel_table,shape_file=shapefile)

   fill_profilepoints(profile_points=profile_table,shape_file=shapefile)

   # fill all the mechanisms
   # fill_mechanisms(overflow_table=overflow_table,piping_table=piping_table,stability_table=stability_table, shape_file=shapefile)

   # fill measures
   fill_measures(measure_table=measures_table)

   # SectionData(dike_traject=)
   # SectionData.get_or_create()
   #peewee doc

   #start with trajectinfo
   #then sectiondata
   #test_orm_controllers ".create(ojbectwith info). updating values can be done through loop
   print(db_obj)
   #
   # db = SQLiteDatabase(output_path,traject)
   #
   # #load vakindeling shape
   # db.load_vakindeling_shape(shape_path=Path('test_data').joinpath('38-1','reference_shape.shp'))
   #
   # db.write_diketrajectinfo_table()
   #
   # db.write_sectiondata_table()

   # #load waterleveldata
   # db.load_waterleveldata()
   # #load overflowdata
   # db.load_overflowdata()
   #
   # db.load_pipingdata()
   #
   # db.load_stabilitydata()

   #load
   #write trajectinfo

   
   # assert db.output_path == output_path
   # assert db.traject == traject
   # assert db.cnx is not None
   # assert db.cursor is not None
   # assert db.cursor.execute('SELECT SQLITE_VERSION()').fetchone()[0] == '3.31.1'
