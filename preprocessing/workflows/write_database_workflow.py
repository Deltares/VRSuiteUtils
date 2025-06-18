from pathlib import Path
import pandas as pd
import geopandas as gpd
from vrtool.orm.orm_controllers import *
from preprocessing.step4_build_sqlite_db.read_intermediate_outputs import *
from preprocessing.step4_build_sqlite_db.write_database import *
import shutil

import logging
from preprocessing.common_functions import log_and_raise_error


def read_csv_linesep(file_path, **kwargs):
    try:
        df = pd.read_csv(file_path, sep = ',', **kwargs)
    except:
        df = pd.read_csv(file_path, sep = ';', lineterminator = '\n', **kwargs)
    df = df.dropna(subset=['doorsnede'])
    return df

def write_config_file(output_dir : Path, traject_name : str, database_name : str, exclude_mechanisms = None):
    # make a json with traject = traject_name and input_database_path = database_path
    
    if exclude_mechanisms is None:
        config = {'traject': traject_name,
                  'T': [0, 20, 25, 50, 75, 100],
                  'input_database_name': str(database_name),
                  'input_directory': None,
                  'output_directory': "Basisberekening"}
    else:
        config = {'traject': traject_name,
                  'T': [0, 20, 25, 50, 75, 100],
                  'excluded_mechanisms': exclude_mechanisms,
                  'input_database_name': str(database_name),
                  'input_directory': None,
                  'output_directory': "Basisberekening"}

    with open(output_dir.joinpath('config.json'), 'w') as f:
        json.dump(config, f, indent=1)

def merge_to_vakindeling(vakindeling_shape: gpd.GeoDataFrame, to_merge: pd.DataFrame, left_key: str, right_key: str):
    return vakindeling_shape.merge(to_merge.drop_duplicates(), left_on=left_key, right_on=right_key, how='left')

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
                        measure_configuration = None,
                        ):

    # check if output_path exists, if not create it
    if not output_dir.exists():
        output_dir.mkdir()
        logging.info("Uitvoermap aangemaakt")
    else:
        #check if the output database already exists
        if (output_dir / output_db_name).exists():
            log_and_raise_error("Uitvoerdatabase bestaat al. Verwijder deze eerst of kies een andere naam", FileExistsError)

    _generic_data_dir = Path(__file__).absolute().parent.parent.joinpath('generic_data')

    # load the vakindeling geojson with in_analyse column as integer
    vakindeling_shape = gpd.read_file(vakindeling_geojson)
    vakindeling_shape = vakindeling_shape.astype({'in_analyse':int, 'overslag': str, 'stabiliteit': str})
    if 'kunstwerken' in vakindeling_shape.columns: vakindeling_shape.drop(columns=['kunstwerken'],inplace=True)
    logging.info(f"Vakindeling geojson bestand succesvol ingelezen.")

    # load HR input csv
    HR_input = read_csv_linesep(hr_input_csv,index_col=0, dtype={'doorsnede':str})

    #read water levels
    waterlevel_results = read_waterlevel_data(waterlevel_results_path, use_hydraring=True)
    logging.info(f"Waterstandsdata succesvol ingelezen.")

    #read mechanism_data and store in dictionary. We must have overflow and stabiliteit. Others are optional
    mechanism_data = {'overslag': read_overflow_data(overflow_results_path, use_hydraring=True), 
                      'stabiliteit': read_stability_data(stability_path),}
    logging.info(f"Data voor overslag en stabiliteit succesvol ingelezen.")

    if piping_path != None: 
        vakindeling_shape.astype({'piping': str})
        mechanism_data['piping'] = read_and_validate_piping_data(piping_path)
        logging.info(f"Data voor piping succesvol ingelezen.") 

    else: #drop column
        vakindeling_shape.drop(columns=['piping'], inplace=True)  
        logging.info(f"Geen piping data aanwezig, kolom 'piping' verwijderd uit vakindeling.")          
    
    if revetment_path != None:
        mechanism_data['slope_part_table'], mechanism_data['rel_GEBU_table'], mechanism_data['rel_ZST_table']  = read_revetment_data(revetment_path)
        logging.info(f"Data voor bekleding succesvol ingelezen.")
    else:
        vakindeling_shape.drop(columns=['bekledingen'], inplace=True)
        logging.info(f"Geen bekledingen data aanwezig, kolom 'bekledingen' verwijderd uit vakindeling.")

    # merge parameters from HR_input with vakindeling_shape:
    vakindeling_shape = merge_to_vakindeling(vakindeling_shape, to_merge = HR_input[["doorsnede", "dijkhoogte", "kruindaling"]], left_key = ['overslag'], right_key = ['doorsnede'])

    # merge subsoil parameters with vakindeling if not present in vakindeling_shape
    if 'pleistoceendiepte' not in vakindeling_shape.columns:
        try:
            # takes only the pleistoceendiepte and deklaagdikte from the first scenario of each doorsnede
            stabiliteit_df_for_merge = mechanism_data['stabiliteit'][~mechanism_data['stabiliteit'].index.duplicated(keep='first')]
            vakindeling_shape = merge_to_vakindeling(vakindeling_shape, to_merge = stabiliteit_df_for_merge[["pleistoceendiepte", "deklaagdikte"]], left_key = ['stabiliteit'], right_key = stabiliteit_df_for_merge.index)
            logging.info(f"Pleistoceendiepte en deklaagdikte niet gevonden in vakindeling. Succesvol toegevoegd op basis van stabiliteit data.")
        except:
            log_and_raise_error('Deklaagdikte en pleistoceendiepte zijn niet aanwezig in de vakindeling, en ook niet in de stabiliteit.CSV', ValueError)


    # read the data for bebouwing
    bebouwing_table = read_bebouwing_data(building_csv_path)
    logging.info(f"Data bebouwing succesvol ingelezen.")

    # read the data for measures
    measures_table = read_measures_data(_generic_data_dir.joinpath("base_measures_totaal.csv"))
    logging.info(f"Tabel met basismaatregelen succesvol ingelezen.")

    if measure_configuration is not None:
        measure_configuration_table, measures_table = read_measures_config(measure_configuration, measures_table)
        logging.info(f"Configuratie van maatregelen per dijkvak succesvol ingelezen.")


    # read the data for profilepoints
    profile_table = read_profile_data(characteristic_profile_csv)
    logging.info(f"Dijkprofielen per vak succesvol ingelezen.")

    # check if the input directories exists

    # now we are going to write it to the database
    initialize_database(output_dir.joinpath(output_db_name))
    if not output_dir.joinpath(output_db_name).exists():
        log_and_raise_error("Database bestand niet succesvol aangemaakt", FileExistsError)
    logging.info(f"Database bestand {output_db_name} succesvol aangemaakt in {output_dir}.")

    db_obj = open_database(output_dir.joinpath(output_db_name))
    logging.info(f"Verbinding met database gelegd.")

    # diketrajectinfo
    fill_diketrajectinfo_table(traject=traject_name, length=vakindeling_shape.m_eind.max())

    # sectiondata
    fill_sectiondata_table(
        traject=traject_name,
        shape_file=vakindeling_shape,
    )
    # waterleveldata
    fill_buildings(buildings=bebouwing_table)

    fill_waterleveldata(waterlevel_table=waterlevel_results, shape_file=vakindeling_shape)

    fill_profiles(profile_table)

    # fill all the mechanisms
    fill_mechanisms(mechanism_data=mechanism_data, shape_file=vakindeling_shape)

    # fill measures
    fill_measures(measure_table=measures_table, measure_configuration=measure_configuration_table, revetment = revetment_path)

    #write a config file
    if revetment_path != None:
        write_config_file(output_dir, traject_name, output_db_name,
                          exclude_mechanisms=['HYDRAULIC_STRUCTURES'])
    else:
        write_config_file(output_dir, traject_name, output_db_name,
                          exclude_mechanisms=['REVETMENT', 'HYDRAULIC_STRUCTURES'])
    logging.info(f"Configuratiebestand succesvol aangemaakt in {output_dir}.")

    #copy the vakindeling to the output directory
    shutil.copy(vakindeling_geojson, output_dir.joinpath(traject_name + '.geojson'))
    logging.info(f"Vakindeling geojson bestand succesvol gekopieerd naar {output_dir}.")

    logging.info(f"Database {output_db_name} gegenereerd voor traject {traject_name} in {output_dir}.")
    # close the database
