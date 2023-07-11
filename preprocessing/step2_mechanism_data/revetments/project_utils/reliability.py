# -*- coding: utf-8 -*-
"""
Created on Wed Feb  1 11:41:52 2023

@author: wojciech
"""

import pandas as pd
import os
import sqlite3
from project_utils.makeHYRProjectFiles import make_sql_qvariant, make_sql_MHW, make_ini_file

def read_beta_mech(fileName):
    
    # read beta for failure mechanism computation P(Z<0)
    con = sqlite3.connect(fileName)
    
    df = pd.read_sql_query('SELECT * FROM DesignBeta WHERE LevelTypeId = 4',con)

    beta = df.BetaValue[0]

    con.close()
    
    return beta

def read_design_value(fileName):
    
    # read design value
    con = sqlite3.connect(fileName)
    
    df = pd.read_sql_query('SELECT * FROM IterateToGivenBetaConvergence',con)
    
    val = df.Value[df.OuterIterationId.max()-1]
    
    con.close()
    
    return val

def read_qvariant(fileName):
    
    # read Q-variant results
    output = {}
    
    con = sqlite3.connect(fileName)
    
    df = pd.read_sql_query('SELECT * FROM QVariantResults',con)
    
    output['h'] = df.WaterLevel[0]
    output['Hs'] = df.WaveHeight[0]
    output['Tp'] = df.WavePeriod[0]
    output['dir'] = df.WaveDirection[0]
    output['S'] = df.ResistanceQvariant[0]
    
    con.close()
    
    return output['h'], output['Hs'], output['Tp'], output['dir'], output['S']

# reliability calculations for the selected hydraulic structure and measure    
class ReliabilityCalculations(object):
        
    def __init__(self, locationId, mechanism, orientation, model, waterlevel, beta):
        
        self.locationId = locationId
        self.mechanism = mechanism
        self.orientation = orientation
        self.model = model
        self.waterlevel = waterlevel
        self.beta = beta
        
        if self.mechanism == 'Qvariant':
            if model == 'zuilen':
                self.a = 1.0
                self.b = 0.4
                self.c = 0.8
            elif model == 'gras_golfklap':
                self.a = 1.0
                self.b = 0.67
                self.c = 0.0
            elif model == 'gras_golfoploop':
                self.a = 1.0
                self.b = 1.7
                self.c = 0.3
        
    def get_numerical_settings(self, configDatabase):
        
        if self.mechanism == 'MHW':
            self.mechanismId = 1
            calculationTypeId = 0
            subMechanismId = [1]
        elif self.mechanism == 'Qvariant':
            self.mechanismId = 3
            calculationTypeId = 1
            subMechanismId = [5]
        
        con = sqlite3.connect(configDatabase)
        
        numSettings = {}
        numSettings['TimeIntegrationSchemeId'] = []
        numSettings['CalculationMethod'] = []
        numSettings['SubMechanismId'] = []
        numSettings['FORM_StartMethod'] = []
        numSettings['DS_Min'] = []
        numSettings['DS_Max'] = []
        
        # get settings from TimeIntegrationSettings
        sql = 'SELECT * FROM TimeIntegrationSettings WHERE LocationID = {} AND CalculationTypeID = {}'
        df = pd.read_sql_query(sql.format(self.locationId, calculationTypeId),con)
        numSettings['TimeIntegrationSchemeId'] = df.TimeIntegrationSchemeID[0]
        
        # get settings from NumericsSettings
        for subMech in subMechanismId:
            
            sql = 'SELECT * FROM NumericsSettings WHERE LocationID = {} AND MechanismID = {} AND SubMechanismID = {}'
            df = pd.read_sql_query(sql.format(self.locationId, self.mechanismId, subMech), con)
            
            numSettings['CalculationMethod'].append(df.CalculationMethod[0])
            numSettings['FORM_StartMethod'].append(df.FORM_StartMethod[0])
            numSettings['DS_Min'].append(df.DS_Min[0])
            numSettings['DS_Max'].append(df.DS_Max[0])
            numSettings['SubMechanismId'].append(subMech)
        
        con.close()

        return numSettings
        
    def run_HydraRing(self, binHydraRing, HRdatabase, year, numSettings):
        
        fileNameConfig = binHydraRing + 'config.sqlite'
        fileNameSQL = '1.sql'
        fileNameIni = '1.ini'
        outputfile = '1-output.sqlite'
        
        if year==2025:
            fileNameHLCD = HRdatabase + '/hlcd.sqlite'
        elif year==2100:
            fileNameHLCD = HRdatabase + '/hlcd_W_2100.sqlite'
        else:
            print('Unknown evaluation year')
        
        if self.mechanism == 'MHW':
            make_sql_MHW(fileNameSQL, self.locationId, self.beta, numSettings)
        elif self.mechanism == 'Qvariant':
            make_sql_qvariant(fileNameSQL, self.locationId, self.orientation, self.beta, self.waterlevel, self.a, self.b, self.c, numSettings)
        
        make_ini_file(fileNameIni, self.mechanismId, fileNameSQL, fileNameConfig, fileNameHLCD)
        os.system("''" + binHydraRing + 'MechanismComputation.exe ' + fileNameIni)
        
        if self.mechanism == 'MHW':
            designValue = read_design_value(outputfile)
            return designValue
        elif self.mechanism == 'Qvariant':
            Qvar = {}
            Qvar['h'], Qvar['Hs'], Qvar['Tp'], Qvar['dir'], Qvar['S'] = read_qvariant(outputfile)
            return Qvar