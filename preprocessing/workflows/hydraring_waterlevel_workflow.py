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

from preprocessing.step4_build_sqlite_db.read_intermediate_outputs import read_design_table


def waterlevel_main(file_path: Path,
    database_paths: list[Path],
    hydraring_path: Path,
        output_path: Path):

    """This is the main function of the workflow.
    It can be used to generate and evaluate Hydra-Ring computations for waterlevel for a given dataset"""
    _generic_data_dir = Path(__file__).absolute().parent.parent.joinpath('generic_data')
    # read HRING reference csv
    hring_data = pd.read_csv(file_path, index_col=0)
    hring_data = hring_data.dropna(subset=['doorsnede'])
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
            loc_output_dir = output_path.joinpath(database_path.stem, str(location.doorsnede))
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
            if "2100" not in str(database_path):
                computation.make_SQL_file(
                    loc_output_dir,
                    _generic_data_dir.joinpath("hr_default_files","sql_reference_waterlevel.sql"
                    ),
                )
            else:
                computation.make_SQL_file(
                    loc_output_dir,
                    _generic_data_dir.joinpath("hr_default_files","sql_reference_waterlevel.sql"
                    ),
                    t_2100=True,
                )
            # make ini file:
            computation.make_ini_file(
                loc_output_dir,
                _generic_data_dir.joinpath("hr_default_files","ini_reference_waterlevel.ini"),
                database_path,
                hydraring_path.joinpath("config.sqlite"),
            )
            
            # run Hydra-Ring
            HydraRingComputation().run_hydraring(hydraring_path, Path(os.getcwd()).joinpath(computation.ini_path))

            # read and check the resulting design table
            # design_table = HydraRingComputation().read_design_table(loc_output_dir)
            for loc_file in loc_output_dir.iterdir():
                if (loc_file.is_file()) and (loc_file.stem.lower().startswith("designtable")) and (loc_file.suffix.lower() == ".txt"):
                    design_table = read_design_table(loc_file)
                    HydraRingComputation().check_and_justify_HydraRing_data(design_table, calculation_type="Overflow",
                                                                           section_name=loc_output_dir.name, design_table_file=loc_file)
