import postprocessing.common_functions.database_access_functions as db_access
import postprocessing.common_functions.database_analytics as db_analytics
import postprocessing.common_functions.generate_output as output_functions
import copy
from vrtool.common.enums import MechanismEnum
from vrtool.probabilistic_tools.probabilistic_functions import beta_to_pf, pf_to_beta
from pathlib import Path


from collections import defaultdict
import pandas as pd
import numpy as np

class VRTOOLOptimizationObject:
    '''Object to get and store all relevant information from an optimization run in the VRTOOL database'''
    
    run_id: int
    db_path: Path
    optimization_type: int
    step: int
    optimization_steps: list[dict]
    costs: list[float]
    lists_of_measures: list[dict]
    measures_per_step: list[dict]
    stepwise_assessment: list[dict]
    traject_probability_per_mechanism: list[dict]
    traject_probs: dict
    assessment_results: dict
    reliability_per_step: list[float]
    traject_probability_per_mechanism: list[dict]
    traject_probs: dict
    forward_vr_order: list[int]
    traject_probs_filtered: dict
    costs_filtered: np.array
    requirement_step: int
    requirement_year: int
    requirements: pd.DataFrame
    measures_df: pd.DataFrame
    
    
    def __init__(self, db_path: Path, run_id: int, step: int = None) -> None:
        self.run_id = run_id
        self.db_path = db_path
        self.optimization_type = [run['optimization_type'] for run in db_access.get_overview_of_runs(self.db_path) if run['id'] == self.run_id][0]
        self.step = step
    
    def get_all_optimization_results(self) -> None:
        self.get_optimization_results()
        if self.step == None:
            if self.optimization_type ==1: #VRM
                self.get_minimal_tc_step()
            else:   #DSN
                #get last step
                self.step = len(self.optimization_steps)-1

        self.get_measures_for_run()
        self.get_measures_per_step()
        self.get_stepwise_assessment()
        self.get_traject_probability_per_mechanism()
        self.get_overall_traject_probability()

    def get_optimization_results(self) -> None:
        self.optimization_steps = db_access.get_optimization_steps_for_run_id(self.db_path, self.run_id)

        self.costs = [step['total_lcc'] for step in self.optimization_steps]


    def get_minimal_tc_step(self) -> None:
        self.step = db_analytics.get_minimal_tc_step(self.optimization_steps)-1

    def get_measures_for_run(self) -> None:
        self.lists_of_measures = db_access.get_measures_for_run_id(self.db_path, self.run_id)

    def get_measures_per_step(self) -> None:
        self.measures_per_step = db_analytics.get_measures_per_step_number(self.lists_of_measures)

    def get_stepwise_assessment(self) -> None:
        has_revetment = False
        
        #has_revetment = db_access.has_revetment(self.db_path)
        self.assessment_results = {}
        for mechanism in [MechanismEnum.OVERFLOW, MechanismEnum.PIPING, MechanismEnum.STABILITY_INNER, MechanismEnum.REVETMENT]:
            if has_revetment or mechanism != MechanismEnum.REVETMENT:
                self.assessment_results[mechanism] = db_access.import_original_assessment(self.db_path, mechanism)

        self.reliability_per_step = db_analytics.get_reliability_for_each_step(self.db_path, self.measures_per_step)
        
        self.stepwise_assessment = db_analytics.assessment_for_each_step(copy.deepcopy(self.assessment_results), self.reliability_per_step)

    def get_traject_probability_per_mechanism(self) -> None:
        self.traject_probability_per_mechanism = db_analytics.calculate_traject_probability_for_steps(self.stepwise_assessment)
    
    def get_overall_traject_probability(self) -> None:
        def calculate_traject_probability(traject_prob: dict[MechanismEnum:dict[int:float]]) -> tuple[list[int], list[float]]:
            p_nonf = [1] * len(list(traject_prob.values())[0].values())
            for mechanism, data in traject_prob.items():
                time, pf = zip(*sorted(data.items()))
                
                p_nonf = np.multiply(p_nonf, np.subtract(1,pf))
            return time, list(1-p_nonf)
        
        traject_probs = [calculate_traject_probability(traject_probability_step) for traject_probability_step in self.traject_probability_per_mechanism]

        self.traject_probs = defaultdict(list)
        for times, pfs in traject_probs:
            for time, pf in zip(times, pfs):
                self.traject_probs[time].append(pf)

    def get_forward_vr_order(self) -> None:
        forward_vr_order = [step['section_id'][0] for id, step in self.measures_per_step.items()]
        #take first of unique values, keep order
        forward_vr_order = [x for i, x in enumerate(forward_vr_order) if forward_vr_order.index(x) == i]      

    def postprocess_optimization_steps(self, BC_threshold: float = 0.8, year: int = 2075) -> None:
        year_int = year-2025

        risk_decrease_per_step = np.abs(np.diff([self.optimization_steps[i]['total_risk'] for i in range(len(self.traject_probs[0]))]))
        cost_increase_per_step = np.diff([self.optimization_steps[i]['total_lcc'] for i in range(len(self.traject_probs[0]))])
        #remove bundling steps (risk is identical)
        #remove all with BC<0.8
        BC_ratio = risk_decrease_per_step/cost_increase_per_step
        low_bc_idx = np.where(BC_ratio < BC_threshold)[0] + 1

        cost_vrm = [self.optimization_steps[i]['total_lcc'] for i in range(len(self.traject_probs[0]))]
        self.traject_probs_filtered = {key: np.delete(value, low_bc_idx) for key, value in self.traject_probs.items()}
        self.costs_filtered = np.delete(cost_vrm, low_bc_idx)

    def set_step_data(self, step: str = 'Economic optimum', year: int = 2075,  pf_req: float = None) -> None:
        '''Set what type of step to use for exporting data on requirements and measures.
        Two types of settings are possible: taking the 'Economic optimum' or the 'Standard in year'. For the latter a pf_req needs to be provided.'''
        if step == 'Standard in year' and pf_req == None:
            raise ValueError('pf_req should be provided when step is Standard in year')
        
        if step == 'Economic optimum':
            self.requirement_step = self.step
            self.requirement_year = year
        elif step == 'Standard in year':
            self.requirement_step = min(np.where(np.array(self.traject_probs[year-2025])<pf_req)[0])
            self.requirement_year = year


    def requirements_from_vrm(self) -> None:
        '''Get the requirements for the VRM based on the optimization results. Returns a requirement for each mechanism per section based on the optimization results.
        Two types of settings are possible: taking the 'Economic optimum' or the 'Standard in year'. For the latter a pf_req needs to be provided.'''
        def get_probability_for_mechanism_in_year_per_section(assessment_step: dict[int:dict[str:list]], year:int, mechanism: MechanismEnum) -> dict[str:float]:
            probability_per_section = {}
            time_index = np.argwhere(np.array(assessment_step[mechanism][1]['time'])==year).flatten()[0]
            for section in assessment_step[mechanism]:
                probability_per_section[section] = assessment_step[mechanism][section]['beta'][time_index]
            return probability_per_section

        all_mechanism_keys = [list(step.keys()) for step in self.stepwise_assessment]
        #flatten and make a set
        all_mechanism_keys = set([item for sublist in all_mechanism_keys for item in sublist])
        requirements_per_section = {mechanism: get_probability_for_mechanism_in_year_per_section(assessment_step=self.stepwise_assessment[self.requirement_step],
                                                                                          year=self.requirement_year - 2025, 
                                                                                          mechanism=mechanism) 
                                                                                          for mechanism in all_mechanism_keys}
        
        self.requirements = pd.DataFrame.from_dict(requirements_per_section)

    def measures_from_vrm(self) -> None:
        '''Get the measures from the VRM for the requirement_step and requirement_year as stored in the object'''
        measures_per_section  = db_analytics.get_measures_per_section_for_step(self.measures_per_step, self.requirement_step+1)
        section_parameters = {}

        for section in measures_per_section.keys():
            section_parameters[section] = []
            for measure in measures_per_section[section][0]:
                parameters = db_access.get_measure_parameters(measure, self.db_path)
                parameters.update(db_access.get_measure_costs(measure, self.db_path))
                parameters.update(db_access.get_measure_type(measure, self.db_path))
                section_parameters[section].append(parameters)
        
        self.measures_df = output_functions.measure_per_section_to_df(measures_per_section, section_parameters)

    