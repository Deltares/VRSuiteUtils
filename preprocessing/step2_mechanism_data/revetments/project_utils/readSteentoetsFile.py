# -*- coding: utf-8 -*-
"""
Created on Sun Apr 23 13:16:42 2023

@author: wojciech
"""
import numpy as np
import pandas as pd

def read_steentoets_file(steentoetsFile, dwarsprofiel):
    # if steentoetsfile contains "17.1.2.1", do:

    if "17.1.2.1" in str(steentoetsFile):
        print("Steentoets versie is 17.1.2.1")
        # df = pd.read_excel(steentoetsFile, skiprows=[1, 2, 3, 4, 5, 6], header=0, index_col=0, dtype={'dwp_oi': str})
        df = pd.read_excel(steentoetsFile, skiprows=[1, 2, 3, 4, 5, 6], header=0, dtype={'dwp_oi': str})
        df_profile = df.loc[df['dwp_oi'] == dwarsprofiel]
        df_profile = df_profile[
            ['Zo_oi', 'Zb_oi', 'tana_oi', 'Bsegment_oi', 'toplaagtype_oi', 'D_oi', 'rho_oi', 'Unnamed: 77',
             'Unnamed: 93']]

    elif "17.1.1.1" in str(steentoetsFile):
        print("Steentoets versie is 17.1.1.1")
        # df = pd.read_excel(steentoetsFile, skiprows=[1, 2, 3, 4, 5, 6], header=0, index_col=0, dtype={'dwp_oi': str})
        df = pd.read_excel(steentoetsFile, skiprows=[1, 2, 3, 4, 5, 6], header=0, dtype={'dwp_oi': str})
        df_profile = df.loc[df['dwp_oi'] == dwarsprofiel]
        df_profile = df_profile[
            ['Yl_oi','Zl_oi', 'Yr_oi', 'Zr_oi','toplaagtype_oi', 'D_oi', 'rho_oi', 'Unnamed: 77',
             'Unnamed: 93']]
        # determine width of each secgment (Bsegment_oi) by subtracting Yl_oi from Yr_oi and insert as new column in
        # df_profile at position 3
        df_profile.insert(4, 'Bsegment_oi', df_profile['Yr_oi'] - df_profile['Yl_oi'])
        # determine tan(alpha) of each segment (tana_oi) by subtracting Zl_oi from Zr_oi and dividing by Bsegment_oi and
        # insert as new column in df_profile at position 3
        df_profile.insert(4, 'tana_oi', (df_profile['Zr_oi'] - df_profile['Zl_oi']) / df_profile['Bsegment_oi'])
        # delete columns Yl_oi and Yr_oi
        df_profile = df_profile.drop(['Yl_oi', 'Yr_oi'], axis=1)

    else:
        raise Exception("Steentoets versie is onbekend. Zorg dat het versienummer in de naam van het steentoetsbestand staat.")

    #rename columns to match the old code
    df_profile.columns = ['Zo', 'Zb', 'tana', 'Bsegment', 'toplaagtype', 'D', 'rho_s', 'Hs_ini', 'overschot']
    for col in df_profile.columns:
        df_profile[col] = df_profile[col].astype('float')

    # Give outer berms a very mild slope to prevent division by 0 later in the vrtool
    # check if tan_a is zero. If so, check if slope of previous and next segment are positive. If so, set tan_a to 0.001
    # and lower previous Zb with (0.001 * Bsegment)/2 and increase next Zo with (0.001 * Bsegment)/2
    for i in range(1, len(df_profile)-1):
        if df_profile['tana'].iloc[i] == 0.0:
            if (df_profile['tana'].iloc[i - 1] > 0.0) & (df_profile['tana'].iloc[i + 1] > 0.0):
                # print("horizontal outer berm adjusted: given a very mild slope")
                df_profile['tana'].iloc[i] = 0.001
                df_profile['Zb'].iloc[i - 1] = df_profile['Zb'].iloc[i - 1] - (0.001 * df_profile['Bsegment'].iloc[i]) / 2
                df_profile['Zo'].iloc[i + 1] = df_profile['Zo'].iloc[i + 1] + (0.001 * df_profile['Bsegment'].iloc[i]) / 2
                df_profile['Zo'].iloc[i] = df_profile['Zb'].iloc[i - 1] - (0.001 * df_profile['Bsegment'].iloc[i]) / 2
                df_profile['Zb'].iloc[i] = df_profile['Zo'].iloc[i + 1] + (0.001 * df_profile['Bsegment'].iloc[i]) / 2

    # go backwards through df_profile. While last row has tana equal to 0 or negative, remove this row (unless tana of
    # the of the section in front is positive: because that is the crest
    while df_profile['tana'].iloc[-1] <= 0.0 and df_profile['tana'].iloc[-2] <= 0.0:
        print("Horizontal or negative part of the slope removed. Dijkvak:", dwarsprofiel)
        print("slope (tan alpha) was:", df_profile['tana'].index[-1])
        df_profile = df_profile.drop(df_profile.index[-1])

    # go backwards through df_profile. While last row has tana equal to 0 or negative, remove this row of the previous
    # tana is not positive. If tana is positive, break the loop. This ensures only crest remains (with minimal slope)
    # while df_profile['tana'].iloc[-1] <= 0.0:
    #     if df_profile['tana'].iloc[-2] > 0.0:
    #         pass
    #     elif df_profile['tana'].iloc[-2] <= 0.0:
    #         df_profile['tana'].iloc[-1] = 0.001
    #         df_profile['Zb'].iloc[-1] = df_profile['Zb'].iloc[-1] + (0.001 * df_profile['Bsegment'].iloc[-1])
    #         # break the while loop
    #         break
    #     else:
    #         df_profile = df_profile.drop(df_profile.index[-1])

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