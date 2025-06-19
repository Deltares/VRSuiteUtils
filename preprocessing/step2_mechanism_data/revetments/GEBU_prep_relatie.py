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

import logging

def revetment_gebu(cross_sections, qvar_path, output_path, binDIKErnel, local_path, p_grid, evaluate_years):
    for cross_section in cross_sections:
        logging.info(f"Start GEBU berekening voor {cross_section.doorsnede}")
        GEBUComputation(cross_section, qvar_path, output_path, local_path, binDIKErnel, years_to_evaluate=evaluate_years).compute_gebu(p_grid)
        logging.info(f"GEBU berekening voor {cross_section.doorsnede} is voltooid.\n")