# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 14:53:11 2023

@author: wojciech
"""

import numpy as np
import pandas as pd

from scipy.special import ndtri
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from preprocessing.step2_mechanism_data.revetments.project_utils.readSteentoetsFile import read_steentoets_file
from preprocessing.step2_mechanism_data.revetments.project_utils.DiKErnel import write_JSON_to_file, read_JSON
from preprocessing.step2_mechanism_data.revetments.project_utils.functions_integrate import issteen





def revetment_zst(df, steentoets_path, output_path, figures_ZST,p_grid, fb_ZST = 0.05, N = 4):

    # define variables
    evaluateYears = [2025, 2100]

    for section_index,section in df.iterrows():

        dwarsprofiel = section.dwarsprofiel

        steentoetsFile = section['steentoetsfile']


        beta = -ndtri(p_grid)

        # import Q-variant results
        Qvar = read_JSON(output_path.joinpath("Qvar_{}.json".format(section.doorsnede)))

        # read Steentoets results
        steentoets_df = read_steentoets_file(steentoets_path.joinpath(steentoetsFile), dwarsprofiel)

        D_opt = []
        years = []
        for i, year in enumerate(evaluateYears):

            for j, p in enumerate(p_grid):

                Qvar_Hs = np.array(Qvar[f'Qvar {i}_{j}_zuilen']['Hs'])
                Qvar_h = np.array(Qvar[f'Qvar {i}_{j}_zuilen']['waterstand'])
                h_help = np.arange(min(Qvar_h), max(Qvar_h), 0.01)
                Hs_help = np.interp(h_help, Qvar_h, Qvar_Hs)

                # determine relation clay thickness vs beta for each vlak
                # for k, Zo in range(0, len(Zo)):
                for index, row in steentoets_df.iterrows():

                    if issteen(row.toplaagtype):

                        D_help = Hs_help/(row.delta * row.ratio_voldoet)
                        select = np.argwhere((h_help >= row.Zo) & (h_help <= row.Zb))

                        if len(select)==0:
                           raise ValueError("No points found")
                        else:
                            D_opt = np.append(D_opt, np.max(D_help[select]))

                    else:
                        D_opt= np.append(D_opt, np.nan)

                    years = np.append(years, evaluateYears[i])

        # scenario 2025 cannot be worse than scenario 2100
        D_opt1 = D_opt[np.argwhere(years==evaluateYears[0])]
        D_opt2 = D_opt[np.argwhere(years==evaluateYears[1])]
        D_opt1 = np.min([D_opt1, D_opt2], axis=0)
        D_opt = np.append(D_opt1, D_opt2)

        D_opt = D_opt.reshape(len(evaluateYears), len(p_grid), steentoets_df.shape[0])

        data = {}
        # export results to JSON
        for i, year in enumerate(evaluateYears):
            steentoets_df.rename(columns={"overgang": "overgang huidig", "D": "D huidig"}, inplace=True)
            data = {"zichtjaar": year,
                    "dwarsprofiel": dwarsprofiel,
                    "aantal deelvakken": steentoets_df.shape[0]}
            for key in ["Zo", "Zb", 'overgang huidig', "D huidig", "tana", "toplaagtype", "delta", "ratio_voldoet"]:
                data[key] = list(steentoets_df[key])

            for j, row in steentoets_df.iterrows():

                if issteen(row.toplaagtype):
                    # include faalkansbijdrage and length-effect factor
                    betaFalen = -ndtri(np.array(p_grid) * fb_ZST / N)
                else:
                    betaFalen = np.full_like(p_grid, np.nan)

                data[f"deelvak {j}"] = {"D_opt": list(D_opt[i,:,j]),
                        "betaFalen": list(betaFalen)}

            write_JSON_to_file(data, output_path.joinpath("ZST_{}_{}.json".format(section_index, evaluateYears[i])))

        # plots
        colors = sns.color_palette("husl", steentoets_df.shape[0])
        plt.figure()
        linestyles = ['-', ':', '--', '-.']
        for i, year in enumerate(evaluateYears):
            for j in range(0, steentoets_df.shape[0]):
                if issteen(steentoets_df.iloc[j].toplaagtype):
                    probFalen = np.array(p_grid) * fb_ZST / N
                    plt.semilogy(D_opt[i,:,j], probFalen, linestyle = linestyles[i], color = colors[j],marker= 'o',label = f'jaar {year} vlak {j}')
        plt.grid()
        plt.legend(loc="center left")
        plt.xlabel('Toplaagdikte [m]')
        plt.ylabel('Faalkans [1/jaar]')
        plt.savefig(figures_ZST.joinpath('Dikte_vs_Faalkans_doorsnede={}.png'.format(section.doorsnede)))
        plt.close()



if __name__ == '__main__':
    # paths
    bekleding_path = Path(r'c:\VRM\test_revetments\Bekleding_default.csv')
    steentoets_path = Path(r'c:\VRM\test_revetments\steentoets')
    figures_ZST = Path(r'c:\VRM\test_revetments\figures_ZST')
    output_path = Path(r'c:\VRM\test_revetments\output')

    # read revetment file
    df = pd.read_csv(bekleding_path,
                     usecols=['vaknaam', 'dwarsprofiel', 'signaleringswaarde', 'ondergrens', 'faalkansbijdrage',
                              'lengte_effectfactor', 'locationid', 'hrdatabase_folder', 'hrdatabase', 'region', 'gws',
                              'getij_amplitude', 'steentoetsfile', 'prfl', 'begin_grasbekleding', 'qvar_p1', 'qvar_p2',
                              'qvar_p3', 'qvar_p4', 'qvar_stap'])
    df = df.dropna(subset=['vaknaam']) # drop rows where vaknaam is Not a Number
    df = df.reset_index(drop=True) # reset index

    # if figures_ZST doesnot exist, create it
    if not figures_ZST.exists():
        figures_ZST.mkdir()
    # elif figures_ZST exists, but not empty, stop the script
    elif figures_ZST.exists() and len(list(figures_ZST.iterdir())) != 0:
        print('The figure folder is not empty. Please empty the figures_ZST folder and run the script again.')
        exit()

    # run revetment_zst
    revetment_zst(df, steentoets_path, output_path, figures_ZST)
