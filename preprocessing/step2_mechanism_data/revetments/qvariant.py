"""
Created on Tue Jan 17 14:40:54 2023

@author: wojciech
"""

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.special import ndtri
from preprocessing.step2_mechanism_data.revetments.project_utils.reliability import QVariantCalculations
from preprocessing.step2_mechanism_data.revetments.project_utils.DiKErnel import write_JSON_to_file, read_prfl
from vrtool.probabilistic_tools.hydra_ring_scripts import read_design_table
from scipy.interpolate import interp1d
from preprocessing.step2_mechanism_data.overflow.overflow_input import OverflowInput

import warnings

def revetment_qvariant(df, profielen_path, database_path, waterlevel_path, hring_path, output_path, local_path, Q_var_pgrid):
# define variables
    models = ['gras_golfklap', 'gras_golfoploop', 'zuilen']

    evaluateYears = [2025, 2100]
    beta = -ndtri(Q_var_pgrid)

    # check if hlcd and hlcd_W_2100 are in HRdatabase
    if len(list(database_path.glob('*hlcd.sqlite')))==0: raise ValueError('No hlcd.sqlite file found in database_path.')
    if len(list(database_path.glob('*hlcd_W_2100.sqlite')))==0: raise ValueError('No hlcd_W_2100.sqlite file found in database_path.')

    #path to config database:
    configDatabase = list(database_path.glob('*.config.sqlite'))[0]
    if len(list(database_path.glob('*.config.sqlite')))>1: warnings.warn('Warning: multiple config.sqlite files found in database_path. Using first file found.')
    if len(list(database_path.glob('*.config.sqlite')))==0: raise Exception('No config.sqlite found in database_path')
    for index,row in df.iterrows():
        dwarsprofiel = row['dwarsprofiel']

        OverflowInput.get_HRLocation(
            hrd_db_location=Path(str(list(database_path.glob('WBI2017_*.sqlite'))[0]).split('.')[0] + '.sqlite'),
            hlcd_db_location=list(database_path.glob('*hlcd.sqlite'))[0], hring_data=row.to_frame().transpose())
        locationId = row['hrlocation']
        orientation = read_prfl(profielen_path.joinpath(row['prfl']))[0]

        # ondergrens waterstand is hoogste punt op voorland. Als voorland niet bestaat, laagste punt op profiel.
        # daar wordt een veiligheidsmarge van 1m bij op geteld, om droogstand te voorkomen getrokken
        try:
            ondergrens_wl = max(read_prfl(profielen_path.joinpath(row['prfl']))[5])+1.
        except:
            ondergrens_wl = min(read_prfl(profielen_path.joinpath(row['prfl']))[3])+1.

        begin_grasbekleding = row['begin_grasbekleding']

        # get design water levels
        valMHW = np.empty((len(evaluateYears), len(Q_var_pgrid)))

        for i, year in enumerate(evaluateYears):
            output_overflow = waterlevel_path.joinpath(f'{year}', f'{row.naam_hrlocatie}', 'designTable.txt')
            wl_frequencycurve = read_design_table(output_overflow)[['Value','Beta']]
            f = interp1d(wl_frequencycurve['Beta'], wl_frequencycurve['Value'], fill_value=('extrapolate'))
            valMHW[i, :] = f(beta)

        # Q-variant calculations
        data = {'dwarsprofiel': dwarsprofiel}
        mechanism = 'Qvariant'
        for i in range(0, len(evaluateYears)):

            for j in range(0, len(Q_var_pgrid)):

                wl = np.arange(ondergrens_wl, valMHW[i, j] - 0.05, row['waterstand_stap'])
                wl = np.append(wl, valMHW[i, j] - 0.05)
                wl = np.unique(wl)

                data[f'MHW {i}_{j}'] = valMHW[i, j]

                for m in models:

                    if m == "gras_golfklap":
                        wl_filtered = wl[wl>=begin_grasbekleding]
                    elif m == "gras_golfoploop":
                        wl_filtered == wl
                    elif m == "zuilen":
                        wl_filtered = wl[wl<=begin_grasbekleding]

                    Qvar_Hs = []
                    Qvar_Tp = []
                    Qvar_dir = []
                    for h in wl_filtered:
                        Qvar = QVariantCalculations(locationId, mechanism, orientation, m, h, beta[j])
                        numSettings = Qvar.get_numerical_settings(configDatabase)
                        QvarRes = Qvar.run_HydraRing(hring_path, str(database_path), local_path, evaluateYears[i], numSettings)

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

        write_JSON_to_file(data, output_path.joinpath("Qvar_{}.json".format(row.doorsnede)))

if __name__ == '__main__':
    # inputs
    bekleding_path = Path(r'c:\VRM\bestanden Scheldestromen\Bekleding_default.csv')
    profielen_path = Path(r'c:\VRM\bestanden Scheldestromen\Overflow\prfl')
    database_path = Path(r'c:\VRM\bestanden Scheldestromen\Databases\V3_WBI2017')
    waterlevel_path = Path(r'c:\VRM\bestanden Scheldestromen\Waterlevel')
    hring_path = Path("c:/Program Files (x86)/BOI/Riskeer 21.1.1.2/Application/Standalone/Deltares/HydraRing-20.1.3.10236")
    output_path = Path(r'c:/VRM/test_revetments/output_test')

    # read csv file as dataframe
    df = pd.read_csv(bekleding_path,
                     usecols=['vaknaam', 'dwarsprofiel', 'signaleringswaarde', 'ondergrens', 'faalkansbijdrage',
                              'lengte_effectfactor', 'locationid', 'hrdatabase_folder', 'hrdatabase', 'region', 'gws',
                              'getij_amplitude', 'steentoetsfile', 'prfl', 'begin_grasbekleding', 'qvar_p1', 'qvar_p2',
                              'qvar_p3', 'qvar_p4', 'qvar_stap'])
    df = df.dropna(subset=['vaknaam'])  # drop rows where vaknaam is Not a Number
    df = df.reset_index(drop=True)  # reset index

    # if output_path doesnot exist, create it
    if not output_path.exists():
        output_path.mkdir()
    # elif output_path exists, but not empty, stop the script
    elif output_path.exists() and len(list(output_path.iterdir())) != 0:
        print('The output folder is not empty. Please empty the folder and run the script again.')
        exit()

    revetment_qvariant(df, profielen_path, database_path, hring_path, output_path)