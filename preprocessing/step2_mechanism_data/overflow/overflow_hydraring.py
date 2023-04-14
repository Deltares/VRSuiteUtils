## This script runs a multitude of HBN calculations for various locations read from an Excel sheet.
## It uses reference HBN calculation files which it copies many times.

import pandas as pd
import shutil
import fileinput
import sys
import os
import numpy as np
# import matplotlib.pyplot as plt
from pathlib import Path
import sqlite3
import subprocess

class HydraRingComputation:
    def __init__(self,HRING_path = r"C:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236\MechanismComputation.exe"):
        #default HRING_path is to latest Riskeer version.
        self.HydraRingPath =  Path(HRING_path)

    def run_hydraring(self,
            inifile: Path,
    ):
        #TODO aanpassen
        subprocess.run([self.HydraRingPath, str(inifile)], cwd=str(inifile.parent))


class OverflowComputation(HydraRingComputation):
    def get_critical_discharge(self,discharge_path):
        critical_discharges = pd.read_csv(discharge_path,index_col=0)
        try:
            subset = critical_discharges.loc[self.sod_class]

        except:
            raise Exception('Zodeklasse {} niet gevonden'.format(self.sod_class))

        if isinstance(subset,pd.Series):
            pass
        else:
            subset = subset.loc[subset.Golfhoogteklasse == self.wave_class].squeeze()

        self.mu = subset.mu
        self.sigma = subset.sigma


    def fill_data(self,data):
        self.name = data.dijkvak
        self.orientation = data.orientatie
        self.dike_height = data.dijkhoogte
        self.sod_class = data.zodeklasse
        self.wave_class = data.bovengrens_golfhoogteklasse
        self.HRLocation = data.HRLocation

    def get_HRING_config(self,db_path):

        #lees data voor config voor Numerics en TimeIntegration
        configfile = list(db_path.glob("*.config.sqlite"))[0]
        cnx = sqlite3.connect(configfile)
        self.TimeIntegrationScheme = np.int_(pd.read_sql_query("SELECT TimeIntegrationSchemeID FROM TimeIntegrationSettings WHERE CalculationTypeID=6 AND LocationID={}".format(self.HRLocation), cnx).values.flatten()[0])
        self.NumericsTable = pd.read_sql_query("SELECT * FROM NumericsSettings WHERE MechanismID=101 AND LocationID={}".format(self.HRLocation), cnx)
        cnx.close()
    def get_prfl(self, fileName):
        prfl = {}
        count_for = ''
        for line in fileinput.input(fileName):
            if 'VERSIE' in line:
                if line.split()[1] != '4.0':
                    raise Exception('prfl moet versie 4.0 zijn')
            elif 'ID' in line:
                prfl['ID'] = line.split()[1]
            elif 'RICHTING' in line:
                prfl['RICHTING'] = np.int_(line.split()[1])
                #TODO: maybe add a check with orientation property
            elif 'VOORLAND' in line:
                count_for = 'VOORLAND'
                count = 0
                total_count = np.int_(line.split()[1])
                voorland_array = np.empty((total_count, 3))
            elif 'KRUINHOOGTE' in line:
                prfl['KRUINHOOGTE'] = np.float_(line.split()[1])
            elif 'DIJK' in line:
                count_for = 'DIJK'
                count = 0
                total_count = np.int_(line.split()[1])
                dijk_array = np.empty((total_count, 3))
                pass
            elif 'DAM' in line:  # damtype
                prfl['DAM'] = line.split()[1]
            elif 'DAMWAND' in line:  # not used in Riskeer
                pass
            elif 'DAMHOOGTE' in line:
                prfl['DAMHOOGTE'] = line.split()[1]
            elif 'MEMO' in line:
                pass
            else:
                if count_for != '':
                    # add points for voorland or dijk
                    if count_for == 'VOORLAND':
                        voorland_array[count, :] = np.array(line.split(), dtype=np.float32)
                    elif count_for == 'DIJK':
                        dijk_array[count, :] = np.array(line.split(), dtype=np.float32)
                    count += 1
                    if total_count == count:
                        count = 0
                        count_for = ''
                else:
                    pass

        prfl['DIJK'] = dijk_array
        prfl['VOORLAND'] = voorland_array
        if prfl['DAM'] != '0': raise Exception('Profiel {} bevat een dam, dit is niet ondersteund'.format(fileName.stem))
        self.prfl = prfl
    def make_SQL_file(self,path,reference_file,lower_bound = -1,upper_bound=2,step_size=0.25):
        new_sql = path.joinpath(self.name + '.sql')
        shutil.copy(reference_file,new_sql)

        # changes values in sql for Location, orientation, claculation method and variables
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace('LocationName', self.name))
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace('HLCDID', str(self.HRLocation)))
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace('ORIENTATION', str(self.prfl['RICHTING'])))
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace('TimeIntegration', str(self.TimeIntegrationScheme)))
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace('Hmin', str(self.prfl['KRUINHOOGTE'] + lower_bound)))
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace('Hmax', str(self.prfl['KRUINHOOGTE'] + upper_bound)))
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace('Hstep', str(step_size)))
        # insert the correct parameters
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace('KRUINHOOGTE', str(self.prfl['KRUINHOOGTE'])))

        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace('MU_QC', str(self.mu / 1000)))
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            sys.stdout.write(line.replace('SIGMA_QC', str(self.sigma / 1000)))

        #TODO add proper Numerics settings

        #write profiles to file
        for j, line in enumerate(fileinput.input(new_sql, inplace=1)):
            if 'INSERTPROFILES' in line:
                #loop over points:
                for k in range(0,self.prfl['DIJK'].shape[0]):
                    sys.stdout.write('INSERT INTO [Profiles] VALUES ({:d}, {:d}, {:.3f}, {:.3f});'.format(1, k+1, self.prfl['DIJK'][k,0], self.prfl['DIJK'][k,1]) + '\n')
            elif 'INSERTCALCULATIONPROFILE' in line:
                #loop over points:
                for k in range(0,self.prfl['DIJK'].shape[0]):
                    sys.stdout.write('INSERT INTO [CalculationProfiles] VALUES ({:d}, {:d}, {:.3f}, {:.3f}, {:.3f});'.format(1, k+1, self.prfl['DIJK'][k,0], self.prfl['DIJK'][k,1], self.prfl['DIJK'][k,2]) + '\n')
            elif 'INSERTFORELANDGEOMETRY' in line:
                #loop over points:
                for k in range(0,self.prfl['VOORLAND'].shape[0]):
                    sys.stdout.write('INSERT INTO [FORELANDS] VALUES ({:d}, {:d}, {:.3f}, {:.3f});'.format(1, k+1, self.prfl['VOORLAND'][k,0], self.prfl['VOORLAND'][k,1]) + '\n')
            elif 'INSERTBREAKWATER' in line:
                pass
            else:
                sys.stdout.write(line)
        pass
    def make_ini_file(self,path,reference_file,db_path):
        new_ini = path.joinpath(self.name + '.ini')
        shutil.copy(reference_file,new_ini)

        for j, line in enumerate(fileinput.input(new_ini, inplace=1)):
            sys.stdout.write(line.replace('DIJKPAAL', self.name))
        for j, line in enumerate(fileinput.input(new_ini, inplace=1)):
            sys.stdout.write(line.replace('DATABASEPATH', str(db_path)))
        self.ini_path = new_ini
def modifyOverflowfile(i, filespath, filename, refsql, refini,database_loc,NumericsSettings,lowerbound= -1,upperbound=2):
    newsql = filespath.joinpath(filename,filename + '.sql')
    newini = filespath.joinpath(filename,filename + '.ini')
    workdir = filespath.joinpath(filename)
    if not os.path.exists(workdir):
        os.makedirs(workdir)
    shutil.copy(refsql, newsql)
    shutil.copy(refini, newini)

    #input prfl data.
    prfl = getPrfl(filespath.parent.joinpath('Input_Profielen',i.prfl_bestandnaam))
    if prfl['DAM'] != '0': raise Exception('Profielbestand {} bevat een dam, dit is niet ondersteund'.format(i.prfl_bestandsnaam))

    # changes values in sql for Location, orientation, claculation method and variables
    for j, line in enumerate(fileinput.input(newsql, inplace=1)):
        sys.stdout.write(line.replace('LocationName', i['Vaknaam']))
    for j, line in enumerate(fileinput.input(newsql, inplace=1)):
        sys.stdout.write(line.replace('HLCDID', str(i.LocationID)))
    for j, line in enumerate(fileinput.input(newsql, inplace=1)):
        # sys.stdout.write(line.replace('ORIENTATION', str(i.prfl_oriëntatie)))
        sys.stdout.write(line.replace('ORIENTATION', str(prfl['RICHTING'])))
    for j, line in enumerate(fileinput.input(newsql, inplace=1)):
        sys.stdout.write(line.replace('TimeIntegration', str(i.TimeIntegrationSchemeID)))
    for j, line in enumerate(fileinput.input(newsql, inplace=1)):
        sys.stdout.write(line.replace('Hmin', str(i.prfl_dijkhoogte+lowerbound)))
    for j, line in enumerate(fileinput.input(newsql, inplace=1)):
        sys.stdout.write(line.replace('Hmax', str(i.prfl_dijkhoogte+upperbound)))
    for j, line in enumerate(fileinput.input(newsql, inplace=1)):
        sys.stdout.write(line.replace('Hstep', str(0.25)))
    # insert the correct parameters
    for j, line in enumerate(fileinput.input(newsql, inplace=1)):
        sys.stdout.write(line.replace('KRUINHOOGTE', str(i.prfl_dijkhoogte)))

    for j, line in enumerate(fileinput.input(newsql, inplace=1)):
        sys.stdout.write(line.replace('MU_QC', str(i.mu_qc/1000)))
    for j, line in enumerate(fileinput.input(newsql, inplace=1)):
        sys.stdout.write(line.replace('SIGMA_QC', str(i.sigma_qc/1000)))


    #write profiles to file
    for j, line in enumerate(fileinput.input(newsql, inplace=1)):
        if 'INSERTPROFILES' in line:
            #loop over points:
            for k in range(0,prfl['DIJK'].shape[0]):
                sys.stdout.write('INSERT INTO [Profiles] VALUES ({:d}, {:d}, {:.3f}, {:.3f});'.format(1, k+1, prfl['DIJK'][k,0], prfl['DIJK'][k,1]) + '\n')
        elif 'INSERTCALCULATIONPROFILE' in line:
            #loop over points:
            for k in range(0,prfl['DIJK'].shape[0]):
                sys.stdout.write('INSERT INTO [CalculationProfiles] VALUES ({:d}, {:d}, {:.3f}, {:.3f}, {:.3f});'.format(1, k+1, prfl['DIJK'][k,0], prfl['DIJK'][k,1], prfl['DIJK'][k,2]) + '\n')
        elif 'INSERTFORELANDGEOMETRY' in line:
            #loop over points:
            for k in range(0,prfl['VOORLAND'].shape[0]):
                sys.stdout.write('INSERT INTO [FORELANDS] VALUES ({:d}, {:d}, {:.3f}, {:.3f});'.format(1, k+1, prfl['VOORLAND'][k,0], prfl['VOORLAND'][k,1]) + '\n')
        elif 'INSERTBREAKWATER' in line:
            pass
        else:
            sys.stdout.write(line)

    #TODO profiel goed in bestand zetten.
    # change values in ini
    for j, line in enumerate(fileinput.input(newini, inplace=1)):
        sys.stdout.write(line.replace('DIJKPAAL', i.Vaknaam))
    for j, line in enumerate(fileinput.input(newini, inplace=1)):
        sys.stdout.write(line.replace('DATABASEPATH', str(database_loc)))
    return newini

#First we generate all the input files
def main():
    PATH = Path(r'c:\PilotWSRL\Overslag')

    #Lees de locaties die moeten worden bekeken. Dit is standaarduitvoer uit de routine die de invoerbestanden maakt.
    inputfile = PATH.joinpath('GEKBdata.csv')

    #refereer naar basisbestanden met specifieke keys
    refsql = PATH.joinpath('Overslag_basis','sql_reference_overflow.sql')
    refini = PATH.joinpath('Overslag_basis','ini_reference_overflow.ini')

    #refereer naar de database die moet worden gebruikt.
    # database_locs = ['DatabaseOntwerp','DatabaseWBI']
    database_locs = ['DatabaseWBI','DatabaseOntwerp']

    for dbloc in database_locs:
        input = pd.read_csv(inputfile)
        database_loc = PATH.joinpath(dbloc)

        #lees data voor config voor Numerics en TimeIntegration
        configfile = list(database_loc.glob("*.config.sqlite"))[0]
        cnx = sqlite3.connect(configfile)
        TimeIntegrationTable = pd.read_sql_query("SELECT * FROM TimeIntegrationSettings", cnx)
        TimeIntegrationTable = TimeIntegrationTable.loc[TimeIntegrationTable.CalculationTypeID==6][['LocationID','TimeIntegrationSchemeID']]

        NumericsTable = pd.read_sql_query("SELECT * FROM NumericsSettings", cnx)
        NumericsTable = NumericsTable.loc[NumericsTable.MechanismID==101]

        input = input.merge(TimeIntegrationTable,on='LocationID')
        #add critical overtopping discharge
        critical_discharges = pd.read_csv(refini.parent.joinpath('critical_discharges.csv'))
        input = add_overtopping_discharges(input,critical_discharges)
        results_dir = PATH.joinpath('Resultaten_{}'.format(database_loc.stem))
        for count, location in input.iterrows():
            ini_file = modifyOverflowfile(location, results_dir,location.Vaknaam,refsql,refini, database_loc,NumericsTable.loc[NumericsTable.LocationId == location.LocationID])
            runHydraRing(ini_file)
        # exit()

if __name__ == '__main__':
    main()
