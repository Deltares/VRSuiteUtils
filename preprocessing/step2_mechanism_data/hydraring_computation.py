import fileinput
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


class HydraRingComputation:
    def __init__(
        self,
        HRING_path=r"C:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236",
    ):
        # default HRING_path is to latest Riskeer version.
        self.HydraRingPath = Path(HRING_path).joinpath("MechanismComputation.exe")

    def run_hydraring(
        self,
        inifile: Path,
    ):
        subprocess.run([str(self.HydraRingPath), str(inifile)], cwd=str(inifile.parent))

    def get_HRING_config(self, db_path):

        # lees data voor config voor Numerics en TimeIntegration
        configfile = list(db_path.glob("*.config.sqlite"))[0]
        print(configfile)
        cnx = sqlite3.connect(configfile)
        self.TimeIntegrationScheme = np.int_(
            pd.read_sql_query(
                "SELECT TimeIntegrationSchemeID FROM TimeIntegrationSettings WHERE CalculationTypeID={} AND LocationID={}".format(
                    self.CalculationTypeID, self.HRLocation
                ),
                cnx,
            ).values.flatten()[0]
        )
        self.NumericsTable = pd.read_sql_query(
            "SELECT * FROM NumericsSettings WHERE MechanismID={} AND LocationID={}".format(
                self.MechanismID, self.HRLocation
            ),
            cnx,
        )
        cnx.close()

    def make_ini_file(self, path, reference_file, db_path, config_db_path):
        if config_db_path.name != "config.sqlite":
            config_db_path = config_db_path.joinpath("config.sqlite")
        new_ini = path.joinpath(self.name + ".ini")
        shutil.copy(reference_file, new_ini)

        for j, line in enumerate(fileinput.input(new_ini, inplace=1)):
            sys.stdout.write(line.replace("DIJKPAAL", self.name))
        for j, line in enumerate(fileinput.input(new_ini, inplace=1)):
            sys.stdout.write(
                line.replace("DATABASEPATH", str(Path(os.getcwd()).joinpath(db_path)))
            )
        for j, line in enumerate(fileinput.input(new_ini, inplace=1)):
            sys.stdout.write(line.replace("CONFIGDBPATH", str(config_db_path)))
        self.ini_path = new_ini
