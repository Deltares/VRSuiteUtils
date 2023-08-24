# -*- coding: utf-8 -*-
"""
Created on Sun Apr 23 13:16:42 2023

@author: wojciech
"""
import numpy as np
import pandas as pd

def read_steentoets_file(steentoetsFile, dwarsprofiel):

    df = pd.read_excel(steentoetsFile, skiprows=[1, 2, 3, 4, 5, 6], header=0, index_col=0, dtype={'dwp_oi': str})
    df_profile = df.loc[df['dwp_oi'] == dwarsprofiel]
    #filter df columns
    df_profile = df_profile[['Zo_oi', 'Zb_oi', 'tana_oi', 'Bsegment_oi', 'toplaagtype_oi', 'D_oi', 'rho_oi', 'Unnamed: 77', 'Unnamed: 93']]
    #rename columns to match the old code
    df_profile.columns = ['Zo', 'Zb', 'tana', 'Bsegment', 'toplaagtype', 'D', 'rho_s', 'Hs_ini', 'overschot']
    for col in df_profile.columns:
        df_profile[col] = df_profile[col].astype('float')
    df_profile_dict = df_profile.to_dict('list')
    for key in df_profile_dict.keys(): df_profile_dict[key] = np.array(df_profile_dict[key])

    rho = 1025.0
            
    df_profile_dict['delta'] = np.subtract(df_profile_dict['rho_s'],rho)/rho
    df_profile_dict['D_voldoet'] = np.subtract(df_profile_dict['D'],df_profile_dict['overschot'])
    df_profile_dict['ratio_voldoet'] = np.divide(df_profile_dict['Hs_ini'],(df_profile_dict['delta'] * df_profile_dict['D_voldoet']))
    #find overgang which is Zo of  where toplaagtype = 20.0
    df_profile_dict['overgang'] =np.argwhere(df_profile_dict['toplaagtype']==20.0)[0][0]

    for col in ['D_voldoet', 'ratio_voldoet', 'Hs_ini', 'overschot', 'delta']:
        # for each col in df_profile_dict set all values larger than 10**7 to np.nan
        df_profile_dict[col] = np.array(df_profile_dict[col])
        df_profile_dict[col][df_profile_dict['overschot']>10**7] = np.nan

    steentoets_result = pd.DataFrame.from_dict(df_profile_dict)
    
    return steentoets_result