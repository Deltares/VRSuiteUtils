import fileinput
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from itertools import pairwise

class HydraRingComputation:
    def __init__(self):
        pass

    def run_hydraring(self, hydraring_path: Path, inifile: Path):
        self.hydraring_path = Path(hydraring_path).joinpath("MechanismComputation.exe")
        subprocess.run([str(self.hydraring_path), str(inifile)], cwd=str(inifile.parent))

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
        for count, row in self.NumericsTable.iterrows():
            #if FORM is used, replace with FORM with Directional Sampling as backup.
            if row.CalculationMethod == 1.0:
                self.NumericsTable.at[count, "CalculationMethod"] = 11
                if self.MechanismID == 101:
                    print(f'CalculationMethod FORM voor Hydra-Ring is vervangen door FORM met Directional Sampling voor overslag op locatie {self.HRLocation}.')
                else:
                    print(f'CalculationMethod FORM voor Hydra-Ring is vervangen door FORM met Directional Sampling voor waterstand op locatie {self.HRLocation}.')


        cnx.close()

    def make_ini_file(self, path, reference_file, db_path, config_db_path):
        if config_db_path.name != "config.sqlite":
            config_db_path = config_db_path.joinpath("config.sqlite")
        new_ini = path.joinpath(self.name + ".ini")
        shutil.copy(reference_file, new_ini)

        for j, line in enumerate(fileinput.input(new_ini, inplace=1)):
            sys.stdout.write(line.replace("DIJKPAAL", self.name))
        for j, line in enumerate(fileinput.input(new_ini, inplace=1)):
            hlcds = list(db_path.glob("*hlcd*.sqlite"))
            if len(hlcds) > 1:
                raise ValueError(
                    "Meer dan 1 hlcd database gevonden in de database folder. Er mag maar 1 hlcd database aanwezig zijn."
                )
            sys.stdout.write(
                line.replace("DATABASEPATH", str(Path(os.getcwd()).joinpath(hlcds[0])))
            )
        for j, line in enumerate(fileinput.input(new_ini, inplace=1)):
            sys.stdout.write(line.replace("CONFIGDBPATH", str(config_db_path)))
        self.ini_path = new_ini
    
    @staticmethod
    def write_design_table(design_table, design_table_file_name):
        with open(design_table_file_name, 'w') as f:
            # Write the header
            # f.write('    '.join(design_table.columns) + '\n')
            # Write this as the header "                    Value      Failure probability     Return period (year)                     Beta"
            f.write("                    Value      Failure probability     Return period (year)                     Beta\n")


            # Write each row with different formats
            for _, row in design_table.iterrows():
                f.write(f"        {row['Value']:.4f}    "
                        f"{row['Failure probability']:.5e}    "
                        f"{row['Return period (year)']:.5e}    "
                        f"{row['Beta']:.4f}\n")

    @staticmethod
    def check_and_justify_HydraRing_data(design_table:pd.DataFrame,
                                          calculation_type:str,
                                          section_name:str = '',
                                          design_table_file:Path = None):
        # create a copy of the design table to avoid modifying the original design table
        design_table_temp = design_table.copy()

        # check if there are beta values in the design table below the threshold, if so, print a warning and remove these values. 
        threshold = 0.5

        if design_table_temp['Beta'].min() < threshold:
            # remove rows with beta values below the threshold
            design_table_temp = design_table_temp[design_table_temp['Beta'] >= threshold]
            print(f"Er zijn beta waarden onder de 0.5 gevonden voor {calculation_type} op dijkvak {section_name}. Deze waarden zijn verwijderd.")

        # set values and betas
        values = list(design_table_temp['Value'])
        betas = list(design_table_temp['Beta'])

        #check if values are increasing
        if not all(a < b for a, b in pairwise(values)):
            raise ValueError(f"Geimporteerde waarden voor {calculation_type} voor dijkvak {section_name} stijgen niet. Controleer de Hydra-Ring resultaten.")
            
        #check if betas are increasing
        if not all(a < b for a, b in pairwise(betas)):
            # modify betas to be increasing
            new_betas = [betas[0]]
            for i in range(1, len(betas)):
                beta_temp = betas[i]
                if beta_temp <= new_betas[i-1]:
                    new_betas.append(new_betas[i-1] + 0.001)
                else:
                    new_betas.append(betas[i])
            # new_betas = [betas[0]] + [max(betas[i], betas[i-1]) for i in range(1, len(betas))]
            print(f"Waarden voor {calculation_type} op dijkvak {section_name} stijgen niet, waarden zijn aangepast.")
            #print original and new betas
            print(f"Originele waarden: {betas}")
            print(f"Nieuwe waarden: {new_betas}")

            # replaces betas in the design_table with the new betas 
            design_table_temp['Beta'] = new_betas

        # check if design_table_temp equals design_table. If not, make a copy of the original file and write the new design_table to the file
        if not design_table_temp.equals(design_table):
            # make a copy of the original file
            before_correction= design_table_file.stem + design_table_file.suffix + ".bak"
            # if not design_table_file.parent.joinpath(before_correction).exists():
            #     before_correction = "BeforeCorrection_"+design_table_file.name
            shutil.copy(design_table_file, design_table_file.parent.joinpath(before_correction))
            print(f"Er is een kopie gemaakt van het originele bestand: {before_correction}")
            # Write to file: 
            HydraRingComputation.write_design_table(design_table_temp, design_table_file)
        
        return design_table_temp