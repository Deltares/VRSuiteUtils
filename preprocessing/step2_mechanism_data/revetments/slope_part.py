from preprocessing.step2_mechanism_data.revetments.project_utils.functions_integrate import issteen
from vrtool.probabilistic_tools.probabilistic_functions import pf_to_beta, beta_to_pf
import numpy as np

class SlopePart:
    def __init__(self, steentoets_series, doorsnede):
        #put values in series as attributes
        self.__dict__ = steentoets_series.to_dict()
        #check if it is a stone slope part
        self.stone = self.check_steen()
        self.D_eff = np.nan

        self.doorsnede = doorsnede
    
    def check_steen(self):
        if issteen(self.toplaagtype):
            return True
        else:
            return False
        
    def add_block_revetment_relation(self, D_sufficient, year_probability, fb_zst, N):
        #add relation as dict[year] = [(D_sufficient, beta)]

        # Initialize the dictionary with empty lists for each year
        self.block_revetment_relation = {year: [] for year, _ in year_probability}

        # Append tuples to the lists
        for idx, (year, p) in enumerate(year_probability):
            self.block_revetment_relation[year].append((D_sufficient[idx], pf_to_beta(p * fb_zst / N)))

    def compute_effective_thickness(self, new_ratio):
        '''Computes the effective thickness of the block revetment based on the new ratio.'''

        #compute the new thickness
        return self.D * self.ratio_voldoet/new_ratio



    def ensure_existing_thickness_in_relation(self):
        '''Ensures that the existing block thickness is covered by the relationship that was derived by adding a point if necessary.'''
        
        for year, relation in self.block_revetment_relation.items():
            if all(D_sufficient < self.D_eff for  D_sufficient, _ in relation): 
                # thickness is higher than relation. So we add a point with a beta that is 0.1 higher than the highest
                _, betas =  zip(*relation)
                relation.append((self.D_eff, max(max(betas)+0.1, 8.0)))
                self.block_revetment_relation[year] = sorted(relation, key=lambda x: x[0])
            elif all(D_sufficient > self.D_eff for  D_sufficient, _ in relation): 
                # thickness is lower than relation. This means that the current revetment is unsafe. We add a point with a beta that corresponds to a failure probability of 1e-2
                relation.append((self.D_eff, beta_to_pf(1e-2)))
                self.block_revetment_relation[year] = sorted(relation, key=lambda x: x[0])
                print(f"Waarschuwing: bestaande steendikte ({self.D}) op doorsnede {self.doorsnede} is lager dan de minimale steendikte in de afgeleide relatie. Aangenomen wordt dat de faalkans van de huidige bekleding gelijk is aan 1/100.")    

    def ensure_future_D_sufficient_lower(self):
        '''Ensures that the D_sufficient values are decreasing for future.'''
        
        #we assume there are 2 years
        thickness, beta_current = list(zip(*self.block_revetment_relation[min(self.block_revetment_relation.keys())]))
        thickness, beta_future  = list(zip(*self.block_revetment_relation[max(self.block_revetment_relation.keys())]))

        beta_future = [beta_current[i] if beta_current[i] > beta_future[i] else beta_future[i] for i in range(len(beta_current))]
        self.block_revetment_relation[max(self.block_revetment_relation.keys())] = list(zip(thickness, beta_future))

    def ensure_D_sufficient_increases(self):
        '''Ensures that the D_sufficient values are increasing and not equal to each other.'''

        for year, relation in self.block_revetment_relation.items():
            #run over values and check if value is higher than previous. If not, use previous+ 0.01
            for idx in range(1, len(relation)):
                if relation[idx][0] <= relation[idx-1][0]:
                    relation[idx] = (relation[idx-1][0] + 0.01, relation[idx][1])
            self.block_revetment_relation[year] = relation