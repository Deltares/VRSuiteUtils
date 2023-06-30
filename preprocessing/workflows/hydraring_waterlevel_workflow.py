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


def waterlevel_main(
    work_dir: Path,
    database_paths: list[Path],
    HydraRing_path: Path,
    file_name: str,
):
    """This is the main function of the workflow.
    It can be used to generate and evaluate Hydra-Ring computations for waterlevel for a given dataset"""

    # read HRING reference csv
    hring_data = pd.read_csv(work_dir.parent.joinpath(file_name), index_col=0)

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
            loc_output_dir = work_dir.joinpath(database_path.stem, str(location.doorsnede))
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
                HydraRing_path.joinpath("config.sqlite"),
            )
            # run Hydra-Ring
            HydraRingComputation().run_hydraring(HydraRing_path, computation.ini_path)
