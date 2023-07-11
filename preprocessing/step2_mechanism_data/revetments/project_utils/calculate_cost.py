# -*- coding: utf-8 -*-
"""
Created on Thu May 18 08:50:12 2023

@author: wojciech
"""

import numpy as np
from scipy import interpolate
from project_utils.functions_integrate import issteen, isgras

def get_cost_measure(measure, vak_length, year):
    
    cost = list()
    for i in range(0, len(measure['Zo'])):
        
        if measure['reinforce'][i] == 'yes':
            
            cost.append(get_cost_vlak(measure['toplaagtype'][i],
                                      measure['previous toplaagtype'][i],
                                      measure['D'][i], 
                                      measure['Zo'][i], 
                                      measure['Zb'][i],
                                      measure['tana'][i],
                                      vak_length, year))
        else:
            cost.append(0.0)
            
    return cost

def get_cost_vlak(toplaagtype, prev_toplaagtype, D_in, y1, y2, tana, vak_length, year):
    
    opslagfactor = 2.509
    discontovoet = 1.02
    
    # Opnemen en afvoeren oude steenbekleding naar verwerker (incl. stort-/recyclingskosten)
    cost_remove_steen = 5.49
    
    # Opnemen en afvoeren teerhoudende oude asfaltbekleding (D=15cm) (incl. stort-/recyclingskosten)
    cost_remove_asfalt = 13.52
    
    # Leveren en aanbrengen (verwerken) betonzuilen, incl. doek, vijlaag en inwassen
    D = np.array([0.3, 0.35, 0.4, 0.45, 0.5])
    cost = np.array([72.52, 82.70, 92.56, 102.06, 111.56])
    f = interpolate.interp1d(D, cost, fill_value=('extrapolate'))
    cost_new_steen = f(D_in)
    
    x = (y2-y1)/tana
    
    if x<0.0 or y2<y1:
        raise ValueError("Calculation of design area not possible!")
    
    # calculate area of new design
    z = np.sqrt(x**2 + (y2-y1)**2)
    area = z * vak_length
    
    if issteen(toplaagtype): # cost of new steen
        cost_vlak = cost_remove_steen + cost_new_steen
    elif toplaagtype==2026.0: # cost of new steen, when previous was gras
        cost_vlak = cost_new_steen
    elif isgras(toplaagtype): # cost of removing old revetment when new revetment is gras
        if prev_toplaagtype==5.0:
            cost_vlak = cost_remove_asfalt
        elif prev_toplaagtype==20.0:
            cost_vlak = 0.0
        else:
            cost_vlak = cost_remove_steen
    else:
        cost_vlak = 0.0
    
    cost_vlak = area * cost_vlak * opslagfactor / discontovoet**(year-2025)
    
    return cost_vlak