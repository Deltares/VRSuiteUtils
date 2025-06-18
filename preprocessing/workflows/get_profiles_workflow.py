import os, sys
from pathlib import Path
from preprocessing.step3_derive_general_data.derive_profiles import profile_generator
from preprocessing.step3_derive_general_data.derive_characteristic_points import obtain_characteristic_profiles

import logging
from preprocessing.common_functions import log_and_raise_error

def main_traject_profiles(traject_id: str,
                          output_path: Path,
                          dx: int,
                          fsd: int,
                          hld: int,
                          NBPW_shape_path=False,
                          flip_traject: bool=False,
                          flip_waterside: bool=False,
                          ):

    # check if output_path exists, if not create it
    if not output_path.exists():
        output_path.mkdir()
        logging.info("Uitvoermap aangemaakt")

    # check if output_path.joinpath(AHN_profiles) exists, if not create it
    ahn_profiles_folder = output_path.joinpath("ahn_profielen")
    if not ahn_profiles_folder.exists():
        ahn_profiles_folder.mkdir()
        logging.info("AHN_profiles folder aangemaakt")
    # if the directory exists, but contains files or folders, delete all files and folders
    elif len(os.listdir(ahn_profiles_folder)) != 0:
        log_and_raise_error('AHN_profiles folder is not empty. Please empty the folder first and rerun the workflow.',
                            FileExistsError)

    else:
        pass


    # check if output_path.joinpath(characteristic_profiles) exists, if not create it
    characteristic_profiles_folder = output_path.joinpath("kar_profielen")
    if not characteristic_profiles_folder.exists():
        characteristic_profiles_folder.mkdir()
        logging.info("characteristic_profiles folder aangemaakt")
    elif len(os.listdir(characteristic_profiles_folder)) != 0:
        log_and_raise_error('characteristic_profiles folder is not empty. Please empty the folder first and rerun the workflow.',
                            FileExistsError)
    else:
        pass
    
    
    profile_generator(traject_id=traject_id,
                      output_path=output_path,
                      foldername_output_csv=ahn_profiles_folder,
                      NBPW_shape_path=NBPW_shape_path,
                      dx=dx,
                      fsd=fsd,
                      hld=hld,
                      flip_traject=flip_traject,
                      flip_waterside=flip_waterside,
                      )
    logging.info(f"Alle AHN4 profielen zijn opgeslagen in {ahn_profiles_folder}\n")

    logging.info("Start met het bepalen van karakteristieke profielen.")
    obtain_characteristic_profiles(input_dir=ahn_profiles_folder,
                                 output_dir=characteristic_profiles_folder)
    
    logging.info(f"Karakteristieke profielen zijn opgeslagen in {characteristic_profiles_folder}\n")

