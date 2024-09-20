# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 14:40:54 2023

@author: wojciech
"""
import numpy as np
import pandas as pd
import os
import shutil
from scipy.special import ndtri
from scipy.stats import norm
import matplotlib.pyplot as plt
from scipy import interpolate
from pathlib import Path
from preprocessing.step2_mechanism_data.revetments.project_utils.belastingen import waterstandsverloop, Hs_verloop, Tp_verloop, betahoek_verloop
from preprocessing.step2_mechanism_data.revetments.project_utils.DiKErnel import DIKErnelCalculations, write_JSON_to_file, read_JSON, read_prfl
from preprocessing.step2_mechanism_data.revetments.project_utils.bisection import bisection
from preprocessing.step2_mechanism_data.revetments.revetment_slope import RevetmentSlope
from preprocessing.step2_mechanism_data.revetments.GEBU_computation import GEBUComputation

def revetment_gebu(cross_sections, qvar_path, output_path, binDIKErnel, local_path, p_grid, evaluate_years):

    

    for cross_section in cross_sections:
        GEBUComputation(cross_section, qvar_path, output_path, local_path, binDIKErnel, years_to_evaluate=evaluate_years).compute_gebu(p_grid)

if __name__ == '__main__':
    # inputs
    traject_id = "13-6"
    bekleding_path = Path(r'c:\VRM\HHNK_20240528\input_files\default_files\Bekleding_20240626_test20240705.csv')
    profielen_path = Path(r'c:\VRM\HHNK_20240528\input_files\prfl_test20240705')
    output_path = Path(r'c:\VRM\HHNK_20240528\intermediate_results\bekleding_test20240705')
    qvar_path = Path(r'c:\VRM\HHNK_20240528\intermediate_results\bekleding_test20240705')
    binDIKErnel = Path(__file__).parent.absolute().parent.joinpath('externals', 'DiKErnel')
    figures_GEBU = output_path.joinpath('figures_GEBU')
    local_path = output_path.joinpath('temp')

    # read bekleding csv
    df = pd.read_csv(bekleding_path,
                     usecols=['doorsnede', 'dwarsprofiel', 'naam_hrlocatie', 'hrlocation', 'hr_koppel', 'region', 'gws',
                              'getij_amplitude', 'steentoetsfile', 'prfl', 'begin_grasbekleding', 'waterstand_stap'],
                     dtype={'doorsnede': str, 'dwarsprofiel': str})
    df = df.dropna(subset=['doorsnede'])  # drop rows where vaknaam is Not a Number
    df = df.reset_index(drop=True)  # reset index

    for output_folder in [figures_GEBU, local_path]:
        if not output_folder.exists():
            output_folder.mkdir(parents=True, exist_ok=False)
        else:
            #remove and recreate the folder.
            shutil.rmtree(output_folder)
            output_folder.mkdir(parents=True, exist_ok=False)


    # set default Q-variant probability grid:
    this_file_path = Path(os.path.dirname(os.path.realpath(__file__)))
    _generic_data_dir = this_file_path.absolute().parent.parent.joinpath('generic_data')
    dike_info = pd.read_csv(_generic_data_dir.joinpath('diketrajectinfo.csv'))
    p_ondergrens = float(dike_info.loc[dike_info['traject_name'] == traject_id, ['p_max']].values[0])
    p_signaleringswaarde = float(dike_info.loc[dike_info['traject_name'] == traject_id, ['p_sig']].values[0])

    p_grid = [1. / 30,
              p_ondergrens,
              p_signaleringswaarde,
              p_signaleringswaarde * (1. / 1000.)]

    revetment_gebu(df, profielen_path, qvar_path, output_path, binDIKErnel, figures_GEBU, local_path, p_grid)

