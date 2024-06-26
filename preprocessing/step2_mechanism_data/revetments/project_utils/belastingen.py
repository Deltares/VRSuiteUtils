# -*- coding: utf-8 -*-
"""
Created on Tue Mar 21 15:05:24 2023

@author: wojciech
"""

import numpy as np
from scipy import interpolate

def waterstandsverloop(region, GWS, MHW, Amp, Qvar_h, Qvar_Hs):
    
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

        # the considered water level is equal to the water level where max Hs is found
        # the duration of the water level is 12 hours
        waterstand = np.array([Qvar_h[np.argmax(Qvar_Hs)]])
        tijd = np.array([0.0, 12.0]) 
    
    return tijd, waterstand

def Hs_verloop(waterstand, h_Qvar, Hs_Qvar):
    
    f = interpolate.interp1d(h_Qvar, Hs_Qvar, fill_value='extrapolate')
    Hs = f(waterstand)
    Hs[Hs<=0.0] = 0.0001
    
    return Hs

def Tp_verloop(waterstand, h_Qvar, Tp_Qvar):
    
    f = interpolate.interp1d(h_Qvar, Tp_Qvar, fill_value='extrapolate')
    Tp = f(waterstand)
    Tp[Tp<=0.0] = 0.0001
    
    return Tp

def betahoek_verloop(waterstand, h_Qvar, dir_Qvar, orientation):    

    wavedir = np.interp(waterstand, h_Qvar, dir_Qvar)
    
    betahoek = abs(wavedir - orientation)
    betahoek[np.where(betahoek>180.0)] = betahoek[np.where(betahoek>180.0)]-360.0
    
    return betahoek