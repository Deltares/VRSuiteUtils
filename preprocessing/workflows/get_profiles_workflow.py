import os, sys
from pathlib import Path
from preprocessing.step3_derive_general_data.derive_profiles import profile_generator
from preprocessing.step3_derive_general_data.derive_characteristic_points import obtain_characteristic_profiles

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
        print("dijkinfo folder created")

    # check if output_path.joinpath(AHN_profiles) exists, if not create it
    ahn_profiles_folder = output_path.joinpath("AHN_profiles")
    if not ahn_profiles_folder.exists():
        ahn_profiles_folder.mkdir()
        print("AHN_profiles folder created")
    # if the directory exists, but contains files or folders, delete all files and folders
    elif len(os.listdir(ahn_profiles_folder)) != 0:
        print('AHN_profiles folder is not empty')
        print('please empty the folder first')
        # stop the script
        sys.exit()
    else:
        pass


    # check if output_path.joinpath(characteristic_profiles) exists, if not create it
    characteristic_profiles_folder = output_path.joinpath("characteristic_profiles")
    if not characteristic_profiles_folder.exists():
        characteristic_profiles_folder.mkdir()
        print("characteristic_profiles folder created")
    elif len(os.listdir(characteristic_profiles_folder)) != 0:
        print('characteristic_profiles folder is not empty')
        print('please empty the folder first')
        # stop the script
        sys.exit()
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

    obtain_characteristic_profiles(input_dir=ahn_profiles_folder,
                                 output_dir=characteristic_profiles_folder)


if __name__ == '__main__':
    traject_id = '38-1'
    output_path = Path(r'c:\VRM\Gegevens 38-1\dijkinfo2')
    # flip_traject = False
    # flip_waterside = False
    dx = 2500


    main_traject_profiles(traject_id=traject_id,
                          output_path=output_path,
                          dx=dx,
                          # fsd=fsd,
                          # hld=hld,
                          # flip_traject=flip_traject,
                          # flip_waterside=flip_waterside,
                          )