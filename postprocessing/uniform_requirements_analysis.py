import pandas as pd
from vrtool.orm.models import *
import itertools
from vrtool.probabilistic_tools.probabilistic_functions import beta_to_pf, pf_to_beta


class UniformRequirementsAnalysis:

    def __init(self, db_path, total_space= 1.0):
        '''Total space sets the omega for all considered mechanisms'''
        p_max = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).p_max
        p_max_space = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).p_max * total_space
        omega_piping = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).omega_piping
        omega_stability_inner = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).omega_stability_inner
        omega_overflow = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).omega_overflow
        a_piping = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).a_piping
        a_stability_inner = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).a_stability_inner
        b_stability_inner = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).b_stability_inner
        b_piping = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).b_piping
        traject_length = DikeTrajectInfo.get(DikeTrajectInfo.id == 1).traject_length
        #step 1: get base info for traject

    def make_N_based_grid(self):
        #step 2: make a grid
        #smaller grid
        N_omega = [2., 3., 4., 6., 8., 16., 32.]
        N_LE = [5., 10., 20., 40., 50.]

        N_overflow_grid = N_omega.copy()
        N_piping_grid = sorted(set([a*b for a,b in list(itertools.product(N_omega, N_LE))]))
        N_stability_inner_grid = sorted(set([a*b for a,b in list(itertools.product(N_omega, N_LE))]))

        #add existing values:
        N_overflow_grid = N_overflow_grid + [np.divide(1, omega_overflow)]
        N_piping_grid = N_piping_grid + [np.divide(1,omega_piping) * np.divide(a_piping * traject_length, b_piping )]
        N_stability_inner_grid = N_stability_inner_grid + [np.divide(1,omega_stability_inner) * np.divide(a_stability_inner * traject_length, b_stability_inner)]

        #make a beta_grid for all
        overflow_grid = pf_to_beta(np.divide(p_max, N_overflow_grid))
        piping_grid = pf_to_beta(np.divide(p_max, N_piping_grid))
        stability_inner_grid = pf_to_beta(np.divide(p_max, N_stability_inner_grid))
                                        
        # #make a grid for all 3 mechanisms. 
        target_beta_grid_all = itertools.product(overflow_grid, piping_grid, stability_inner_grid)

    def make_tuple_based_grid(self):
        #step 2: make a grid
        pass

    def analyze_grid(self):
        #step 3: analyze the grid
        pass