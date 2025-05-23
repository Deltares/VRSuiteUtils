import os
from pathlib import Path

import pandas as pd

from preprocessing.common_functions import check_string_in_list
from preprocessing.step2_mechanism_data.hydraring_computation import (
    HydraRingComputation,
)
from preprocessing.step2_mechanism_data.overflow.overflow_hydraring import (
    OverflowComputationInput,
)
from preprocessing.step2_mechanism_data.overflow.overflow_input import OverflowInput

from preprocessing.step4_build_sqlite_db.read_intermediate_outputs import read_design_table


def overflow_main(file_path: Path,
    database_paths: list[Path],
    profielen_dir: Path,
    HydraRing_path: Path,
    output_path: Path):
    """This is the main function of the workflow.
    It can be used to generate and evaluate Hydra-Ring computations for overflow for a given dataset"""

    _generic_data_dir = Path(__file__).absolute().parent.parent.joinpath('generic_data')

    # read HRING reference csv, and add to OverflowInput object
    hring_data = pd.read_csv(file_path, index_col=0)
    hring_data = hring_data.dropna(subset=['doorsnede'])
    overflow_input_object = OverflowInput()
    overflow_input_object.add_hring_data(hring_data)

    # if the hrlocation column is missing, or, if the hrlocation column is present, but empty,
    # then hrlocation is derived from the database, using hr_koppel
    if "hrlocation" not in hring_data.columns or hring_data["hrlocation"].isna().any():
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

        overflow_input_object.get_HRLocation(
            hrd_path, hlcd_path, overflow_input_object.hring_data
        )

    overflow_input_object.verify_and_filter_columns()
    # now we have a dataframe with all the data we need to generate the Hydra-Ring input files.
    # we can now loop over all the locations and databases to generate the Hydra-Ring input files.
    for database_path in database_paths:
        for count, location in overflow_input_object.hring_data.iterrows():
            # make output dir
            loc_output_dir = output_path.joinpath(database_path.stem, str(location.doorsnede))
            if loc_output_dir.exists():
                loc_output_dir.rmdir()
            loc_output_dir.mkdir(parents=True, exist_ok=False)
            # make computation object
            computation = OverflowComputationInput()
            # data from input sheet:
            computation.fill_data(location)
            # add profile data:
            computation.get_prfl(profielen_dir.joinpath( location.prfl_bestand))
            # get config from hydraulic database:
            print(database_path)
            computation.get_HRING_config(database_path)
            # get critical discharge

            computation.get_critical_discharge(
                _generic_data_dir.joinpath("hr_default_files", "critical_discharges.csv")
            )
            # make sql file
            print(loc_output_dir)
            print("")
            print(_generic_data_dir.joinpath("hr_default_files", "sql_reference_overflow.sql"))
            computation.make_SQL_file(
                loc_output_dir,
                _generic_data_dir.joinpath("hr_default_files", "sql_reference_overflow.sql"),
            )
            # make ini file:
            computation.make_ini_file(
                loc_output_dir,
                _generic_data_dir.joinpath("hr_default_files", "ini_reference_overflow.ini"),
                database_path,
                HydraRing_path.joinpath("config.sqlite"),
            )
            # run Hydra-Ring
            HydraRingComputation().run_hydraring(HydraRing_path, Path(os.getcwd()).joinpath(computation.ini_path))

            # read and check the resulting design table
            # design_table = HydraRingComputation().read_design_table(loc_output_dir)
            for loc_file in loc_output_dir.iterdir():
                if (loc_file.is_file()) and (loc_file.stem.lower().startswith("designtable")) and (loc_file.suffix.lower() == ".txt"):
                    design_table = read_design_table(loc_file)
                    HydraRingComputation().check_and_justify_HydraRing_data(design_table, calculation_type="Waterstand",
                                                                           section_name=loc_output_dir.name, design_table_file=loc_file)

