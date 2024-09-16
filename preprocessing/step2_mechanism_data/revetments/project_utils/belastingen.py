# -*- coding: utf-8 -*-
"""
Created on Tue Mar 21 15:05:24 2023

@author: wojciech
"""

import numpy as np
from scipy import interpolate

def waterstandsverloop(region, GWS, MHW, Amp, Qvar_h):
    
    if region == 'meer':
        
        duur = 36
        t_top = duur/2.0
        tijd = np.arange(0, duur, 1)
    
        waterstand = np.interp(tijd, [0.0, t_top - 2.0, t_top, t_top + 2.0, duur], [GWS, MHW - 0.1, MHW, MHW - 0.1, GWS])
    
    elif region == 'kust':
        
        t_basis = 36 # basis of trapezium
        t_peak = 4 # 0.5 of peak duration
        omega = 12
        delta = 1

        tijd = np.arange(-0.5*t_basis, 0.5*t_basis, delta)
        t_peak  = t_peak*np.full_like(tijd, 1.0)
        t_max = np.full_like(tijd, 0.0)

        delta_h = (MHW-Amp)/(0.5*(t_basis-t_peak))
        waterstand = Amp*np.cos(2*np.pi*tijd/omega) + (MHW-Amp)-np.maximum(abs(tijd)-0.5*t_peak,t_max)*delta_h
        
        tijd = tijd + t_basis/2.0 # shift to positive

    elif region == 'rivieren':

        # constant at MHW
        waterstand = np.array([MHW, MHW])
        tijd = np.array([0.0, 12.0])
    
    return tijd * 3600.0, waterstand

def Hs_verloop(waterstand, h_Qvar, Hs_Qvar):
    def get_Hs(h_Qv, Hs_Qv):
        f = interpolate.interp1d(h_Qv, Hs_Qv, fill_value='extrapolate')
        return f(waterstand)

    Hs = get_Hs(h_Qvar, Hs_Qvar)
    if any(np.isnan(Hs)):
        #take unique values of h_Qvar
        h_Qvar2, unique_indices = np.unique(h_Qvar, return_index=True)
        #take the corresponding Hs_Qvar values
        Hs_Qvar2 = np.array(Hs_Qvar)[unique_indices]
        #interpolate the Hs values
        Hs = get_Hs(h_Qvar2, Hs_Qvar2)
    
    Hs[Hs<0.01] = 0.01
    return Hs

def Tp_verloop(waterstand, h_Qvar, Tp_Qvar):
    def get_Tp(h_Qv, Tp_Qv):
        f = interpolate.interp1d(h_Qv, Tp_Qv, fill_value='extrapolate')
        return f(waterstand)
    Tp = get_Tp(h_Qvar, Tp_Qvar)

    if any(np.isnan(Tp)):
        #take unique values of h_Qvar
        h_Qvar2, unique_indices = np.unique(h_Qvar, return_index=True)
        #take the corresponding Tp_Qvar values
        Tp_Qvar2 = np.array(Tp_Qvar)[unique_indices]
        #interpolate the Tp values
        Tp = get_Tp(h_Qvar2, Tp_Qvar2)

    Tp[Tp<=1.0] = 1.0
    
    return Tp

def betahoek_verloop(waterstand, h_Qvar, dir_Qvar, orientation):    

    wavedir = np.interp(waterstand, h_Qvar, dir_Qvar)
    
    betahoek = abs(wavedir - orientation)
    betahoek[np.where(betahoek>180.0)] = betahoek[np.where(betahoek>180.0)]-360.0
    
    return betahoek