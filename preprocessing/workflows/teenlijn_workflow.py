from pathlib import Path

from preprocessing.step3_derive_general_data.get_binnenteenlijn import derive_teenlijn


def main_teenlijn(
    characteristic_profile_dir: Path,
    profile_path: Path,
    output_dir: Path
    ):

    # check if output_path exists, if not create it
    if not output_dir.exists():
        output_dir.mkdir()
        print("teenlijn folder created")



    derive_teenlijn(characteristic_profile_dir,
                    profile_path,
                    output_dir)

if __name__ == '__main__':
    characteristic_profile_dir = Path(r'c:\VRM\Gegevens 38-1\dijkinfo\characteristic_profiles')
    profile_path = Path(r'c:\VRM\Gegevens 38-1\dijkinfo2\traject_profiles.csv')
    output_dir = Path(r"c:\VRM\Gegevens 38-1\dijkinfo2\teenlijn")

    main_teenlijn(characteristic_profile_dir,
                        profile_path,
                        output_dir)