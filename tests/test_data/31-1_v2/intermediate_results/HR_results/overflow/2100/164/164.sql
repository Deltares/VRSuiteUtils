--! Basic input file for GEKB computation
-- KEYS TO BE FILLED: '164', 1500305, 220, 1, 7.5, 10.5, 0.25, data from profile and numerics settings
DELETE FROM [HydraulicModels];
INSERT INTO [HydraulicModels] VALUES (1, 1, 'WTI 2017');

DELETE FROM [Sections];
INSERT INTO [Sections] VALUES (1, 1, 1, '164', '164', -999,-999,-999,-999, 1500305, 1500305, 100, 220, 0);

DELETE FROM [SectionCalculationSchemes];
INSERT INTO [SectionCalculationSchemes] VALUES (1, 101, 1);

DELETE FROM [DesignTables];
INSERT INTO [DesignTables] VALUES (1, 101, 1, 1, 3, 1, NULL, 7.5, 10.5, 0.25, 0, 0, 0);

DELETE FROM [PreprocessorSettings];

DELETE FROM [Numerics];
INSERT INTO [Numerics] VALUES (1, 101, 1, 1, 102, 11, 4, 150, 0.15000001, 0.005, 0.005, 0.005, 2, 3, 10000, 40000, 0.1, -6, 6, 25);
INSERT INTO [Numerics] VALUES (1, 101, 1, 1, 103, 11, 4, 150, 0.15000001, 0.005, 0.005, 0.005, 2, 3, 10000, 40000, 0.1, -6, 6, 25);

DELETE FROM [VariableDatas];
INSERT INTO [VariableDatas] VALUES (1, 101, 1, 1, 1, 8.5, 0, 0, NULL, NULL, NULL, 1, 0, 300);
INSERT INTO [VariableDatas] VALUES (1, 101, 1, 1, 8, 1, 0, 0, NULL, NULL, NULL, 1, 0, 300);
INSERT INTO [VariableDatas] VALUES (1, 101, 1, 1, 10, 0, 19, 4.75, 0.5, 0, 99, 1, 0, 300);
INSERT INTO [VariableDatas] VALUES (1, 101, 1, 1, 11, 0, 19, 2.6, 0.35, 0, 99, 1, 0, 300);
INSERT INTO [VariableDatas] VALUES (1, 101, 1, 1, 12, 1, 0, 0, NULL, NULL, NULL, 1, 0, 300);
INSERT INTO [VariableDatas] VALUES (1, 101, 1, 1, 17, 0, 4, 0.003, 0.0005, NULL, NULL, 1, 0, 300);
INSERT INTO [VariableDatas] VALUES (1, 101, 1, 1, 120, 0, 19, 1, 0.07, 0, 99, 1, 0, 300);
INSERT INTO [VariableDatas] VALUES (1, 101, 1, 1, 123, 0, 19, 0.92, 0.24, 0, 99, 1, 0, 300);

DELETE FROM [SectionFaultTreeModels];
INSERT INTO [SectionFaultTreeModels] VALUES (1, 101, 1, 1, 1017);

DELETE FROM [SectionSubMechanismModels];
INSERT INTO [SectionSubMechanismModels] VALUES (1, 1, 1, 102, 94);
INSERT INTO [SectionSubMechanismModels] VALUES (1, 1, 1, 103, 95);

DELETE FROM [Fetches];

DELETE FROM [AreaPoints];

DELETE FROM [PresentationSections];

--Below is only the part that is used for the dike profile: meaning all data to be read from the prfl 
--(Forelands, ForelandModels, Profiles, CalculationProfiles, Breakwaters)

DELETE FROM [CalculationProfiles];
INSERT INTO [CalculationProfiles] VALUES (1, 1, -43.240, -2.000, 1.000);
INSERT INTO [CalculationProfiles] VALUES (1, 2, -42.190, -1.700, 1.000);
INSERT INTO [CalculationProfiles] VALUES (1, 3, -13.420, 6.090, 1.000);
INSERT INTO [CalculationProfiles] VALUES (1, 4, -6.630, 6.370, 1.000);
INSERT INTO [CalculationProfiles] VALUES (1, 5, -0.500, 8.430, 1.000);
INSERT INTO [CalculationProfiles] VALUES (1, 6, -0.260, 8.500, 1.000);
--Example line: INSERT INTO [CalculationProfiles] VALUES (1, 1, -17, 5.13, 1);

DELETE FROM [Profiles];
INSERT INTO [Profiles] VALUES (1, 1, -43.240, -2.000);
INSERT INTO [Profiles] VALUES (1, 2, -42.190, -1.700);
INSERT INTO [Profiles] VALUES (1, 3, -13.420, 6.090);
INSERT INTO [Profiles] VALUES (1, 4, -6.630, 6.370);
INSERT INTO [Profiles] VALUES (1, 5, -0.500, 8.430);
INSERT INTO [Profiles] VALUES (1, 6, -0.260, 8.500);
--Example line: INSERT INTO [Profiles] VALUES (1, 1, -17, 5.13);

DELETE FROM [ForelandModels];
INSERT INTO [ForelandModels] VALUES (1, 101, 3);

DELETE FROM [Forelands];
INSERT INTO [FORELANDS] VALUES (1, 1, -129.000, -2.250);
INSERT INTO [FORELANDS] VALUES (1, 2, -51.000, -1.210);
INSERT INTO [FORELANDS] VALUES (1, 3, -42.190, -1.210);
--Example line: INSERT INTO [Forelands] VALUES (1, 1, -68, 2.56);

DELETE FROM [ProbabilityAlternatives];

DELETE FROM [SetUpHeights];

DELETE FROM [CalcWindDirections];

DELETE FROM [Swells];

DELETE FROM [WaveReductions];

DELETE FROM [Areas];
INSERT INTO [Areas] VALUES (1, '1', 'Nederland');

DELETE FROM [Projects];
INSERT INTO [Projects] VALUES (1, 'BOI', 'Riskeer calculation');

DELETE FROM [Breakwaters];
