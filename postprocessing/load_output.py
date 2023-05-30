import copy

import numpy as np
import pandas as pd
from vrtool.probabilistic_tools.probabilistic_functions import beta_to_pf, pf_to_beta


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

def get_traject_prob_development(optimal_measures,taken_measures,initial_beta,
                                 option_dir, calc_type='Veiligheidsrendement', mechanisms = ['StabilityInner','Piping','Overflow']):
    section_order = taken_measures['Section'].dropna().unique()
    beta_dfs = []
    #begin_betas:
    beta_dfs.append(initial_beta)
    for count, section in enumerate(section_order,1):
        beta_df = copy.deepcopy(beta_dfs[-1])
        # print('Original')

        # maatregel lezen:
        # option_index = taken_measures.loc[optimal_measures.loc[section]['Unnamed: 0']].option_index
        # vr_measure = pd.read_csv(results_dir.joinpath(run,'{}_Options_{}.csv'.format(section,calc_type)),index_col=0).loc[option_index]
        #if section
        if taken_measures.loc[taken_measures.Section==section].shape[0] == 1:
            measure_data = taken_measures.loc[taken_measures.Section==section].squeeze()
        else:
            measure_data = taken_measures.loc[optimal_measures.loc[section]['Unnamed: 0']]
        if not np.isnan(measure_data.option_index):
            vr_measure = pd.read_csv(option_dir.joinpath('{}_Options_{}.csv'.format(section,calc_type)),index_col=0)
            vr_measure = vr_measure.loc[(vr_measure.ID == measure_data.ID) & (vr_measure['yes/no'] == measure_data['yes/no'])
                                    & (vr_measure.dcrest == measure_data.dcrest) & (vr_measure.dberm == measure_data.dberm)].squeeze()
            for mechanism in mechanisms:
                mask = vr_measure.index.str.startswith(mechanism)
                betas = vr_measure.loc[mask].values
                beta_df.loc[(section[2:],mechanism),:]=betas

        else:
            #no measure, so keep initial beta
            pass

        beta_dfs.append(beta_df)
        # print('added {} with {}'.format(section,vr_measure.type))

    traject_probs = np.empty((len(beta_dfs),7))
    raw_traject_probs = []
    for count, beta_df in enumerate(beta_dfs):
        traject_probs[count,:], raw_traject_prob = get_traject_prob(beta_df)
        raw_traject_probs.append(raw_traject_prob)
    return section_order,traject_probs
