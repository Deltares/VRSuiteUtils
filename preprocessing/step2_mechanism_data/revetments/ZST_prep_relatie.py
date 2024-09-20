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
from preprocessing.step2_mechanism_data.revetments.project_utils.DiKErnel import write_JSON_to_file, read_JSON, read_prfl
from preprocessing.step2_mechanism_data.revetments.project_utils.functions_integrate import issteen

from preprocessing.step2_mechanism_data.revetments.ZST_computation import ZSTComputation



def revetment_zst(cross_sections, qvar_path,  output_path, figures_ZST,p_grid, evaluate_years, fb_ZST = 0.05, N = 4):

    for cross_section in cross_sections:
        computation = ZSTComputation(cross_section, qvar_path, output_path, years_to_evaluate=evaluate_years)
        computation.compute_zst(p_grid)

        # # plots
        # colors = sns.color_palette("husl", steentoets_df.shape[0])
        # plt.figure()
        # linestyles = ['-', ':', '--', '-.']
        # for i, year in enumerate(evaluateYears):
        #     for j in range(0, steentoets_df.shape[0]):
        #         if issteen(steentoets_df.iloc[j].toplaagtype):
        #             probFalen = np.array(p_grid) * fb_ZST / N
        #             plt.semilogy(D_opt[i,:,j], probFalen, linestyle = linestyles[i], color = colors[j],marker= 'o',label = f'jaar {year} vlak {j}')
        # plt.grid()
        # plt.legend(loc="center left")
        # plt.xlabel('Toplaagdikte [m]')
        # plt.ylabel('Faalkans [1/jaar]')
        # plt.xlim(left=0.0)
        # plt.savefig(figures_ZST.joinpath('Dikte_vs_Faalkans_doorsnede={}.png'.format(section.doorsnede)))
        # plt.close()

if __name__ == '__main__':
    # paths
    # bekleding_path = Path(r"c:\vrm_test\bekleding_split_workflow\Bekleding_20230830_full.csv")
    # profielen_path = Path(r'c:\vrm_test\bekleding_split_workflow\PRFL')
    # steentoets_path = Path(r"c:\vrm_test\bekleding_split_workflow\steentoets")
    # output_path = Path(r"c:\vrm_test\bekleding_split_workflow\output_full")

    bekleding_path = Path(r"c:\VRM\preprocess_test\20240510_test_31_1\input_files\default_files\Bekleding_default_31-1.csv")
    profielen_path = Path(r'c:\VRM\preprocess_test\20240510_test_31_1\input_files\prfl')
    steentoets_path = Path(r"c:\VRM\preprocess_test\20240510_test_31_1\input_files\steentoets")
    output_path = Path(r"c:\VRM\preprocess_test\20240510_test_31_1\intermediate_results\bekleding")
    figures_ZST = output_path.joinpath('figures_ZST')


    traject_id = "31-1"
    _generic_data_dir = Path(__file__).absolute().parent.parent.parent.joinpath('generic_data')
    dike_info = pd.read_csv(_generic_data_dir.joinpath('diketrajectinfo.csv'))
    p_ondergrens = float(dike_info.loc[dike_info['traject_name'] == traject_id, ['p_max']].values[0])
    p_signaleringswaarde = float(dike_info.loc[dike_info['traject_name'] == traject_id, ['p_sig']].values[0])

    p_grid = [1. / 30,
              p_ondergrens,
              p_signaleringswaarde,
              p_signaleringswaarde * (1. / 1000.)]

    # read revetment file
    df = pd.read_csv(bekleding_path,
                     usecols=['doorsnede', 'dwarsprofiel', 'naam_hrlocatie', 'hrlocation', 'hr_koppel', 'region', 'gws',
                              'getij_amplitude', 'steentoetsfile', 'prfl', 'begin_grasbekleding', 'waterstand_stap'],
                     dtype={'doorsnede': str, 'dwarsprofiel': str})
    df = df.dropna(subset=['doorsnede'])  # drop rows where vaknaam is Not a Number
    df = df.reset_index(drop=True)  # reset index

    # if figures_ZST doesnot exist, create it
    if not figures_ZST.exists():
        figures_ZST.mkdir()
    # elif figures_ZST exists, but not empty, stop the script
    elif figures_ZST.exists() and len(list(figures_ZST.iterdir())) != 0:
        print('The figure folder is not empty. Please empty the figures_ZST folder and run the script again.')
        exit()

    # run revetment_zst
    revetment_zst(df, profielen_path, steentoets_path, output_path, output_path, figures_ZST, p_grid)
