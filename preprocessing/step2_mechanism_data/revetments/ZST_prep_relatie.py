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
from preprocessing.common_functions import read_csv



def revetment_zst(cross_sections, qvar_path,  output_path, figures_ZST,p_grid, evaluate_years, versterking_bekleding, fb_ZST = 0.05, N = 4):

    for cross_section in cross_sections:
        computation = ZSTComputation(cross_section, qvar_path, output_path, years_to_evaluate=evaluate_years, mode = versterking_bekleding)
        computation.compute_zst(p_grid)

if __name__ == '__main__':
    pass
