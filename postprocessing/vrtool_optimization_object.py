import postprocessing.database_access_functions as db_access
import postprocessing.database_analytics as db_analytics
import copy
from vrtool.common.enums import MechanismEnum
from vrtool.probabilistic_tools.probabilistic_functions import beta_to_pf, pf_to_beta
from collections import defaultdict

import numpy as np

class VRTOOLOptimizationObject:
    '''Object to get and store all relevant information from an optimization run in the VRTOOL database'''
    def __init__(self, db_path, run_id, step = None):
        self.run_id = run_id
        self.db_path = db_path
        # self.db_path = str(db_path)
        self.optimization_type = [run['optimization_type'] for run in db_access.get_overview_of_runs(self.db_path) if run['id'] == self.run_id][0]
        self.step = step
    
    def get_all_optimization_results(self):
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

    def get_optimization_results(self):
        self.optimization_steps = db_access.get_optimization_steps_for_run_id(self.db_path, self.run_id)

        self.costs = [step['total_lcc'] for step in self.optimization_steps]


    def get_minimal_tc_step(self):
        self.step = db_analytics.get_minimal_tc_step(self.optimization_steps)-1

    def get_measures_for_run(self):
        self.lists_of_measures = db_access.get_measures_for_run_id(self.db_path, self.run_id)

    def get_measures_per_step(self):
        self.measures_per_step = db_analytics.get_measures_per_step_number(self.lists_of_measures)

    def get_stepwise_assessment(self):
        has_revetment = False
        
        #has_revetment = db_access.has_revetment(self.db_path)
        self.assessment_results = {}
        for mechanism in [MechanismEnum.OVERFLOW, MechanismEnum.PIPING, MechanismEnum.STABILITY_INNER, MechanismEnum.REVETMENT]:
            if has_revetment or mechanism != MechanismEnum.REVETMENT:
                self.assessment_results[mechanism] = db_access.import_original_assessment(self.db_path, mechanism)

        self.reliability_per_step = db_analytics.get_reliability_for_each_step(self.db_path, self.measures_per_step)
        
        self.stepwise_assessment = db_analytics.assessment_for_each_step(copy.deepcopy(self.assessment_results), self.reliability_per_step)

    def get_traject_probability_per_mechanism(self):
        self.traject_probability_per_mechanism = db_analytics.calculate_traject_probability_for_steps(self.stepwise_assessment)
    
    def get_overall_traject_probability(self):
        def calculate_traject_probability(traject_prob):
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

    def get_forward_vr_order(self):
        forward_vr_order = [step['section_id'][0] for id, step in self.measures_per_step.items()]
        #take first of unique values, keep order
        forward_vr_order = [x for i, x in enumerate(forward_vr_order) if forward_vr_order.index(x) == i]      

    def postprocess_optimization_steps(self, BC_threshold = 0.8, year = 2075):
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



