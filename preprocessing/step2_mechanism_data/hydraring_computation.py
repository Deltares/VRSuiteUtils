import sqlite3
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd


class HydraRingComputation:
    def __init__(self,HRING_path = r"C:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236\MechanismComputation.exe"):
        #default HRING_path is to latest Riskeer version.
        self.HydraRingPath =  Path(HRING_path)

    def run_hydraring(self,
            inifile: Path,
    ):
        subprocess.run([str(self.HydraRingPath), str(inifile)], cwd=str(inifile.parent))

    def get_HRING_config(self,db_path,CalculationTypeID,MechanismID):

        #lees data voor config voor Numerics en TimeIntegration
        configfile = list(db_path.glob("*.config.sqlite"))[0]
        cnx = sqlite3.connect(configfile)
        self.TimeIntegrationScheme = np.int_(pd.read_sql_query("SELECT TimeIntegrationSchemeID FROM TimeIntegrationSettings WHERE CalculationTypeID={}} AND LocationID={}".format(self,CalculationTypeID,self.HRLocation), cnx).values.flatten()[0])
        self.NumericsTable = pd.read_sql_query("SELECT * FROM NumericsSettings WHERE MechanismID={}} AND LocationID={}".format(MechanismID,self.HRLocation), cnx)
        cnx.close()
