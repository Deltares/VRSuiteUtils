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


def main(
    work_dir: Path,
    database_paths: list[Path],
    HydraRing_path: Path = Path(
        r"c:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236\config.sqlite"
    ),
    file_name: str = "HR_default.csv",
):
    """This is the main function of the workflow.
    It can be used to generate and evaluate Hydra-Ring computations for overflow for a given dataset"""

    # read HRING reference csv, and add to OverflowInput object
    hring_data = pd.read_csv(work_dir.parent.joinpath(file_name), index_col=0)
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
            loc_output_dir = work_dir.joinpath(
                database_path.stem, str(location.doorsnede)
            )
            if loc_output_dir.exists():
                loc_output_dir.rmdir()
            loc_output_dir.mkdir(parents=True, exist_ok=False)
            # make computation object
            computation = OverflowComputationInput()
            # data from input sheet:
            computation.fill_data(location)
            # add profile data:
            computation.get_prfl(work_dir.joinpath("prfl", location.prfl_bestand))
            # get config from hydraulic database:
            print(database_path)
            computation.get_HRING_config(database_path)
            # get critical discharge
            from tests import test_data

            computation.get_critical_discharge(
                test_data.joinpath("general", "critical_discharges.csv")
            )
            # make sql file
            print(loc_output_dir)
            print("")
            print(test_data.joinpath("general", "sql_reference_overflow.sql"))
            computation.make_SQL_file(
                loc_output_dir,
                test_data.joinpath("general", "sql_reference_overflow.sql"),
            )
            # make ini file:
            computation.make_ini_file(
                loc_output_dir,
                test_data.joinpath("general", "ini_reference_overflow.ini"),
                database_path,
                HydraRing_path.joinpath("config.sqlite"),
            )
            # run Hydra-Ring
            HydraRingComputation().run_hydraring(computation.ini_path)


if __name__ == "__main__":
    # MAIN SETTINGS:
    # working directory:
    work_dir = Path(r"c:\VRM\test_hydraring_workflow_wdod\overslag")

    # path to Hydra-Ring:
    HydraRing_path = Path(
        r"c:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236"
    )
    # list of paths to databases to be considered
    database_paths = [
        Path(r"c:\VRM\test_hydraring_workflow_wdod\HR\2023"),
        Path(r"c:\VRM\test_hydraring_workflow_wdod\HR\2100"),
    ]
    file_name = "HR_default.csv"
    main(work_dir, database_paths, HydraRing_path, file_name)
