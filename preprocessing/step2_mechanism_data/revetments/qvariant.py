"""
Created on Tue Jan 17 14:40:54 2023

@author: wojciech
"""

import numpy as np
import pandas as pd
from project_utils.reliability import ReliabilityCalculations
from scipy.special import ndtri
from project_utils.DiKErnel import write_JSON_to_file, read_prfl
from pathlib import Path

# inputs
bekleding_path = Path(r'c:\VRM\test_revetments\Bekleding_default.csv')
profielen_path = Path(r'c:\VRM\test_revetments\profielen')
database_path = Path(r'c:\VRM\test_revetments\database')
hring_path = "c:/Program Files (x86)/BOI/Riskeer 21.1.1.2/Application/Standalone/Deltares/HydraRing-20.1.3.10236/"
# hring_path = 'c:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236'
# "n:\Projects\11209000\11209353\B. Measurements and calculations\007 - VRTool bekledingen\Scripts\bin_HYR\"
df = pd.read_csv(bekleding_path,
                 usecols=['vaknaam', 'dwarsprofiel', 'signaleringswaarde', 'ondergrens', 'locationid', 'prfl',
                          'hrdatabase_folder', 'hrdatabase', 'qvar_p1', 'qvar_p2', 'qvar_p3', 'qvar_p4', 'qvar_stap'])
df = df.dropna(subset=['vaknaam']) # drop rows where vaknaam is Not a Number

models = ['gras_golfklap', 'gras_golfoploop', 'zuilen']
evaluateYears = [2025, 2100]

indexvak = np.arange(0, len(df))

for index in indexvak:
    dwarsprofiel = df['dwarsprofiel'].values[index]
    signaleringswaarde = df['signaleringswaarde'].values[index]
    ondergrens = df['ondergrens'].values[index]
    locationId = df['locationid'].values[index]
    orientation = read_prfl(profielen_path.joinpath(df['prfl'].values[index]))[0]

    HRdatabase = database_path.joinpath(df['hrdatabase_folder'].values[index])
    configDatabase = HRdatabase.joinpath(df['hrdatabase'].values[index] + '.config.sqlite')
    # binHydraRing = 'c:/Werk/Veiligheidsrendement_bekledingen/bin_HYR/'


    Qvar_p1 = df['qvar_p1'].values[index]
    Qvar_p2 = df['qvar_p2'].values[index]
    Qvar_p3 = df['qvar_p3'].values[index]
    Qvar_p4 = df['qvar_p4'].values[index]
    Qvar_stap = df['qvar_stap'].values[index]

    prob = [Qvar_p1, Qvar_p2, Qvar_p3, Qvar_p4]
    beta = -ndtri(prob)

    # water level calculations
    mechanism = 'MHW'
    valMHW = []
    for i in range(0, len(evaluateYears)):

        for j in range(0, len(prob)):
            MHW = ReliabilityCalculations(locationId, mechanism, 0.0, '', 0.0, beta[j])
            numSettings = MHW.get_numerical_settings(configDatabase)
            valMHW = np.append(valMHW, MHW.run_HydraRing(str(hring_path), str(HRdatabase), evaluateYears[i], numSettings))

    valMHW = valMHW.reshape(len(evaluateYears), len(prob))

    # Q-variant calculations
    data = {'dwarsprofiel': dwarsprofiel / 1.0}
    mechanism = 'Qvariant'
    for i in range(0, len(evaluateYears)):

        for j in range(0, len(prob)):

            wl = np.arange(0.0, valMHW[i, j] - 0.05, Qvar_stap)
            wl = np.append(wl, valMHW[i, j] - 0.05)
            wl = np.unique(wl)

            data[f'MHW {i}_{j}'] = valMHW[i, j]

            for m in models:

                Qvar_Hs = []
                Qvar_Tp = []
                Qvar_dir = []
                for h in wl:
                    Qvar = ReliabilityCalculations(locationId, mechanism, orientation, m, h, beta[j])
                    numSettings = Qvar.get_numerical_settings(configDatabase)
                    QvarRes = Qvar.run_HydraRing(binHydraRing, HRdatabase, evaluateYears[i], numSettings)

                    Qvar_Hs = np.append(Qvar_Hs, QvarRes['Hs'])
                    Qvar_Tp = np.append(Qvar_Tp, QvarRes['Tp'])
                    Qvar_dir = np.append(Qvar_dir, QvarRes['dir'])

                data[f"Qvar {i}_{j}_{m}"] = {"zichtjaar": evaluateYears[i] / 1.0,
                                             "beta": beta[j],
                                             "model": m,
                                             "waterstand": list(wl),
                                             "Hs": list(Qvar_Hs),
                                             "Tp": list(Qvar_Tp),
                                             "dir": list(Qvar_dir)}

    write_JSON_to_file(data, f"Output/Qvar_{index}.json")