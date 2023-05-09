import pandas as pd
from vrtool.probabilistic_tools.probabilistic_functions import pf_to_beta, beta_to_pf
import copy

def read_assessment_betas(filename):
    """Reads the assessment betas from a csv file and returns a dataframe with the betas and the corresponding
    probabilities of failure"""

    betas = pd.read_csv(filename)
    for count, line in betas.iterrows():
        betas.loc[count, 'name'] = line['name'].strip('DV')

    list_of_cols_to_change = ['0', '19', '20', '25', '50', '75', '100']
    probabilities = copy.deepcopy(betas)
    probabilities[list_of_cols_to_change] = probabilities[
        list_of_cols_to_change].apply(lambda x: beta_to_pf(x))
    return betas, probabilities



