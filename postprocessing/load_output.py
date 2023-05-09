import pandas as pd
from vrtool.probabilistic_tools.probabilistic_functions import pf_to_beta, beta_to_pf
import copy
import numpy as np
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


def get_traject_prob(beta_df, mechanisms = ['StabilityInner','Piping','Overflow']):
    # determines the probability of failure for a traject based on the standardized beta input
    beta_df = beta_df.reset_index().set_index('mechanism').drop(columns=['name'])
    traject_probs = dict((el,[]) for el in mechanisms)
    total_traject_prob = np.empty((1,beta_df.shape[1]))
    for mechanism in mechanisms:
        if mechanism == 'Overflow':
            #take min beta in each column
            traject_probs[mechanism] = beta_to_pf(beta_df.loc[mechanism].min().values)
        else:
            pf_df = beta_to_pf(beta_df.loc[mechanism].values)
            pnonf_df = np.subtract(1,pf_df)
            pnonf_traject = np.product(pnonf_df,axis=0)
            traject_probs[mechanism] = 1-pnonf_traject
            #convert to probability
            #1-prod(1-p)
        total_traject_prob += traject_probs[mechanism]
    return total_traject_prob, traject_probs


