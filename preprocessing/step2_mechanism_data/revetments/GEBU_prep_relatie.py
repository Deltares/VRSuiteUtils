# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 14:40:54 2023

@author: wojciech
"""
import numpy as np
import pandas as pd
from project_utils.belastingen import waterstandsverloop, Hs_verloop, Tp_verloop, betahoek_verloop
from scipy.special import ndtri
from scipy.stats import norm
from project_utils.DiKErnel import DIKErnelCalculations, write_JSON_to_file, read_JSON, read_prfl
import matplotlib.pyplot as plt
from scipy import interpolate
from project_utils.bisection import bisection
from pathlib import Path



# inputs
input_dir = Path(r'c:\VRM\test_revetments')
bekleding_path = Path(r'Bekleding_default.csv')
output_dir = Path(r'c:\VRM\test_revetments\output')
# binDIKErnel = Path(r'c:\VRM\test_revetments\bin_DiKErnel')
binDIKErnel = 'c:/VRM/test_revetments/bin_DiKErnel/'

figures_GEBU = Path(r'c:\VRM\test_revetments\figures_GEBU')

typeZode = 'grasGeslotenZode'
models = ['gras_golfklap', 'gras_golfoploop']
evaluateYears = [2025, 2100]
indexvak = [0, 1, 2]

# if figures_GEBU doesnot exist, create it
if not figures_GEBU.exists():
    figures_GEBU.mkdir()
# elif figures_GEBU exists, but not empty, stop the script
elif figures_GEBU.exists() and len(list(figures_GEBU.iterdir())) != 0:
    print('The figure folder is not empty. Please empty the figures_GEBU folder and run the script again.')
    exit()

# read revetment file
df = pd.read_csv(input_dir.joinpath('Bekleding_default.csv'),
                 usecols=['vaknaam', 'dwarsprofiel', 'signaleringswaarde', 'ondergrens', 'locationid', 'prfl',
                          'hrdatabase_folder', 'hrdatabase', 'region', 'gws', 'getij_amplitude', 'begin_grasbekleding',
                          'qvar_p1', 'qvar_p2', 'qvar_p3', 'qvar_p4', 'qvar_stap'])
df = df.dropna(subset=['vaknaam']) # drop rows where vaknaam is Not a Number

for index in indexvak:
    
    orientation, kruinhoogte, dijkprofiel_x, dijkprofiel_y = read_prfl(input_dir.joinpath('profielen/' + df['prfl'].values[index]))

    dwarsprofiel = df['dwarsprofiel'].values[index]
    signaleringswaarde = df['signaleringswaarde'].values[index]
    ondergrens = df['ondergrens'].values[index]
    GWS = df['gws'].values[index] # gemiddelde buitenwaterstand
    Amp = df['getij_amplitude'].values[index] # getij amplitude
    region = df['region'][index]
    begin_grasbekleding = df['begin_grasbekleding'][index]
    Qvar_p1 = df['qvar_p1'].values[index]
    Qvar_p2 = df['qvar_p2'].values[index]
    Qvar_p3 = df['qvar_p3'].values[index]
    Qvar_p4 = df['qvar_p4'].values[index]

    grasbekleding_begin = np.arange(begin_grasbekleding, kruinhoogte - 0.1, 0.25)
    grasbekleding_end = kruinhoogte
    
    prob = [Qvar_p1, Qvar_p2, Qvar_p3, Qvar_p4]
    beta = -ndtri(prob)

    # import Q-variant results
    Qvar = read_JSON(output_dir.joinpath("Qvar_{}.json".format(index)))
    
    # get time series
    h_series = []
    Hs_series = []
    Tp_series = []
    betahoek_series = []
    for i in range(0, len(evaluateYears)):
        
        for j in range(0, len(prob)):
            
            for k in range(0,len(models)):
            
                valMHW = Qvar[f'MHW {i}_{j}']
                Qvar_h = np.array(Qvar[f'Qvar {i}_{j}_{models[k]}']['waterstand'])
                Qvar_Hs = np.array(Qvar[f'Qvar {i}_{j}_{models[k]}']['Hs'])    
                Qvar_Tp = np.array(Qvar[f'Qvar {i}_{j}_{models[k]}']['Tp'])    
                Qvar_dir = np.array(Qvar[f'Qvar {i}_{j}_{models[k]}']['dir'])    
                
                tijd, h_hulp = waterstandsverloop(region, GWS, valMHW, Amp)
                Hs_hulp = Hs_verloop(h_hulp, Qvar_h, Qvar_Hs)
                Tp_hulp = Tp_verloop(h_hulp, Qvar_h, Qvar_Tp)
                betahoek_hulp = betahoek_verloop(h_hulp, Qvar_h, Qvar_dir, orientation)
                tijdstippen = 3600.0*tijd
                
                h_series = np.append(h_series, h_hulp)
                Hs_series = np.append(Hs_series, Hs_hulp)
                Tp_series = np.append(Tp_series, Tp_hulp)
                betahoek_series = np.append(betahoek_series, betahoek_hulp)
                
    h_series = h_series.reshape(len(evaluateYears), len(prob), len(models), len(tijd))
    Hs_series = Hs_series.reshape(len(evaluateYears), len(prob), len(models), len(tijd))
    Tp_series = Tp_series.reshape(len(evaluateYears), len(prob), len(models), len(tijd))
    betahoek_series = betahoek_series.reshape(len(evaluateYears), len(prob), len(models), len(tijd))
    
    # run DiKErnel
    SF = []
    for i in range(0, len(evaluateYears)):
        
        for j in range(0, len(prob)):
            
            valMHW = Qvar[f'MHW {i}_{j}']
            
            for k in range(0, len(grasbekleding_begin)):
                
                golfklap = False
                golfoploop = False
                positions_golfklap = []
                positions_golfoploop = []
                
                if grasbekleding_end<=valMHW: # golfklap
                    positions = np.arange(grasbekleding_begin[k], grasbekleding_end, 0.1)
                    positions_golfklap = np.interp(positions, dijkprofiel_y, dijkprofiel_x)
                    golfklap = True
                elif grasbekleding_begin[k]>=valMHW: # golfoploop
                    positions = np.array([grasbekleding_begin[k]])
                    positions_golfoploop = np.interp(positions, dijkprofiel_y, dijkprofiel_x)
                    golfoploop = True
                else: # in between --> then only golfklap
                    positions = np.arange(grasbekleding_begin[k], valMHW, 0.1)
                    positions_golfklap = np.interp(positions, dijkprofiel_y, dijkprofiel_x)
                    positions = np.array([valMHW])
                    positions_golfoploop = np.interp(positions, dijkprofiel_y, dijkprofiel_x)
                    golfklap = True
                    golfoploop = True
        
                plt.figure()
                plt.plot(dijkprofiel_x, dijkprofiel_y,'g')
                plt.plot(positions_golfklap, np.interp(positions_golfklap, dijkprofiel_x, dijkprofiel_y),'ro')
                plt.plot(positions_golfoploop, np.interp(positions_golfoploop, dijkprofiel_x, dijkprofiel_y),'bo')
                plt.plot(dijkprofiel_x, np.full_like(dijkprofiel_x, valMHW),'b--')
                plt.grid()
                plt.xlabel('Horizontale richting dijk x [m]')
                plt.ylabel('Verticale richting dijk z [m+NAP]')
                plt.close()
                plt.savefig(figures_GEBU.joinpath('posities_{}_{}_prob_{}_set_{}.png'.format(index,
                                                                                             evaluateYears[i], j, k)))
    
                maxSchadegetal_golfklap = 0.0            
                if golfklap:
                    ind = 0 # golfklap
                    
                    for p in positions_golfklap:
                        bek = DIKErnelCalculations(tijdstippen, h_series[i,j,ind,:], Hs_series[i,j,ind,:], Tp_series[i,j,ind,:], betahoek_series[i,j,ind,:], dijkprofiel_x, dijkprofiel_y, p)
                        bek.gras_golfklap_input_JSON(typeZode)
                        maxSchadegetal_golfklap = np.max([maxSchadegetal_golfklap, bek.run_DIKErnel(binDIKErnel)])
                    
                maxSchadegetal_golfoploop = 0.0            
                if golfoploop:
                    ind = 1 # golfoploop
                                
                    for p in positions_golfoploop:
                        bek = DIKErnelCalculations(tijdstippen, h_series[i,j,ind,:], Hs_series[i,j,ind,:], Tp_series[i,j,ind,:], betahoek_series[i,j,ind,:], dijkprofiel_x, dijkprofiel_y, p)
                        bek.gras_golfoploop_input_JSON(typeZode)
                        maxSchadegetal_golfoploop = np.max([maxSchadegetal_golfoploop, bek.run_DIKErnel(binDIKErnel)])
                
                maxSchadegetal = np.max([maxSchadegetal_golfklap, maxSchadegetal_golfoploop, 10**(-4)])
                SF = np.append(SF, 1/maxSchadegetal)
            
    SF = SF.reshape(len(evaluateYears), len(prob), len(grasbekleding_begin))
    
    # get relation between h_overgang and beta
    betaFalen = []
    years = []
    for i in range(0, len(evaluateYears)):
        for j in range(0, len(grasbekleding_begin)):
            
            f = interpolate.interp1d(beta, SF[i,:,j]-1.0, fill_value=('extrapolate'))
            try:
                betaFalen = np.append(betaFalen, bisection(f, 0.0, 10.0, 0.01)) # looking for root
            except:
                if f(0.0)<0.0 and f(10.0)<0.0:
                    betaFalen = np.append(betaFalen, 0.0)
                elif f(0.0)>0.0 and f(10.0)>0.0:
                    betaFalen = np.append(betaFalen, np.max(beta))
                else:
                    betaFalen = np.append(betaFalen, np.nan)
            
            years = np.append(years, evaluateYears[i])
    
    # scenario 2025 cannot be worse than scenario 2100
    beta_1 = betaFalen[np.argwhere(years==evaluateYears[0])]
    beta_2 = betaFalen[np.argwhere(years==evaluateYears[1])]
    beta_2 = np.min([beta_1, beta_2], axis=0)
    betaFalen = np.append(beta_1, beta_2)
    
    betaFalen = betaFalen.reshape(len(evaluateYears), len(grasbekleding_begin))
    
    # export results to JSON
    for i in range(0, len(evaluateYears)):
        data = {"zichtjaar": evaluateYears[i]/1.0,
                "dwarsprofiel": dwarsprofiel/1.0,
                "dijkprofiel_x": list(dijkprofiel_x),
                "dijkprofiel_y": list(dijkprofiel_y),
                "grasbekleding_begin": list(grasbekleding_begin), 
                "betaFalen": list(betaFalen[i])}        
        write_JSON_to_file(data, output_dir.joinpath("GEBU_{}_{}.json".format(index, evaluateYears[i])))
    
    # plot safety factor
    for i in range(0, len(evaluateYears)):
        for j in range(0, len(grasbekleding_begin)):        
            plt.figure()
            plt.semilogx(1/np.array(prob), SF[i,:,j], 'o--')
            plt.semilogx(1/np.array(prob), np.full_like(SF[i,:,j], 1.0), 'k')
            plt.grid()
            plt.xlabel('Terugkeertijd [jaar]')
            plt.ylabel('SF [-]')
            plt.title(f'Begin gras = {grasbekleding_begin[j]} m+NAP, eind gras = {grasbekleding_end} m+NAP')
            plt.close()
            plt.savefig(figures_GEBU.joinpath('safetyFactor_{}_{}_overhang_{}.png'.format(index, evaluateYears[i], j)))

    # plot beta
    plt.figure()
    for i in range(0, len(evaluateYears)):
        probFalen = norm.cdf(-betaFalen[i,:])
        plt.semilogy(grasbekleding_begin, probFalen, 'o--', label = f'year= {evaluateYears[i]}')
    plt.grid()
    plt.legend()
    plt.xlabel('h_overgang [m+NAP]')
    plt.ylabel('Faalkans [1/jaar]')
    plt.close()
    plt.savefig(figures_GEBU.joinpath('betaFalen_{}.png'.format(index)))

    # plot water levels
    # plt.figure()
    # for i in range(0, len(evaluateYears)):
    #     plt.semilogx(1.0/np.array(prob), valMHW[i,:], 'o--', label=str(evaluateYears[i]))
    # plt.legend()
    # plt.grid()
    # plt.xlabel('Terugkeertijd [jaar]')    
    # plt.ylabel('Waterstand [m+NAP]')
    # plt.close
    # plt.savefig(f'Figures_GEBU/waterstand_{index}.png')
    
    # plot time series
    for i in range(0, len(evaluateYears)):
        
        for j in range(0, len(prob)):
    
            for k in range(0, len(models)):
                
                plt.plot()    
                fig, axs = plt.subplots(2, 2)
                axs[0, 0].plot(tijd, h_series[i,j,k,:])
                axs[0, 0].set_title('Waterstand (boven), Tp (onder)', fontdict={'fontsize':8})
                axs[0, 0].grid()
                axs[0, 1].plot(tijd, Hs_series[i,j,k,:])
                axs[0, 1].set_title('Hs (boven), hoek (onder)', fontdict={'fontsize':8})
                axs[0, 1].grid()
                axs[1, 0].plot(tijd, Tp_series[i,j,k,:])
                axs[1, 0].grid()
                axs[1, 1].plot(tijd, betahoek_series[i,j,k,:])
                axs[1, 1].grid()
                plt.close()
                plt.savefig(figures_GEBU.joinpath('belasting_{}_{}_{}_{}.png'.format(index, evaluateYears[i], j, k)))
