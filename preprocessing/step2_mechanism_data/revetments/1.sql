DELETE FROM [HydraulicModels];
INSERT INTO [HydraulicModels] VALUES ( 1 , 1, "WTI 2017");
 
DELETE FROM [Sections];
INSERT INTO [Sections] VALUES (1, 1, 1, 1, 1, 0, 0, 0, 0, 1400364.0, 1400364.0, 100, 0, 0);
 
DELETE FROM [DesignTables];
INSERT INTO [DesignTables] VALUES (1, 1, 1, 1, 9, 26, 0, 0, 0, 0, 2, 4, 2.3263478740408408);
 
DELETE FROM [PreprocessorSettings];
 
DELETE FROM [Numerics];
INSERT INTO [Numerics] VALUES (1, 1, 1, 1, 1, 12, 4, 150, 0.15000001, 0.005, 0.005, 0.005, 2, 6 , 10000, 40000, 0.1, -6, 6, 25);
 
DELETE FROM [VariableDatas];
INSERT INTO [VariableDatas] VALUES (1, 1, 1, 1, 26, 0, 0, 0, NULL, NULL, NULL, 1, 0, 300);
 
DELETE FROM [CalculationProfiles];
 
DELETE FROM [SectionFaultTreeModels];
INSERT INTO [SectionFaultTreeModels] VALUES (1, 1, 1, 1, 1);
 
DELETE FROM [SectionSubMechanismModels];
 
DELETE FROM [Fetches];
 
DELETE FROM [AreaPoints];
 
DELETE FROM [PresentationSections];
 
DELETE FROM [Profiles];
 
DELETE FROM [ForelandModels];
 
DELETE FROM [Forelands];
 
DELETE FROM [ProbabilityAlternatives];
 
DELETE FROM [SetUpHeights];
 
DELETE FROM [CalcWindDirections];
 
DELETE FROM [Swells];
 
DELETE FROM [WaveReductions];
 
DELETE FROM [Areas];
INSERT INTO [Areas] VALUES (1, "1", "Nederland");
 
DELETE FROM [Projects];
INSERT INTO [Projects] VALUES (1, "BOI", "Hydra-Ring calculation");
 
DELETE FROM [Breakwaters];
 
