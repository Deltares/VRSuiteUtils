from preprocessing.step2_mechanism_data.revetments.revetment_slope import RevetmentSlope
from preprocessing.step2_mechanism_data.revetments.project_utils.belastingen import waterstandsverloop, Hs_verloop, Tp_verloop, betahoek_verloop
from preprocessing.step2_mechanism_data.revetments.project_utils.bisection import bisection

from preprocessing.step2_mechanism_data.revetments.project_utils.DiKErnel import DIKErnelCalculations, write_JSON_to_file, read_JSON, read_prfl
from pathlib import Path
from itertools import product
from scipy.interpolate import interp1d

import numpy as np
import matplotlib.pyplot as plt
from vrtool.probabilistic_tools.probabilistic_functions import pf_to_beta, beta_to_pf



class GEBUComputation:
    def __init__(self, cross_section: RevetmentSlope, qvariant_path: Path, output_path: Path, local_path: Path, binDIKErnel: Path,
                 years_to_evaluate: list[int] = [2023, 2100]):
        self.cross_section = cross_section
        self.years_to_evaluate = years_to_evaluate
        self.models = ['gras_golfklap', 'gras_golfoploop']
        self.zode_type = 'grasGeslotenZode'
        self.gebu_variation = 'upper_limit'
        self.qvariant_path = qvariant_path
        self.local_path = local_path
        self.output_path = output_path
        self.binDIKErnel = binDIKErnel

        self.transition_levels = np.arange(self.cross_section.begin_grasbekleding, self.cross_section.end_grasbekleding, 0.25)
        self.SF_results = dict()

    def add_qvariant_results(self, qvariant_path: Path):
        self.qvariant_results = read_JSON(qvariant_path.joinpath("Qvar_{}.json".format(self.cross_section.doorsnede)))

    
    def compute_gebu(self, p_grid: list[float]):
        #Add the qvariant results to the object
        self.add_qvariant_results(self.qvariant_path)

        #Case 1: begin grasbekleding is very close to the crest. We then assume 2 transition levels. At 1 cm below crest and 25 cm lower. Beta of 8 and 7.9 are assumed. This prevents extrapolation problems in the vrtool.
        if self.cross_section.begin_grasbekleding >= self.cross_section.end_grasbekleding - 0.25:
            self.GEBU_close_to_crest()

        #Case 2: no grass revetment present. Not sure if this is possible, but if so, we break
        elif len(self.transition_levels) == 0:
            #TODO: @Stephan te bespreken: is dit de case waarbij er alleen steen is? Moeten we dan een GrassRevetmentRelation maken of niet?
            print(f"Error: Geen overgangen gevonden voor dwarsprofiel {self.cross_section.dwarsprofiel}. Controleer de invoer")
            exit()
        
        #Case 3: regular case with grass revetment.
        else:
        
            #make a grid of years and p-values
            combinations = list(product(self.years_to_evaluate, p_grid))

            #make the same for the combination_index (TBD what to use)
            combination_idx = list(product(range(len(self.years_to_evaluate)), range(len(p_grid))))

            #for transition level in transition levels
            for i, transition_level in enumerate(self.transition_levels):
                #evaluate each combination of year and p-value
                SF_list = [self.GEBU_normal_case(year_idx, p_idx, transition_level, combinations[count]) for count, (year_idx, p_idx) in enumerate(combination_idx)]
                self.SF_results[transition_level] =  [(year, p, value) for (year, p), value in zip(combinations, SF_list)]

            #get relation between beta and SF
            self.get_beta_SF_relation()

            self.write_regular_results()

    
    def GEBU_close_to_crest(self):
        for i, year in enumerate(self.years_to_evaluate):
            data = {"zichtjaar": year,
                    "dwarsprofiel": self.cross_section.dwarsprofiel,
                    "dijkprofiel_x": list(self.cross_section.dijkprofiel_x),
                    "dijkprofiel_y": list(self.cross_section.dijkprofiel_y),
                    "grasbekleding_begin": [self.cross_section.end_grasbekleding-0.25, self.cross_section.kruinhoogte+.1],
                    "betaFalen": [7.9, 8.]}
            write_JSON_to_file(data, self.output_path.joinpath(f"GEBU_{self.cross_section.doorsnede}_{year}.json"))
        print(f'GEBU Case 1 voor dwarsprofiel {self.cross_section.dwarsprofiel}. Begin grasbekleding (={self.cross_section.begin_grasbekleding}) (bijna) gelijk aan de kruinhoogte'
                f' (={self.cross_section.kruinhoogte}). Faalkans verwaarloosbaar.')
    
    def GEBU_normal_case(self, year_idx, p_idx, transition_level, year_probability):
        year, probability = year_probability
        #get water level from Qvariant
        water_level = self.qvariant_results[f'MHW {year_idx}_{p_idx}']
        #if water_level >= transition_level we evaluate gras_golfklap, else gras_golfoploop
        if water_level >= transition_level:
            load_time_series = self.get_hydraulic_load_time_series(water_level,year_idx, p_idx, 'gras_golfklap')
            
            #plot the hydraulic load time series
            self.plot_hydraulic_load_time_series(load_time_series, water_level, year, probability, 'gras_golfklap')

            #derive the positions on the slope
            positions = self.get_positions_golfklap(transition_level, water_level)

            #make positions plot 
            #NOTE: Turned off as it produces a lot of useless figures.
            # self.plot_positions(positions, transition_level, water_level, year, probability, 'gras_golfklap')
            #run the computation
            SF = self.run_computation(load_time_series, positions, transition_level, 'gras_golfklap')


        else:
            load_time_series = self.get_hydraulic_load_time_series(water_level, year_idx, p_idx, 'gras_golfoploop')

            #plot the hydraulic load time series
            self.plot_hydraulic_load_time_series(load_time_series, water_level, year, probability, 'gras_golfoploop')

            #derive the positions on the slope
            positions = self.get_positions_golfoploop(transition_level, water_level)

            #make positions plot
            #NOTE: Turned off as it produces a lot of useless figures.
            # self.plot_positions(positions, transition_level, water_level, year, probability, 'gras_golfklap')

            #run the computation
            SF = self.run_computation(load_time_series, positions, transition_level, 'gras_golfoploop')
        
        return SF
        
    def plot_hydraulic_load_time_series(self, loads:dict[np.array], water_level: float, year: int, probability: float, model: str):
        fig, axs = plt.subplots(2, 2)
        
        tijd = loads['tijd']/3600.0

        axs[0, 0].plot(tijd, loads['waterstand'], '--o')
        axs[0, 0].set_title('Waterstand (boven), Tp (onder)', fontdict={'fontsize':8})
        axs[0, 0].grid()
        axs[0, 1].plot(tijd, loads['Hs'], '--o')
        axs[0, 1].set_title('Hs (boven), hoek (onder)', fontdict={'fontsize':8})
        axs[0, 1].grid()
        axs[1, 0].plot(tijd, loads['Tp'], '--o')
        axs[1, 0].grid()
        axs[1, 1].plot(tijd, loads['betahoek'], '--o')
        axs[1, 1].grid()
        for ax in axs.flatten():
            ax.set_xlim(left= min(tijd), right = max(tijd))
        plt.savefig(self.output_path.joinpath('figures_GEBU',f'belasting_loc={self.cross_section.doorsnede}_{year}_{int(1/probability)}_{model}.png'))
        plt.close()

    def get_hydraulic_load_time_series(self, water_level: float, year_idx: int, p_idx: int, model: str):
        '''Get the hydraulic load time series for a given water level, year, p-value and model'''

        #load the values from the qvariant results
        Qvar_data = {key: self.qvariant_results[f'Qvar {year_idx}_{p_idx}_{model}'][key] for key in ['waterstand', 'Hs', 'Tp', 'dir']}
        if len(Qvar_data['waterstand']) == 0:
            exit() #this is too rigourous, needs refinement as it should just skip this transition level

        #append the water level to waterstand and the last values for the others
        Qvar_data['waterstand'].append(water_level)
        [Qvar_data[key].append(Qvar_data[key][-1]) for key in ['Hs', 'Tp', 'dir']]

        #derive the time series
        tijd, h_hulp = waterstandsverloop(self.cross_section.region, self.cross_section.GWS, water_level, self.cross_section.Amp, Qvar_data['waterstand'])
        Hs_hulp = Hs_verloop(h_hulp, Qvar_data['waterstand'], Qvar_data['Hs'])
        Tp_hulp = Tp_verloop(h_hulp, Qvar_data['waterstand'], Qvar_data['Tp'])
        betahoek_hulp = betahoek_verloop(h_hulp, Qvar_data['waterstand'], Qvar_data['dir'], self.cross_section.orientation)

        return {'tijd': tijd, 'waterstand': h_hulp, 'Hs': Hs_hulp, 'Tp': Tp_hulp, 'betahoek': betahoek_hulp}

    def get_positions_golfklap(self, transition_level: float, water_level: float):
        '''Derive the positions on the slope for golfklap'''
        if transition_level > water_level:
            print(f"Error: overgangshoogte ({transition_level}) is hoger dan de waterstand ({water_level}) bij golfklap. Neem contact op met Deltares")
            exit()
        #y-coordinaat bereik is tussen overgang en einde gras/waterstand
        #derive the positions on the slope
        positions = np.arange(transition_level, min(self.cross_section.end_grasbekleding, water_level), 0.1)
        return np.interp(positions, self.cross_section.dijkprofiel_y, self.cross_section.dijkprofiel_x)
    
    def get_positions_golfoploop(self, transition_level: float, water_level: float):
        '''Derive the positions on the slope for golfoploop'''
        if transition_level < water_level:
            print(f"Error: overgangshoogte ({transition_level}) is lager dan de waterstand ({water_level}) bij golfoploop. Neem contact op met Deltares")
            exit()
        #y-coordinaat is hoogte overgang
        positions = np.array([transition_level])
        return np.interp(positions, self.cross_section.dijkprofiel_y, self.cross_section.dijkprofiel_x)
    
    def run_computation(self, load_time_series: dict, positions: np.array, transition_level: float, model: str):
        '''Run the computation for golfklap'''
        max_schade = 0
        #initialize the DIKErnelCalculations object
        for position in positions:
            dike_kernel = DIKErnelCalculations(load_time_series, self.cross_section.dijkprofiel_x, self.cross_section.dijkprofiel_y, position)
            if model == 'gras_golfklap':
                dike_kernel.gras_golfklap_input_JSON(self.zode_type, self.local_path)	
            elif model == 'gras_golfoploop':
                dike_kernel.gras_golfoploop_input_JSON(self.zode_type, self.local_path)        
            schadegetal = dike_kernel.run_DIKErnel(self.binDIKErnel, self.output_path, self.local_path, self.cross_section.region)
            max_schade = np.max([max_schade, schadegetal])
        if max_schade > 0:
            return 1./max_schade
        else:
            return 1e4

    def get_beta_SF_relation(self):
        #make a dictionary to store the results with self.years_to_evaluate as keys and lists as values
        results = {year: [] for year in self.years_to_evaluate}

        for transition_level in self.SF_results.keys():
            result = self.SF_results[transition_level]
            years, p_values, SF_values = zip(*result)
            #convert p_values to beta values
            beta_values = pf_to_beta(p_values)
            #get SF_values and p_values for each year in years
            for year in self.years_to_evaluate:
                SF_values_year = [SF_values[i] for i in range(len(years)) if years[i] == year]
                beta_values_year = [beta_values[i]for i in range(len(years)) if years[i] == year]
                #get the relation between beta and SF and find point where SF = 1
                f = interp1d(beta_values_year, np.subtract(SF_values_year,1.0), fill_value=('extrapolate'))
                if f(0.0) < 0.0 and f(10.0) < 0.0:
                    beta = 0.0 #all values unsafe
                elif f(0.0) > 0.0 and f(10.0) > 0.0:
                    beta = np.max(beta_values_year) #all values safe, take highest
                else:   #find intersection
                    #TODO check wat hier mis gaat met 31-1
                    beta = bisection(f, 0.0, 10.0, 1e-2)    #NOTE: this can lead to lower betas for more safe situations due to the extrapolation. Inconsequential for results as it will only happen for P < min(p_grid)
                results[year].append((transition_level, beta))
                self.plot_SF_probability(beta_values_year, SF_values_year, transition_level, year, beta)

        self.beta_SF = results

        self.postprocess_beta_SF()

        self.plot_beta_SF()

    def plot_beta_SF(self):
        fig, ax = plt.subplots()
        linestyles = ['--', ':']
        for count, year in enumerate(self.years_to_evaluate):
            transitions, betas = zip(*self.beta_SF[year])
            ax.plot(transitions, betas, linestyle = linestyles[count], marker = 'o', label = f'year= {year}')
        ax.grid()
        ax.legend()
        ax.set_xlabel('h_overgang [m+NAP]')
        ax.set_ylabel('Beta [-]')
        ax.set_title(f'Relatie tussen beta en overgangshoogte voor dwarsprofiel {self.cross_section.dwarsprofiel}')
        plt.savefig(self.output_path.joinpath('figures_GEBU','betaFalen_loc={}.png'.format(self.cross_section.doorsnede)))
        plt.close()

    def plot_SF_probability(self, beta_values_year, SF_values_year, transition_level, year, beta):
        fig, ax = plt.subplots()
        min_beta = min([np.min(beta_values_year), beta])
        max_beta = max([np.max(beta_values_year), beta])
        #add beta, 1 to beta_values_year, SF_values_year and ensure they are sorted on beta_values_year to avoid confusing plots
        beta_values_year = np.append(beta_values_year, beta)
        SF_values_year = np.append(SF_values_year, 1.0)
        beta_values_year, SF_values_year = zip(*sorted(zip(beta_values_year, SF_values_year)))
        ax.plot(beta_to_pf(list(beta_values_year)), list(SF_values_year), 'bo--')
        ax.plot(beta_to_pf(beta), 1.0, 'ro')
        #horizontal line at 1.0
        ax.plot(np.array([beta_to_pf(min_beta), beta_to_pf(max_beta)/10]), [1.0, 1.0], 'k:')
        ax.grid()
        ax.set_xscale('log')
        if max(SF_values_year) > 10.0:
            ax.set_yscale('log')
        ax.set_xlabel('P_f [-]')
        ax.set_ylabel('SF [-]')
        ax.set_ylim(bottom=0.1)
        ax.set_xlim(left = beta_to_pf(max_beta)/10, right = beta_to_pf(min_beta))
        ax.set_title(f'Begin gras = {transition_level:.2f} m+NAP, eind gras = {self.cross_section.end_grasbekleding:.2f} m+NAP')
        plt.savefig(self.output_path.joinpath('figures_GEBU','safetyFactor_loc={}_{}_overgang_{:.2f}.png'.format(self.cross_section.doorsnede, year, transition_level)))
        plt.close()

    def postprocess_beta_SF(self):
        transitions, beta_current  = map(list, zip(*self.beta_SF[min(self.years_to_evaluate)]))
        transitions, beta_future = map(list, zip(*self.beta_SF[max(self.years_to_evaluate)]))
        #STEP 1: values for increasing transition levels may not be lower than for lower transition levels
        for i in range(1, len(beta_current)):
            if beta_current[i] < beta_current[i-1]:
                beta_current[i] = beta_current[i-1]
        for i in range(1, len(beta_future)):
            if beta_future[i] < beta_future[i-1]:
                beta_future[i] = beta_future[i-1]

        #STEP 2: future situation may not be better than current situation. We assume that years_to_evaluate has length 2.

        #check if beta_current is larger than beta_future. If so, set beta_future equal to beta_current
        beta_future = [beta_current[i] if beta_current[i] > beta_future[i] else beta_future[i] for i in range(len(beta_current))]

        #STEP 3: Deal with the upper limit 
        # It can happen that within the "regular" measure space for GEBU no sufficient beta can be achieved. This is
        # strange, because when the transition level is increased until the crest, GEBU cannot occur. Therefore, we
        # include alternative calculation methods, which can only be set from the sandbox, not CLI. These methods are:
        #   1. Regular calculation: possibly leading to insufficient betas
        #   2. Upper limit approach: when transition level is at crest level (or actually 1 cm below crest level), the
        #      beta is set to 8.0.
        #   3. Lower limit approach: For each transition level, the beta is set to 8.0. This way, GEBU will not play anyt
        #      role in the vrtool optimization.
        # gebu_alternative = "regular", "upper_limit", "lower_limit"
        if self.gebu_variation == "upper_limit":
            if np.max(transitions) >= self.cross_section.kruinhoogte - 0.01: #change data for existing point close to crest
                beta_current[-1] = 8.0
                beta_future[-1] = 8.0
            else: #add new point close to crest
                transitions = np.append(transitions, np.round(self.cross_section.kruinhoogte - 0.01,3))
                beta_current = np.append(beta_current, 8.0)
                beta_future = np.append(beta_future, 8.0)
        elif self.gebu_variation == "lower_limit":
            #change all beta to 8.0
            beta_current = np.array([8.0 for _ in beta_current])
            beta_future = np.array([8.0 for _ in beta_future])
        elif self.gebu_variation == "regular":
            pass
        else:
            print("Error: gebu_variation not recognized. Choose from 'upper_limit', 'lower_limit', 'regular'")
            exit()

        #store the results
        self.beta_SF[min(self.years_to_evaluate)] = list(zip(transitions, beta_current))
        self.beta_SF[max(self.years_to_evaluate)] = list(zip(transitions, beta_future))

    def write_regular_results(self):
        # export results to JSON
        for i, year in enumerate(self.years_to_evaluate):
            transitions, betas = zip(*self.beta_SF[year])
            data = {"zichtjaar": year,
                    "dwarsprofiel": self.cross_section.dwarsprofiel,
                    "dijkprofiel_x": list(self.cross_section.dijkprofiel_x),
                    "dijkprofiel_y": list(self.cross_section.dijkprofiel_y),
                    "grasbekleding_begin": transitions,
                    "betaFalen": betas}
            write_JSON_to_file(data, self.output_path.joinpath("GEBU_{}_{}.json".format(self.cross_section.doorsnede, year)))
        
    def plot_positions(self, positions, transition_level, water_level, year, probability, model:str):
        fig, ax = plt.subplots()
        ax.plot(self.cross_section.dijkprofiel_x, self.cross_section.dijkprofiel_y,'g')
        if model == 'gras_golfklap':
            ax.plot(positions, np.interp(positions, self.cross_section.dijkprofiel_x, self.cross_section.dijkprofiel_y),'ro')
        elif model == 'gras_golfoploop':
            ax.plot(positions, np.interp(positions, self.cross_section.dijkprofiel_x, self.cross_section.dijkprofiel_y),'bo')
        ax.plot(self.cross_section.dijkprofiel_x, np.full_like(self.cross_section.dijkprofiel_x, water_level),'b--')
        ax.grid()
        ax.set_xlabel('Horizontale richting dijk x [m]')
        ax.set_ylabel('Verticale richting dijk z [m+NAP]')
        plt.savefig(self.output_path.joinpath('figures_GEBU',
                                              f'posities_dijkvak_{self.cross_section.doorsnede}_{year}_T_{int(1/probability)}_transitionlevel_{transition_level}.png'))
        plt.close()


