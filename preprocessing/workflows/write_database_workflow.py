from pathlib import Path
import pandas as pd
import geopandas as gpd
from vrtool.orm.orm_controllers import *
from preprocessing.step4_build_sqlite_db.read_intermediate_outputs import *
from preprocessing.step4_build_sqlite_db.write_database import *
import random
def read_csv_linesep(file_path, **kwargs):
    try:
        df = pd.read_csv(file_path, sep = ',', lineterminator = '\n', **kwargs)
    except:
        df = pd.read_csv(file_path, sep = ';', lineterminator = '\n', **kwargs)
    return df

def write_config_file(output_dir : Path, traject_name : str, database_path : Path):
    # make a json with traject = traject_name and input_database_path = database_path
    config = {'traject': traject_name,
              'input_database_path': str(database_path.absolute()).replace('\\','/')}

    with open(output_dir.joinpath('config.json'), 'w') as f:
        json.dump(config, f, indent=1)
def write_database_main(traject_name : str,
                        vakindeling_geojson : Path,
                        characteristic_profile_csv : Path,
                        building_csv_path : Path,
                        output_dir : Path,
                        output_db_name : str,
                        hr_input_csv: Path,
                        waterlevel_results_path: Path,
                        overflow_results_path : Path,
                        piping_path = None,
                        stability_path = None,
                        revetment_path = None,
                        ):

    # check if output_path exists, if not create it
    if not output_dir.exists():
        output_dir.mkdir()
        print("output folder created")
    else:
        #check if the output database already exists
        if (output_dir / output_db_name).exists():
            raise Exception("Uitvoerdatabase bestaat al. Verwijder deze eerst of kies een andere naam")

    _generic_data_dir = Path(__file__).absolute().parent.parent.joinpath('generic_data')

    # load the vakindeling geojson with in_analyse column as integer
    vakindeling_shape = gpd.read_file(vakindeling_geojson)
    vakindeling_shape = vakindeling_shape.astype({'in_analyse':int, 'stabiliteit': str, 'piping': str, 'overslag': str, 'bekledingen': str})

    # load HR input csv
    HR_input = read_csv_linesep(hr_input_csv,index_col=0, dtype={'doorsnede':str})

    #read water levels
    waterlevel_results = read_waterlevel_data(waterlevel_results_path)

    #read mechanism_data and store in dictionary. We must have overflow. Others are optional
    mechanism_data = {'overslag': read_overflow_data(overflow_results_path)}
    if piping_path != None: mechanism_data['piping'] = read_piping_data(piping_path)
    if stability_path != None: mechanism_data['stabiliteit'] = read_stability_data(stability_path)
    if revetment_path != None:
        revetment_path = Path(revetment_path)
        mechanism_data['slope_part_table'], mechanism_data['rel_GEBU_table'], mechanism_data['rel_ZST_table']  = read_revetment_data(revetment_path)

    # read the data for bebouwing
    bebouwing_table = read_bebouwing_data(building_csv_path)

    # read the data for measures

    measures_table = read_measures_data(_generic_data_dir.joinpath("base_measures_totaal.csv"))


    # read the data for profilepoints
    profile_table = read_profile_data(characteristic_profile_csv)
    # check if the input directories exists

    # now we are going to write it to the database
    initialize_database(output_dir.joinpath(output_db_name))
    assert output_dir.joinpath(output_db_name).exists(), "Database file was not created."

    db_obj = open_database(output_dir.joinpath(output_db_name))

    # diketrajectinfo
    fill_diketrajectinfo_table(traject=traject_name, length=vakindeling_shape.m_eind.max())
    # sectiondata
    fill_sectiondata_table(
        traject=traject_name,
        shape_file=vakindeling_shape,
        HR_input=HR_input,
        geo_input=mechanism_data['stabiliteit'][["deklaagdikte", "pleistoceendiepte"]],
    )
    # waterleveldata
    fill_buildings(buildings=bebouwing_table)

    fill_waterleveldata(waterlevel_table=waterlevel_results, shape_file=vakindeling_shape)

    fill_profiles(profile_table)

    # fill all the mechanisms
    fill_mechanisms(mechanism_data=mechanism_data, shape_file=vakindeling_shape)

    # fill measures
    fill_measures(measure_table=measures_table)

    #write a config file
    write_config_file(output_dir, traject_name, output_dir.joinpath(output_db_name))

if __name__ == '__main__':
    traject_name = "31-1"
    vakindeling_geojson =       Path(r'c:\vrm_test\scheldestromen_database_31_1\Vakindeling_31-1.geojson')
    characteristic_profile_csv= Path(r'c:\vrm_test\scheldestromen_database_31_1\profielen\representative_profiles\selected_profiles.csv')
    building_csv_path =         Path(r'c:\vrm_test\scheldestromen_database_31_1\bebouwing\building_count_traject31-1.csv')
    output_dir =                Path(r'c:\vrm_test\scheldestromen_database_31_1\database')
    output_db_name =            f'traject_31_1.db'
    hr_input_csv =              Path(r'c:\vrm_test\scheldestromen_database_31_1\HR_default_31-1.csv')
    waterlevel_results_path =   Path(r'c:\vrm_test\scheldestromen_database_31_1\waterlevel')
    overflow_results_path =     Path(r'c:\vrm_test\scheldestromen_database_31_1\overflow')
    piping_path =               Path(r'c:\vrm_test\scheldestromen_database_31_1\piping_default_31-1.csv')
    stability_path =            Path(r'c:\vrm_test\scheldestromen_database_31_1\Stabiliteit_default_31-1.csv')
    revetment_path =            Path(r"c:\vrm_test\scheldestromen_database_31_1\bekleding")


    write_database_main(traject_name                =   traject_name,
                        vakindeling_geojson         =   vakindeling_geojson,
                        characteristic_profile_csv  =   characteristic_profile_csv,
                        building_csv_path           =   building_csv_path,
                        output_dir                  =   output_dir,
                        output_db_name              =   output_db_name,
                        hr_input_csv                =   hr_input_csv,
                        waterlevel_results_path     =   waterlevel_results_path,
                        overflow_results_path       =   overflow_results_path,
                        piping_path                 =   piping_path,
                        stability_path              =   stability_path,
                        revetment_path              =   revetment_path,
                        )