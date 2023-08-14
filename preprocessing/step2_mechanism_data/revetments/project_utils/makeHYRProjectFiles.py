# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 15:24:21 2023

@author: wojciech
"""

def make_sql_qvariant(fileNameSQL,locationId,orientation,beta,waterlevel,a,b,c,numSettings):

    with open(fileNameSQL,'w') as f:
        
        # [HydraulicModels]
        print('DELETE FROM [HydraulicModels];',file=f,sep='')
        print('INSERT INTO [HydraulicModels] VALUES ( ',numSettings['TimeIntegrationSchemeId'],' , 1, "WTI 2017");',file=f,sep='')
        print(' ',file=f,sep='') #empty line
    
        # [Sections]
        print('DELETE FROM [Sections];',file=f,sep='')
        print('INSERT INTO [Sections] VALUES (1, 1, 1, 1, 1, 0, 0, 0, 0, ',locationId,', ',locationId,', 100, ',orientation,', 0);',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [DesignTables]
        print('DELETE FROM [DesignTables];',file=f,sep='')
        print('INSERT INTO [DesignTables] VALUES (1, 3, 1, 1, 8, 114, 0, 0, 0, 0, 10, 50, ',beta,');',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [PreprocessorSettings]
        print('DELETE FROM [PreprocessorSettings];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [Numerics]
        print('DELETE FROM [Numerics];',file=f,sep='')
        print('INSERT INTO [Numerics] VALUES (1, 3, 1, 1, 5, ',
                  numSettings['CalculationMethod'][0],', ',numSettings['FORM_StartMethod'][0],', 150, 0.15000001, 0.005, 0.005, 0.005, 2, ',
                  '6 , ',numSettings['DS_Min'][0],', ',numSettings['DS_Max'][0],', 0.1, -6, 6, 25);',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [VariableDatas]
        print('DELETE FROM [VariableDatas];',file=f,sep='')
        
        print('INSERT INTO [VariableDatas] VALUES (1, 3, 1, 1, 113, ',waterlevel,', 0, 0, NULL, NULL, NULL, 1, 0, 300);',file=f,sep='')
        print('INSERT INTO [VariableDatas] VALUES (1, 3, 1, 1, 114, 1, 0, 0, NULL, NULL, NULL, 1, 0, 300);',file=f,sep='')
        print('INSERT INTO [VariableDatas] VALUES (1, 3, 1, 1, 115, ',a,', 0, 0, NULL, NULL, NULL, 1, 0, 300);',file=f,sep='')
        print('INSERT INTO [VariableDatas] VALUES (1, 3, 1, 1, 116, ',b,', 0, 0, NULL, NULL, NULL, 1, 0, 300);',file=f,sep='')
        print('INSERT INTO [VariableDatas] VALUES (1, 3, 1, 1, 119, ',c,', 0, 0, NULL, NULL, NULL, 1, 0, 300);',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [CalculationProfiles]
        print('DELETE FROM [CalculationProfiles];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [SectionFaultTreeModels]
        print('DELETE FROM [SectionFaultTreeModels];',file=f,sep='')
        print('INSERT INTO [SectionFaultTreeModels] VALUES (1, 3, 1, 1, 6);',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [SectionSubMechanismModels]
        print('DELETE FROM [SectionSubMechanismModels];',file=f,sep='')
        print('INSERT INTO [SectionSubMechanismModels] VALUES (1, 1, 1, 5, 71);',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [Fetches]
        print('DELETE FROM [Fetches];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [AreaPoints]
        print('DELETE FROM [AreaPoints];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [PresentationSections]
        print('DELETE FROM [PresentationSections];',file=f,sep='')
        print(' ',file=f,sep='') #empty line

        # [Profiles]
        print('DELETE FROM [Profiles];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [ForelandModels]
        print('DELETE FROM [ForelandModels];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [Forelands]
        print('DELETE FROM [Forelands];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [ProbabilityAlternatives]
        print('DELETE FROM [ProbabilityAlternatives];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [SetUpHeights]
        print('DELETE FROM [SetUpHeights];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [CalcWindDirections]
        print('DELETE FROM [CalcWindDirections];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [Swells]
        print('DELETE FROM [Swells];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [WaveReductions]
        print('DELETE FROM [WaveReductions];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [Areas]
        print('DELETE FROM [Areas];',file=f,sep='')
        print('INSERT INTO [Areas] VALUES (1, "1", "Nederland");',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [Projects]
        print('DELETE FROM [Projects];',file=f,sep='')
        print('INSERT INTO [Projects] VALUES (1, "BOI", "Hydra-Ring calculation");',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [Breakwaters]
        print('DELETE FROM [Breakwaters];',file=f,sep='')
        print(' ',file=f,sep='') #empty line

def make_sql_MHW(fileNameSQL,locationId,beta,numSettings):

    with open(fileNameSQL,'w') as f:
        
        # [HydraulicModels]
        print('DELETE FROM [HydraulicModels];',file=f,sep='')
        print('INSERT INTO [HydraulicModels] VALUES ( ',numSettings['TimeIntegrationSchemeId'],' , 1, "WTI 2017");',file=f,sep='')
        print(' ',file=f,sep='') #empty line
    
        # [Sections]
        print('DELETE FROM [Sections];',file=f,sep='')
        print('INSERT INTO [Sections] VALUES (1, 1, 1, 1, 1, 0, 0, 0, 0, ',locationId,', ',locationId,', 100, 0, 0);',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [DesignTables]
        print('DELETE FROM [DesignTables];',file=f,sep='')
        print('INSERT INTO [DesignTables] VALUES (1, 1, 1, 1, 9, 26, 0, 0, 0, 0, 2, 4, ',beta,');',file=f,sep='') #to do: check in config
        print(' ',file=f,sep='') #empty line
        
        # [PreprocessorSettings]
        print('DELETE FROM [PreprocessorSettings];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [Numerics]        
        print('DELETE FROM [Numerics];',file=f,sep='')
        print('INSERT INTO [Numerics] VALUES (1, 1, 1, 1, 1, ',
                  numSettings['CalculationMethod'][0],', ',numSettings['FORM_StartMethod'][0],', 150, 0.15000001, 0.005, 0.005, 0.005, 2, ',
                  '6 , ',numSettings['DS_Min'][0],', ',numSettings['DS_Max'][0],', 0.1, -6, 6, 25);',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [VariableDatas]
        print('DELETE FROM [VariableDatas];',file=f,sep='')
        print('INSERT INTO [VariableDatas] VALUES (1, 1, 1, 1, 26, 0, 0, 0, NULL, NULL, NULL, 1, 0, 300);',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [CalculationProfiles]
        print('DELETE FROM [CalculationProfiles];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [SectionFaultTreeModels]
        print('DELETE FROM [SectionFaultTreeModels];',file=f,sep='')
        print('INSERT INTO [SectionFaultTreeModels] VALUES (1, 1, 1, 1, 1);',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [SectionSubMechanismModels]
        print('DELETE FROM [SectionSubMechanismModels];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [Fetches]
        print('DELETE FROM [Fetches];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [AreaPoints]
        print('DELETE FROM [AreaPoints];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [PresentationSections]
        print('DELETE FROM [PresentationSections];',file=f,sep='')
        print(' ',file=f,sep='') #empty line

        # [Profiles]
        print('DELETE FROM [Profiles];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [ForelandModels]
        print('DELETE FROM [ForelandModels];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [Forelands]
        print('DELETE FROM [Forelands];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [ProbabilityAlternatives]
        print('DELETE FROM [ProbabilityAlternatives];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [SetUpHeights]
        print('DELETE FROM [SetUpHeights];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [CalcWindDirections]
        print('DELETE FROM [CalcWindDirections];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [Swells]
        print('DELETE FROM [Swells];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [WaveReductions]
        print('DELETE FROM [WaveReductions];',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [Areas]
        print('DELETE FROM [Areas];',file=f,sep='')
        print('INSERT INTO [Areas] VALUES (1, "1", "Nederland");',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [Projects]
        print('DELETE FROM [Projects];',file=f,sep='')
        print('INSERT INTO [Projects] VALUES (1, "BOI", "Hydra-Ring calculation");',file=f,sep='')
        print(' ',file=f,sep='') #empty line
        
        # [Breakwaters]
        print('DELETE FROM [Breakwaters];',file=f,sep='')
        print(' ',file=f,sep='') #empty line

def make_ini_file(fileNameIni,mechanismId,fileNameSQL,fileNameConfig,fileNameHLCD):
    
    with open(fileNameIni,'w') as f:
        print('section = 1',file=f,sep='')
        print('mechanism = ',mechanismId,file=f,sep='')
        print('alternative = 1',file=f,sep='')
        print('layer = 1',file=f,sep='')
        print('logfile = hydraring.log',file=f,sep='')
        print('outputverbosity = basic',file=f,sep='')
        print('outputtofile = file',file=f,sep='')
        print('projectdbfilename = ',fileNameSQL,file=f,sep='')
        print('configdbfilename = ',fileNameConfig,file=f,sep='')
        print('hydraulicdbfilename = ',fileNameHLCD,file=f,sep='')
        print('availablecores = 4',file=f,sep='')
        print('designpointoutput = sqlite',file=f,sep='')