# -*- coding: utf-8 -*-
"""
Created on Sun Apr 23 13:16:42 2023

@author: wojciech
"""
import numpy as np
import pandas as pd

def read_steentoets_file(steentoetsFile, dwarsprofiel):

    df = pd.read_excel(steentoetsFile)
    profiel = df['dwp_oi'].values[6:-1]
    Zo = df['Zo_oi'].values[6:-1]
    Zb = df['Zb_oi'].values[6:-1]
    tana = df['tana_oi'].values[6:-1]
    Bsegment = df['Bsegment_oi'].values[6:-1]
    toplaagtype = df['toplaagtype_oi'].values[6:-1]
    D = df['D_oi'].values[6:-1]
    rho_s = df['rho_oi'].values[6:-1]
    Hs_ini = df['Unnamed: 77'].values[6:-1]
    overschot = df['Unnamed: 93'].values[6:-1]
    rho = 1025.0
    
    ind = np.argwhere((profiel==dwarsprofiel) & (tana>0.0))[:,0]
    
    Zo = Zo[ind].astype('float')
    Zb = Zb[ind].astype('float')
    tana = tana[ind].astype('float')
    Bsegment = Bsegment[ind].astype('float')
    toplaagtype = toplaagtype[ind].astype('float')
    D = D[ind].astype('float')
    rho_s = rho_s[ind].astype('float')
    Hs_ini = Hs_ini[ind].astype('float')
    overschot = overschot[ind].astype('float')
            
    delta = (rho_s - rho)/rho
    D_voldoet = D - overschot
    ratio_voldoet = Hs_ini/(delta * D_voldoet)
    overgang = min(Zo[toplaagtype==20.0])
    
    # correct cases with no data
    D_voldoet[overschot>10**7] = np.nan
    ratio_voldoet[overschot>10**7] = np.nan
    Hs_ini[overschot>10**7] = np.nan
    overschot[overschot>10**7] = np.nan
    
    return Zo, Zb, overgang, tana, Bsegment, toplaagtype, D, rho_s, Hs_ini, overschot, delta, D_voldoet, ratio_voldoet