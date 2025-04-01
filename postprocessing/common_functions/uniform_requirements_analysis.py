import pandas as pd
from vrtool.orm.models import *
import itertools
from vrtool.probabilistic_tools.probabilistic_functions import beta_to_pf, pf_to_beta
from vrtool.common.enums import MechanismEnum
from postprocessing.common_functions.database_access_functions import * 
from postprocessing.common_functions.vrtool_optimization_object import VRTOOLOptimizationObject
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from postprocessing.common_functions.Deltares_colors import Deltares_colors 

sns.set(style="whitegrid")
colors =  Deltares_colors().sns_palette("DeltaresFull")


class UniformRequirementsAnalysis:
    p_max: float
    p_max_space: float
    omega_piping: float
    omega_stability_inner: float
    omega_overflow: float
    omega_revetment: float
    a_piping: float
    a_stability_inner: float
    b_stability_inner: float
    b_piping: float
    traject_length: float
    measures: pd.DataFrame
    year: int
    target_beta_grid_all: list[tuple[float]]
    specific_target_beta_grid: dict[MechanismEnum, list[float]]
    cost_grid_Nbased: list[float]
    pf_traject_Nbased: list[float]
    cost_grid_specific: list[float]
    pf_traject_specific: list[float]   
    factsheet: pd.DataFrame
    measures_Nbased_optimal: pd.DataFrame


    def __init__(self, measures: pd.DataFrame, total_space: float = 1.0) -> None:
        '''Total space sets the omega for all considered mechanisms'''
        
        self.p_max = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).p_max
        self.p_max_space = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).p_max * total_space
        self.omega_piping = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).omega_piping
        self.omega_stability_inner = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).omega_stability_inner
        self.omega_overflow = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).omega_overflow
        # self.omega_revetment = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).omega_revetment
        self.omega_revetment = 0.10
        self.a_piping = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).a_piping
        self.a_stability_inner = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).a_stability_inner
        self.b_stability_inner = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).b_stability_inner
        self.b_piping = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).b_piping
        self.traject_length = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).traject_length
        
        self.measures = measures.measures_for_all_sections
        self.year = measures.design_year

    def plot_results(self, vrm_run: VRTOOLOptimizationObject, save_dir: Path, dsn_run: VRTOOLOptimizationObject = False, LE = False) -> None:
        fig,ax = plt.subplots()

        #plot the main grid if it exists
        if hasattr(self, 'cost_grid_Nbased'):
            ax.scatter(self.cost_grid_Nbased, self.pf_traject_Nbased, color = colors[4], marker = '.', label = 'Combinaties van eisen')
        if hasattr(self, 'cost_grid_specific'):
            ax.scatter(self.cost_grid_specific, self.pf_traject_specific, color = colors[6], marker = '.', label = 'Bandbreedte o.b.v. OI2014')

        # plot dsn results if they exist
        if dsn_run:
            #plot the DSN run
            ax.scatter(dsn_run.costs[dsn_run.step], dsn_run.traject_probs[self.year][dsn_run.step], color = colors[6], marker = 'o', s=40, linestyle = '', label = 'Default doorsnede-eisen')

        
        #plot the VRM run path
        if hasattr(vrm_run, 'costs_filtered'):
            #plot the VRM run if filtered results exist
            ax.plot(vrm_run.costs_filtered, vrm_run.traject_probs_filtered[self.year], color = colors[0], marker = '.',label = 'Veiligheidsrendement')
        else:
            ax.plot(vrm_run.costs, vrm_run.traject_probs[self.year], color = colors[0], marker = '.', label = 'Veiligheidsrendement')

        #highlight the economic optimum
        ax.scatter(vrm_run.optimization_steps[vrm_run.step]['total_lcc'], vrm_run.traject_probs[self.year][vrm_run.step], color = colors[2], marker = 'o', s = 20, label = 'Optimum Veiligheidsrendement',zorder= 1000)
        
        #highlight where the requirement is met
        ind_req_met = min(np.where(np.array(vrm_run.traject_probs[self.year])<self.p_max_space)[0])
        # ax.scatter(vrm_run.optimization_steps[ind_req_met]['total_lcc'], vrm_run.traject_probs[self.year][ind_req_met], marker = 's', s= 30, color = colors[2], label=f'VRM < eis {2025+self.year}')


        ax.set_xlim(left = 0, right = max(self.cost_grid_Nbased))
        ax.hlines(self.p_max_space, 0, 5e8, colors='k', linestyles='dashed', label='Faalkanseis')
        ax.set_ylim(top=self.p_max *10,  bottom = self.p_max/10)
        ax.set_xlabel('Kosten (M€)')
        ax.set_ylabel(f'Trajectfaalkans in {2025+self.year}')
        ax.set_yscale('log')
        ax.legend(bbox_to_anchor=(1.05, 1))
        #get xtick labels and divide by 1e6 and replace
        ax.set_xticklabels([f'{x/1e6:.0f}' for x in ax.get_xticks()]);
        ax.grid(True, which='both', linestyle=':')



        if LE== 'full':
            plt.savefig(save_dir.joinpath(f'{DikeTrajectInfo.get(DikeTrajectInfo.id == 1).traject_name}_jaar={self.year+2025}_LE.png'), dpi=300, bbox_inches='tight')
        elif LE == 'no':
            plt.savefig(save_dir.joinpath(f'{DikeTrajectInfo.get(DikeTrajectInfo.id == 1).traject_name}_jaar={self.year+2025}.png'), dpi=300, bbox_inches='tight')
        elif LE == 4:
            plt.savefig(save_dir.joinpath(f'{DikeTrajectInfo.get(DikeTrajectInfo.id == 1).traject_name}_jaar={self.year+2025}_N=4.png'), dpi=300, bbox_inches='tight')
        else:
            plt.savefig(save_dir.joinpath(f'{DikeTrajectInfo.get(DikeTrajectInfo.id == 1).traject_name}_jaar={self.year+2025}_{vrm_run.db_path.stem}.png'), dpi=300, bbox_inches='tight')
     


    def make_Nbased_grid(self, N_omega: list[float], N_LE: list[float], revetment: bool = False) -> None:

        N_overflow_grid = N_omega.copy()
        N_overflow_grid = N_overflow_grid + [np.divide(1, self.omega_overflow)]
        overflow_grid = pf_to_beta(np.divide(self.p_max, N_overflow_grid))
        
        N_piping_grid = sorted(set([a*b for a,b in list(itertools.product(N_omega, N_LE))]))
        N_piping_grid = N_piping_grid + [np.divide(1,self.omega_piping) * np.divide(self.a_piping * self.traject_length, self.b_piping )]
        piping_grid = pf_to_beta(np.divide(self.p_max, N_piping_grid))

        #add existing values:
        N_stability_inner_grid = sorted(set([a*b for a,b in list(itertools.product(N_omega, N_LE))]))
        N_stability_inner_grid = N_stability_inner_grid + [np.divide(1,self.omega_stability_inner) * np.divide(self.a_stability_inner * self.traject_length, self.b_stability_inner)]
        stability_inner_grid = pf_to_beta(np.divide(self.p_max, N_stability_inner_grid))

        if revetment:
            N_revetment_grid = N_omega.copy()
            N_revetment_grid = N_revetment_grid + [np.divide(1, self.omega_revetment)]
            revetment_grid = pf_to_beta(np.divide(self.p_max, N_revetment_grid))  
        #make a beta_grid for all
                                        
        # #make a grid for all mechanisms. 
        if revetment:
            target_beta_grid_all = itertools.product(overflow_grid, piping_grid, stability_inner_grid, revetment_grid)
        else:
            target_beta_grid_all = itertools.product(overflow_grid, piping_grid, stability_inner_grid)

        self.target_beta_grid_all = list(target_beta_grid_all)
        

    
    def make_dict_based_grid(self, omega_grids: dict[MechanismEnum, list[float]], LE_grid: dict[MechanismEnum, list[float]] = False) -> None:
        #step 2: make a grid based on a dict with emchanisms as keys and values in lists
        #omega_grid contains lists of values expressed as N, should be same length
        #check length of .values in N_omega_dict
        if len(set([len(values) for values in omega_grids.values()])) != 1:
            raise ValueError('Lists of values in omega_grids should have the same length')
        
        if LE_grid: #now we have more than 1 LE parameterization
            if len(set([len(values) for values in LE_grid.values()])) != 1:
                raise ValueError('Lists of values in N_LE_dict should have the same length')
            LE_grid[MechanismEnum.OVERFLOW] = [1] * (len(list(LE_grid.values())[0])+1)
            LE_grid[MechanismEnum.REVETMENT] = [1] * (len(list(LE_grid.values())[0])+1)  
        
            LE_grid[MechanismEnum.PIPING] = [self.a_piping * self.traject_length / self.b_piping] + [a_traject * self.traject_length / self.b_piping for a_traject in list(LE_grid[MechanismEnum.PIPING])]
            LE_grid[MechanismEnum.STABILITY_INNER] = [self.a_stability_inner * self.traject_length / self.b_stability_inner] + [a_traject * self.traject_length / self.b_stability_inner for a_traject in list(LE_grid[MechanismEnum.STABILITY_INNER])]
        else:
            LE_grid = {MechanismEnum.OVERFLOW: [1], MechanismEnum.REVETMENT: [1], MechanismEnum.PIPING: [self.a_piping * self.traject_length / self.b_piping], MechanismEnum.STABILITY_INNER: [self.a_stability_inner * self.traject_length / self.b_stability_inner]}

        N_specific_grids = {mechanism: list(itertools.product(omega_grids[mechanism], LE_grid[mechanism])) for mechanism in omega_grids.keys()}
        #for each value in the list of values in specific grids we compute the product of the tuple
        N_specific_grids = {mechanism: [a*b for a,b in values] for mechanism, values in N_specific_grids.items()}

        #make a beta_grid for all
        self.specific_target_beta_grid = {mechanism: pf_to_beta(np.divide(self.p_max, N_specific_grids[mechanism])) for mechanism in omega_grids.keys()}
        
        #N_LE_dict contains a_traject values for piping, stability. Is optional and will be added to the default values.

    
    @staticmethod
    def compute_traject_probability(minimal_cost_dataset: pd.DataFrame) -> float:
        #no upscaling in sections. 
        pf_overflow = max(beta_to_pf(minimal_cost_dataset['Overflow']))
        p_nonf_piping = np.product(np.subtract(1,beta_to_pf(minimal_cost_dataset['Piping'])))
        p_nonf_stability = np.product(np.subtract(1,beta_to_pf(minimal_cost_dataset['StabilityInner'])))
        pf_traject = 1- (1-pf_overflow)*(p_nonf_piping)*(p_nonf_stability)
        return pf_traject

    @staticmethod
    def calculate_cost(overflow_beta: float, piping_beta: float, stability_beta: float, measures_df: pd.DataFrame, revetment_beta: float = None) -> tuple[float, float, pd.DataFrame]:
        #calculate the cost for the given beta values

        #get all sections
        sections = measures_df['section_id'].unique()

        if revetment_beta == None:
            possible_measures = measures_df.loc[(measures_df['Overflow_dsn'] >= overflow_beta) & 
                            (measures_df['Piping_dsn'] >= piping_beta) & 
                                (measures_df['StabilityInner_dsn'] >= stability_beta)]
        else:
            possible_measures = measures_df.loc[(measures_df['Overflow_dsn'] >= overflow_beta) & 
                            (measures_df['Piping_dsn'] >= piping_beta) & 
                                (measures_df['StabilityInner_dsn'] >= stability_beta) &
                                    (measures_df['Revetment_dsn'] >= revetment_beta)]
        #get the minimal cost for each section_id and the betas that belong to that measure
        minimal_costs_idx = possible_measures.reset_index().groupby('section_id')['cost'].idxmin()
        minimal_costs_data = possible_measures.reset_index().loc[minimal_costs_idx]

        computed_traject_probability = UniformRequirementsAnalysis.compute_traject_probability(minimal_costs_data)

        minimal_costs = minimal_costs_data['cost']
        #check if all sections are in the minimal_costs, if any of them is not in there return 1e99, else return the sum of the costs
        if len(sections) != len(minimal_costs):
            return 1e99, computed_traject_probability, minimal_costs_data
        else:
            return minimal_costs.sum(), computed_traject_probability, minimal_costs_data
    
    def analyze_Nbased_grid(self) -> None:
        cost_grid = []
        pf_traject = []

        if len(self.target_beta_grid_all[0]) == 3:  #no revetment
            for count, (overflow_beta, piping_beta, stability_beta) in enumerate(self.target_beta_grid_all):
                cost_i, pf_traject_i, measures_per_section_for_step =  self.calculate_cost(overflow_beta, piping_beta, stability_beta, self.measures)
                if cost_i < 1.e99:
                    cost_grid.append(cost_i)
                    pf_traject.append(pf_traject_i)
                else:
                    print('No measures found for combination: ', overflow_beta, piping_beta, stability_beta)

        elif len(self.target_beta_grid_all[0]) == 4: # with revetment
            for count, (overflow_beta, piping_beta, stability_beta, revetment_beta) in enumerate(self.target_beta_grid_all):
                cost_i, pf_traject_i, measures_per_section_for_step = self.calculate_cost(overflow_beta, piping_beta, stability_beta, self.measures, revetment_beta)
                if cost_i < 1.e99:
                    cost_grid.append(cost_i)
                    pf_traject.append(pf_traject_i)
                else:
                    print('No measures found for combination: ', overflow_beta, piping_beta, stability_beta, revetment_beta)

        self.cost_grid_Nbased = cost_grid
        self.pf_traject_Nbased = pf_traject 
        #get the index of the optimum
        self.get_optimal_from_Nbased_grid()

    def get_optimal_from_Nbased_grid(self) -> None:
        #get the optimal cost from the Nbased grid where p_max_space is met
        self.N_grid_min_idx = np.where(np.array(self.pf_traject_Nbased)<self.p_max_space)[0][np.argmin(np.array(self.cost_grid_Nbased)[np.where(np.array(self.pf_traject_Nbased)<self.p_max_space)])]
        #get the measures for this combination
        if len(self.target_beta_grid_all[0]) == 3:  #no revetment
            self.measures_Nbased_optimal = self.calculate_cost(self.target_beta_grid_all[self.N_grid_min_idx][0], self.target_beta_grid_all[self.N_grid_min_idx][1], self.target_beta_grid_all[self.N_grid_min_idx][2], self.measures)[2]
        elif len(self.target_beta_grid_all[0]) == 4: # with revetment
            self.measures_Nbased_optimal = self.calculate_cost(self.target_beta_grid_all[self.N_grid_min_idx][0], self.target_beta_grid_all[self.N_grid_min_idx][1], self.target_beta_grid_all[self.N_grid_min_idx][2], self.measures, self.target_beta_grid_all[self.N_grid_min_idx][3])[2]


    def analyze_specific_grid(self) -> None:
        cost_specific = []
        pf_traject_specific = []
        measures_specific = []

        #get length of grid
        for i in range(0, len(list(self.specific_target_beta_grid.values())[0])):
            if MechanismEnum.REVETMENT in self.specific_target_beta_grid.keys():
                cost_i, pf_traject_i, measures_i = self.calculate_cost(self.specific_target_beta_grid[MechanismEnum.OVERFLOW][i], 
                                                                       self.specific_target_beta_grid[MechanismEnum.PIPING][i],
                                                                       self.specific_target_beta_grid[MechanismEnum.STABILITY_INNER][i],
                                                                       self.measures, 
                                                                       self.specific_target_beta_grid[MechanismEnum.REVETMENT][i])
            else:
                cost_i, pf_traject_i, measures_i = self.calculate_cost(self.specific_target_beta_grid[MechanismEnum.OVERFLOW][i],
                                                                          self.specific_target_beta_grid[MechanismEnum.PIPING][i],
                                                                            self.specific_target_beta_grid[MechanismEnum.STABILITY_INNER][i],
                                                                            self.measures)            
            if cost_i < 1.e99:
                cost_specific.append(cost_i)
                pf_traject_specific.append(pf_traject_i)
                measures_specific.append(measures_i)

            else:
                if MechanismEnum.REVETMENT in self.specific_target_beta_grid.keys():
                    print('No measures found for combination: ', self.specific_target_beta_grid[MechanismEnum.OVERFLOW][i],
                                                                       self.specific_target_beta_grid[MechanismEnum.PIPING][i],
                                                                       self.specific_target_beta_grid[MechanismEnum.STABILITY_INNER][i],
                                                                       self.specific_target_beta_grid[MechanismEnum.REVETMENT][i])
                else:
                    print('No measures found for combination: ', self.specific_target_beta_grid[MechanismEnum.OVERFLOW][i],
                                                                       self.specific_target_beta_grid[MechanismEnum.PIPING][i],
                                                                       self.specific_target_beta_grid[MechanismEnum.STABILITY_INNER][i])
        self.cost_grid_specific = cost_specific
        self.pf_traject_specific = pf_traject_specific
        self.measures_specific = measures_specific

    def generate_factsheet(self, vrm_run: VRTOOLOptimizationObject) -> None:
        '''Generates a factsheet for uniform optimal requirements in comparison to a VRM computation'''
        if len(self.target_beta_grid_all[0]) == 3: #no revetment
            table_df = pd.DataFrame(self.target_beta_grid_all, columns = ['Overflow', 'Piping', 'StabilityInner'])
        elif len(self.target_beta_grid_all[0]) == 4: #with revetment
            table_df = pd.DataFrame(self.target_beta_grid_all, columns = ['Overflow', 'Piping', 'StabilityInner', 'Revetment'])
        
        #convert betas to N-values
        table_df = table_df.apply(lambda x: np.divide(self.p_max, beta_to_pf(x)))
        table_df['cost'] = self.cost_grid_Nbased
        table_df['pf_traject'] = self.pf_traject_Nbased

        minimal_cost_for_uniform = min(np.array(self.cost_grid_Nbased)[np.where(np.array(self.pf_traject_Nbased) < self.p_max_space)[0]])
        vrm_cost_for_standard = vrm_run.costs
        vrm_pf = vrm_run.traject_probs[self.year]
        vrm_cost_for_standard = vrm_cost_for_standard[np.where(np.array(vrm_pf) < self.p_max_space)[0][0]]

        table_df['Unsafe design'] = table_df['pf_traject'] > self.p_max_space
        table_df['% cost difference vs VRM'] = table_df['cost'].apply(lambda x: (x-vrm_cost_for_standard)/vrm_cost_for_standard)*100
        table_df['% cost difference vs Uniform'] = table_df['cost'].apply(lambda x: (x-minimal_cost_for_uniform)/minimal_cost_for_uniform)*100
        self.factsheet = table_df

    @staticmethod
    def get_measure_parameters(measures_df: pd.DataFrame, db_path: Path) -> pd.DataFrame:
        parameters = []
        #nsure measure_result column is of dtype int
        measures_df['measure_result'] = measures_df['measure_result'].astype(int)
        for row in measures_df.itertuples():
            row_params = get_measure_parameters(row.measure_result, db_path)
            measure_df_subset = measures_df.loc[measures_df.measure_result == row.measure_result]
            if type(measure_df_subset) == pd.Series:
                row_params['cost'] = measure_df_subset.cost
            else:
                row_params['cost'] = measure_df_subset.loc[np.round(measure_df_subset.Piping,2) == np.round(row.Piping,2)].cost.values[0]
            # row_params.update(get_measure_costs(row.measure_result, db_path))
            row_params.update(get_measure_type(row.measure_result, db_path))
            if row.measure_type_id == 99:
                row_params['name'] = 'Verticaal Zanddicht Geotextiel + Grondversterking binnenwaarts'
            row_params['section_id'] = row.section_id
            parameters.append(row_params)
        parameters_df = pd.DataFrame(parameters)
        parameters_df = parameters_df[['section_id', 'name', 'cost', 'dcrest', 'dberm', 'l_stab_screen']]
        return parameters_df