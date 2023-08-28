import os
from pathlib import Path

import pandas as pd

from preprocessing.common_functions import check_string_in_list
from preprocessing.step2_mechanism_data.hydraring_computation import (
    HydraRingComputation,
)
from preprocessing.step2_mechanism_data.overflow.overflow_input import OverflowInput
from preprocessing.step2_mechanism_data.waterlevel.waterlevel_hydraring import (
    WaterlevelComputationInput,
)


def waterlevel_main(file_path: Path,
    database_paths: list[Path],
    hydraring_path: Path,
        output_path: Path):

    """This is the main function of the workflow.
    It can be used to generate and evaluate Hydra-Ring computations for waterlevel for a given dataset"""

    # read HRING reference csv
    hring_data = pd.read_csv(file_path, index_col=0)

    # if the hrlocation column is missing, or, if the hrlocation column is present, but empty,
    # then hrlocation is derived from the database, using hr_koppel
    if ("hrlocation" not in hring_data.columns or hring_data["hrlocation"].isna().any()):
        hrd_path = [
            pad
            for pad in database_paths[0].glob("*.sqlite")
            if not check_string_in_list(pad.name, [".config", "hlcd"])
        ][0]
        hlcd_path = [
            pad
            for pad in database_paths[0].glob("*.sqlite")
            if check_string_in_list(pad.name, ["hlcd"])
        ][0]

        hring_data = OverflowInput.get_HRLocation(hrd_path, hlcd_path, hring_data)

    # we can now loop over all the locations and databases to generate the Hydra-Ring input files.
    for database_path in database_paths:
        for count, location in hring_data.iterrows():
            # make output dir
            loc_output_dir = output_path.joinpath(str(location.doorsnede))
            if loc_output_dir.exists():
                loc_output_dir.rmdir()
            loc_output_dir.mkdir(parents=True, exist_ok=False)
            # make computation object
            computation = WaterlevelComputationInput()
            # data from input sheet:
            computation.fill_data(location)
            # get config from hydraulic database:
            computation.get_HRING_config(database_path)
            # make sql file. Make sure that range is adjusted for 2100
            from tests import test_data
            if "2100" not in str(database_path):
                computation.make_SQL_file(
                    loc_output_dir,
                    test_data.joinpath("general", "sql_reference_waterlevel.sql"
                    ),
                )
            else:
                computation.make_SQL_file(
                    loc_output_dir,
                    test_data.joinpath("general", "sql_reference_waterlevel.sql"
                    ),
                    t_2100=True,
                )
            # make ini file:
            computation.make_ini_file(
                loc_output_dir,
                test_data.joinpath("general", "ini_reference_waterlevel.ini"),
                database_path,
                hydraring_path.joinpath("config.sqlite"),
            )
            # run Hydra-Ring
            HydraRingComputation().run_hydraring(hydraring_path, computation.ini_path)

# # file_name: str,
# #     database_paths: list[Path],
# #     output_path: Path
#

# if __name__ == '__main__':
#     # input paths
#     # Path_prf = Path(
#     #     r'C:\Users\wopereis\OneDrive - Stichting Deltares\Documents\A - Projects\2023 Veiligheidsrendement\A - Sensitivity analysis\Sensitivity analyse GEKB\Overslag\prfl')
#     Path_results = Path(
#         r'C:\Users\wopereis\OneDrive - Stichting Deltares\Documents\A - Projects\2023 Veiligheidsrendement\A - Sensitivity analysis\Sensitivity analyse GEKB\Overslag\Result test')
#     Path_HR = [Path(
#         r"C:\Users\wopereis\OneDrive - Stichting Deltares\Documents\A - Projects\2023 Veiligheidsrendement\A - Sensitivity analysis\Sensitivity analyse GEKB\Overslag\DatabaseWBI")]
#     Path_file = r"C:\Users\wopereis\OneDrive - Stichting Deltares\Documents\A - Projects\2023 Veiligheidsrendement\A - Sensitivity analysis\Sensitivity analyse GEKB\Overslag\GEKBdata_base.csv"
#
#     waterlevel_main(Path_file,Path_HR, Path_results)