# -*- coding: utf-8 -*-
"""
Created on Sun Apr 30 12:01:20 2023

@author: wojciech
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
from project_utils.bisection import bisection
import math
from scipy.stats import norm
from scipy.special import ndtri
import warnings

def issteen(toplaagtype):
    
    res = False
    
    if toplaagtype>=26.0 and toplaagtype<=27.9:
        res = True
    
    return res

def isgras(toplaagtype):
    
    res = False
    
    if toplaagtype==20.0:
        res = True
     
    return res

def beta_comb(betaZST, betaGEBU):
    
    if np.all(np.isnan(betaZST)):
        probZST = 0.0
    else:
        probZST = norm.cdf(-np.nanmin(betaZST))
    
    if np.all(np.isnan(betaGEBU)):
        probGEBU = 0.0
    else:
        probGEBU = norm.cdf(-np.nanmin(betaGEBU))
        
    probComb = probZST + probGEBU
    betaComb = -ndtri(probComb)
    return betaComb

def evaluate_bekleding(dataZST, dataGEBU):
    
    betaZST = []
    betaGEBU = []
    
    for i in range(0, dataZST['aantal deelvakken']):
        
        if issteen(dataZST['toplaagtype'][i]): # for steen
            
            betaZST.append(evaluate_steen(dataZST['D huidig'][i], dataZST[f'deelvak {i}']['D_opt'], dataZST[f'deelvak {i}']['betaFalen']))
            betaGEBU.append(np.nan)

        elif isgras(dataZST['toplaagtype'][i]): # for gras
            
            betaZST.append(np.nan)
            betaGEBU.append(evaluate_gras(dataZST['overgang huidig'], dataGEBU['grasbekleding_begin'], dataGEBU['betaFalen']))
            
        else:
            
            betaZST.append(np.nan)
            betaGEBU.append(np.nan)
            
    return betaZST, betaGEBU

def apply_measure(count, beta, h_onder, dataZST, dataGEBU, kruinhoogte):

    measure = {'Zo': list(), 'Zb': list(), 'toplaagtype': list(), 
               'D': list(), 'betaZST': list(), 'betaGEBU': list(),
               'previous toplaagtype': list(), 'reinforce': list(), 
               'tana': list()}
    
    count = 0
    for i in range(0, dataZST['aantal deelvakken']):
        
        if dataZST['Zb'][i] <= h_onder:
            
            count += 1
            # steen
            topd, betares, reinforce = design_steen(beta, dataZST[f'deelvak {i}']['D_opt'], 
                                                   dataZST[f'deelvak {i}']['betaFalen'], 
                                                   dataZST['toplaagtype'][i],
                                                   dataZST['D huidig'][i])
            
            measure['Zo'].append(dataZST['Zo'][i])
            measure['Zb'].append(dataZST['Zb'][i])
            measure['toplaagtype'].append(dataZST['toplaagtype'][i])
            measure['previous toplaagtype'].append(dataZST['toplaagtype'][i])
            measure['D'].append(topd)
            measure['betaZST'].append(betares)
            measure['betaGEBU'].append(np.nan)
            measure['reinforce'].append(reinforce)
            measure['tana'].append(dataZST['tana'][i])
    
        elif dataZST['Zo'][i] < h_onder and dataZST['Zb'][i] > h_onder: # part is steen and part is gras
            
            count += 2
            # steen
            topd, betares, reinforce = design_steen(beta, dataZST[f'deelvak {i}']['D_opt'], 
                                                   dataZST[f'deelvak {i}']['betaFalen'], 
                                                   dataZST['toplaagtype'][i],
                                                   dataZST['D huidig'][i])
            
            measure['Zo'].append(dataZST['Zo'][i])
            measure['Zb'].append(h_onder)
            measure['toplaagtype'].append(dataZST['toplaagtype'][i])
            measure['previous toplaagtype'].append(dataZST['toplaagtype'][i])
            measure['D'].append(topd)
            measure['betaZST'].append(betares)
            measure['betaGEBU'].append(np.nan)
            measure['reinforce'].append(reinforce)
            measure['tana'].append(dataZST['tana'][i])
            
            # gras
            measure['Zo'].append(h_onder)
            measure['Zb'].append(dataZST['Zb'][i])
            measure['toplaagtype'].append(20.0)
            measure['previous toplaagtype'].append(dataZST['toplaagtype'][i])
            measure['D'].append(np.nan)
            measure['betaZST'].append(np.nan)
            measure['betaGEBU'].append(evaluate_gras(h_onder, dataGEBU['grasbekleding_begin'], dataGEBU['betaFalen']))
            measure['reinforce'].append('yes')
            measure['tana'].append(dataZST['tana'][i])
            
        elif dataZST['Zo'][i] >= h_onder: # gras
            
            count += 1
            # gras
            measure['Zo'].append(dataZST['Zo'][i])
            measure['Zb'].append(dataZST['Zb'][i])
            measure['toplaagtype'].append(20.0)
            measure['previous toplaagtype'].append(dataZST['toplaagtype'][i])
            measure['D'].append(np.nan)
            measure['betaZST'].append(np.nan)
            measure['betaGEBU'].append(evaluate_gras(h_onder, dataGEBU['grasbekleding_begin'], dataGEBU['betaFalen']))
            measure['reinforce'].append('yes')
            measure['tana'].append(dataZST['tana'][i])

    if h_onder >= np.max(dataZST['Zb']):
        
        if h_onder>=kruinhoogte:
            raise ValueError("Overgang >= kruinhoogte")
        
        count += 1
        # gras
        measure['Zo'].append(h_onder)
        measure['Zb'].append(kruinhoogte)
        measure['toplaagtype'].append(20.0)
        measure['previous toplaagtype'].append(np.nan)
        measure['D'].append(np.nan)
        measure['betaZST'].append(np.nan)
        measure['betaGEBU'].append(evaluate_gras(h_onder, dataGEBU['grasbekleding_begin'], dataGEBU['betaFalen']))
        measure['reinforce'].append('yes')
        measure['tana'].append(dataZST['tana'][i])
            
    return count, measure

def design_steen(beta, D_opt, betaFalen, toplaagtype, D):
    
    if issteen(toplaagtype): # only for steen

        fsteen = interpolate.interp1d(D_opt, np.array(betaFalen) - beta, fill_value=('extrapolate'))
        try:
            topd = bisection(fsteen, 0.0, 1.0, 0.01)
            topd = math.ceil(topd/0.05)*0.05
            betares = beta
            reinforce = 'yes'
        except:
            topd = np.nan
            betares = np.nan
            reinforce = 'no'

        if topd <= D:
            warnings.warn("Design D is <= than the current D")
            topd = D
            betares = evaluate_steen(topd, D_opt, betaFalen)
            reinforce = 'no'
        
    else: # other type
        
        topd = D
        betares = np.nan
        reinforce = 'no'
        
    return topd, betares, reinforce

def evaluate_steen(D, D_opt, betaFalen):
    
    fsteen = interpolate.interp1d(D_opt, betaFalen, fill_value=('extrapolate'))
    beta = fsteen(D)
    
    return beta
    
def add_steen(h_onder, measure):
    
    for i in range(0, len(measure['toplaagtype'])):
        if issteen(measure['toplaagtype'][i]):
            D_last = measure['D'][i]
            betaZST_last = measure['betaZST'][i]
    
    for i in range(0, len(measure['toplaagtype'])):
        if isgras(measure['previous toplaagtype'][i]) and measure['Zo'][i]<h_onder:
            measure['D'][i] = D_last
            measure['toplaagtype'][i] = 2026.0
            measure['betaZST'][i] = betaZST_last
            measure['reinforce'][i] = 'yes'
    
    return measure
    
def evaluate_gras(h_onder, grasbekleding_begin, betaFalen):
        
    fgras = interpolate.interp1d(grasbekleding_begin, betaFalen, fill_value=('extrapolate'))
    beta = fgras(h_onder)
    
    return beta

def plot_bekleding(index, year, h_onder, beta, dijk_x, dijk_y, measure):
    
    plt.figure()
    plt.plot(dijk_x, dijk_y,'b')
    
    for i in range(0, len(measure['Zo'])):
        
        bek_y = np.arange(measure['Zo'][i], measure['Zb'][i], 0.05)
        bek_x = np.interp(bek_y, dijk_y, dijk_x)
        
        if issteen(measure['toplaagtype'][i]):
            plt.plot(bek_x, bek_y, '0.9', linewidth=measure['D'][i]*50)
        elif measure['toplaagtype'][i]==2026.0:
            plt.plot(bek_x, bek_y, '0.5', linewidth=measure['D'][i]*50)
        elif isgras(measure['toplaagtype'][i]):
            plt.plot(bek_x, bek_y, 'g', linewidth=5.0)
    
    plt.grid()
    plt.xlabel('X [m]')
    plt.xlabel('Z [m+NAP]')
    plt.title(f'overgang = {h_onder}, beta_steen = {beta}')
    plt.savefig(f'Figures_integrate/design_{index}_{year}_{h_onder}_{beta}.png')