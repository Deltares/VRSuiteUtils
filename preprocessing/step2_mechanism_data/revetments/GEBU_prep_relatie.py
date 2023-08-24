# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 14:40:54 2023

@author: wojciech
"""
import numpy as np
import pandas as pd
from scipy.special import ndtri
from scipy.stats import norm
import matplotlib.pyplot as plt
from scipy import interpolate
from pathlib import Path
from preprocessing.step2_mechanism_data.revetments.project_utils.belastingen import waterstandsverloop, Hs_verloop, Tp_verloop, betahoek_verloop
from preprocessing.step2_mechanism_data.revetments.project_utils.DiKErnel import DIKErnelCalculations, write_JSON_to_file, read_JSON, read_prfl
from preprocessing.step2_mechanism_data.revetments.project_utils.bisection import bisection


def revetment_gebu(df, profielen_path, output_path, binDIKErnel, figures_GEBU, local_path, p_grid):

    # define variables
    typeZode = 'grasGeslotenZode'
    models = ['gras_golfklap', 'gras_golfoploop']
    evaluateYears = [2025, 2100]



    for index, row in df.iterrows():

        orientation, kruinhoogte, dijkprofiel_x, dijkprofiel_y = read_prfl(profielen_path.joinpath(df['prfl'].values[index]))

        dwarsprofiel = row.dwarsprofiel
        GWS = row['gws'] # gemiddelde buitenwaterstand
        Amp = row['getij_amplitude'] # getij amplitude
        region = row['region']
        begin_grasbekleding = row['begin_grasbekleding']

        transition_levels = np.arange(begin_grasbekleding, kruinhoogte - 0.1, 0.25)
        grasbekleding_end = kruinhoogte

        beta = -ndtri(p_grid)

        # import Q-variant results
        Qvar = read_JSON(output_path.joinpath("Qvar_{}.json".format(row.doorsnede)))

        # get time series
        h_series = []
        Hs_series = []
        Tp_series = []
        betahoek_series = []
        for i, year in enumerate(evaluateYears):

            for j, p in enumerate(p_grid):

                for k,model in enumerate(models):

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

        h_series = h_series.reshape(len(evaluateYears), len(p_grid), len(models), len(tijd))
        Hs_series = Hs_series.reshape(len(evaluateYears), len(p_grid), len(models), len(tijd))
        Tp_series = Tp_series.reshape(len(evaluateYears), len(p_grid), len(models), len(tijd))
        betahoek_series = betahoek_series.reshape(len(evaluateYears), len(p_grid), len(models), len(tijd))

        # run DiKErnel
        SF = []
        for i, year in enumerate(evaluateYears):

            for j, p in enumerate(p_grid):

                valMHW = Qvar[f'MHW {i}_{j}']

                for k, transition_level in enumerate(transition_levels):

                    golfklap = False
                    golfoploop = False
                    positions_golfklap = []
                    positions_golfoploop = []

                    if grasbekleding_end<=valMHW: # golfklap
                        positions = np.arange(transition_level, grasbekleding_end, 0.1)
                        positions_golfklap = np.interp(positions, dijkprofiel_y, dijkprofiel_x)
                        golfklap = True
                    elif transition_level>=valMHW: # golfoploop
                        positions = np.array([transition_level])
                        positions_golfoploop = np.interp(positions, dijkprofiel_y, dijkprofiel_x)
                        golfoploop = True
                    else: # in between --> then only golfklap
                        positions = np.arange(transition_level, valMHW, 0.1)
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
                    plt.savefig(figures_GEBU.joinpath(f'posities_dijkvak_{row.doorsnede}_{year}_T_{1/p}_transitionlevel_{transition_level}.png'))
                    plt.close()

                    maxSchadegetal_golfklap = 0.0
                    if golfklap:
                        ind = 0 # golfklap

                        for p in positions_golfklap:
                            bek = DIKErnelCalculations(tijdstippen, h_series[i,j,ind,:], Hs_series[i,j,ind,:], Tp_series[i,j,ind,:], betahoek_series[i,j,ind,:], dijkprofiel_x, dijkprofiel_y, p)
                            bek.gras_golfklap_input_JSON(typeZode, local_path)
                            maxSchadegetal_golfklap = np.max([maxSchadegetal_golfklap, bek.run_DIKErnel(binDIKErnel, output_path, local_path)])

                    maxSchadegetal_golfoploop = 0.0
                    if golfoploop:
                        ind = 1 # golfoploop

                        for p in positions_golfoploop:
                            bek = DIKErnelCalculations(tijdstippen, h_series[i,j,ind,:], Hs_series[i,j,ind,:], Tp_series[i,j,ind,:], betahoek_series[i,j,ind,:], dijkprofiel_x, dijkprofiel_y, p)
                            bek.gras_golfoploop_input_JSON(typeZode, local_path)
                            maxSchadegetal_golfoploop = np.max([maxSchadegetal_golfoploop, bek.run_DIKErnel(binDIKErnel, output_path, local_path)])

                    maxSchadegetal = np.max([maxSchadegetal_golfklap, maxSchadegetal_golfoploop, 10**(-4)])
                    SF = np.append(SF, 1/maxSchadegetal)

        SF = SF.reshape(len(evaluateYears), len(p_grid), len(transition_levels))

        # get relation between h_overgang and beta
        betaFalen = []
        years = []
        for i in range(0, len(evaluateYears)):
            for j in range(0, len(transition_levels)):

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

        betaFalen = betaFalen.reshape(len(evaluateYears), len(transition_levels))

        # export results to JSON
        for i, year in enumerate(evaluateYears):
            data = {"zichtjaar": year,
                    "dwarsprofiel": dwarsprofiel,
                    "dijkprofiel_x": list(dijkprofiel_x),
                    "dijkprofiel_y": list(dijkprofiel_y),
                    "grasbekleding_begin": list(transition_levels),
                    "betaFalen": list(betaFalen[i])}
            write_JSON_to_file(data, output_path.joinpath("GEBU_{}_{}.json".format(row.doorsnede, year)))

        # plot safety factor
        for i, year in enumerate(evaluateYears):
            for j, transition_level in enumerate(transition_levels):
                plt.figure()
                plt.semilogx(1/np.array(p_grid), SF[i,:,j], 'o--')
                plt.semilogx(1/np.array(p_grid), np.full_like(SF[i,:,j], 1.0), 'k')
                plt.grid()
                plt.xlabel('Terugkeertijd [jaar]')
                plt.ylabel('SF [-]')
                plt.title(f'Begin gras = {transition_levels[j]} m+NAP, eind gras = {grasbekleding_end} m+NAP')
                plt.savefig(figures_GEBU.joinpath('safetyFactor_{}_{}_overgang_{}.png'.format(row.doorsnede, year, transition_level)))
                plt.close()

        # plot beta
        plt.figure()
        for i, year in enumerate(evaluateYears):
            probFalen = norm.cdf(-betaFalen[i,:])
            plt.semilogy(transition_levels, probFalen, 'o--', label = f'year= {year}')
        plt.grid()
        plt.legend()
        plt.xlabel('h_overgang [m+NAP]')
        plt.ylabel('Faalkans [1/jaar]')
        plt.savefig(figures_GEBU.joinpath('betaFalen_{}.png'.format(row.doorsnede)))
        plt.close()

        # plot water levels
        # plt.figure()
        # for i in range(0, len(evaluateYears)):
        #     plt.semilogx(1.0/np.array(p_grid), valMHW[i,:], 'o--', label=str(evaluateYears[i]))
        # plt.legend()
        # plt.grid()
        # plt.xlabel('Terugkeertijd [jaar]')
        # plt.ylabel('Waterstand [m+NAP]')
        # plt.savefig(f'Figures_GEBU/waterstand_{index}.png')
        # plt.close()

        # plot time series
        for i, year in enumerate(evaluateYears):

            for j, p in enumerate(p_grid):

                for k, model in enumerate(models):

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
                    plt.savefig(figures_GEBU.joinpath('belasting_loc={}_{}_T={}_{}.png'.format(row.doorsnede, year, 1/p, model)))
                    plt.close()

if __name__ == '__main__':
    # inputs
    bekleding_path = Path(r'c:\VRM\test_revetments\Bekleding_default.csv')
    profielen_path = Path(r'c:\VRM\test_revetments\profielen')
    output_path = Path(r'c:\VRM\test_revetments\output')
    binDIKErnel = Path('c:/VRM/test_revetments/bin_DiKErnel')
    figures_GEBU = Path(r'c:\VRM\test_revetments\figures_GEBU')

    # read csv file as dataframe
    df = pd.read_csv(bekleding_path,
                     usecols=['vaknaam', 'dwarsprofiel', 'signaleringswaarde', 'ondergrens', 'faalkansbijdrage',
                              'lengte_effectfactor', 'locationid', 'hrdatabase_folder', 'hrdatabase', 'region', 'gws',
                              'getij_amplitude', 'steentoetsfile', 'prfl', 'begin_grasbekleding', 'qvar_p1', 'qvar_p2',
                              'qvar_p3', 'qvar_p4', 'qvar_stap'])
    df = df.dropna(subset=['vaknaam'])  # drop rows where vaknaam is Not a Number
    df = df.reset_index(drop=True)  # reset index

    # if figures_GEBU doesnot exist, create it
    if not figures_GEBU.exists():
        figures_GEBU.mkdir()
    # elif figures_GEBU exists, but not empty, stop the script
    elif figures_GEBU.exists() and len(list(figures_GEBU.iterdir())) != 0:
        print('The figure folder is not empty. Please empty the figures_GEBU folder and run the script again.')
        exit()

    revetment_gebu(df, profielen_path, output_path, binDIKErnel, figures_GEBU)
