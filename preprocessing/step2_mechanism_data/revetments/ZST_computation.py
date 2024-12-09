from preprocessing.step2_mechanism_data.revetments.slope_part import SlopePart
from preprocessing.step2_mechanism_data.revetments.revetment_slope import RevetmentSlope

from preprocessing.step2_mechanism_data.revetments.project_utils.functions_integrate import issteen
from preprocessing.step2_mechanism_data.revetments.project_utils.DiKErnel import write_JSON_to_file, read_JSON
from pathlib import Path
from itertools import product
from scipy.interpolate import interp1d
import seaborn as sns

import numpy as np
import matplotlib.pyplot as plt
from vrtool.probabilistic_tools.probabilistic_functions import pf_to_beta, beta_to_pf

class ZSTComputation:
    def __init__(self, cross_section: RevetmentSlope, qvariant_path: Path, output_path: Path,
                 years_to_evaluate: list[int] = [2023, 2100], fb_zst: float = 0.05, N: int = 4, mode: str = 'uitbreiden', new_ratio: float = 4.5):
        self.cross_section = cross_section
        self.qvariant_path = qvariant_path
        self.output_path = output_path
        self.years_to_evaluate = years_to_evaluate
        self.fb_zst = fb_zst
        self.N = N
        self.mode = mode    #'uitbreiden' or 'vervangen'
        if self.mode == 'vervangen':
            self.new_ratio = new_ratio

    def add_qvariant_results(self, qvariant_path: Path):
        self.qvariant_results = read_JSON(qvariant_path.joinpath("Qvar_{}.json".format(self.cross_section.doorsnede)))


    def compute_zst(self, p_grid: list[float]):
        #CASE 1: no steentoets input. Assume full grass slope and write default values
        if not hasattr(self.cross_section, 'steentoetsfile'):
            self.case_no_steentoets()
            return

        #add the qvariant results to the object
        self.add_qvariant_results(self.qvariant_path)

        [self.evaluate_slope_part(slope_part_idx, p_grid) for slope_part_idx,slope_part in enumerate(self.cross_section.slope_parts)]

        self.postprocess_slope_parts()

        self.write_json_output()

        self.plot_slope_part_relations()

    def case_no_steentoets(self):
        #write default values
        for i, year in enumerate(self.years_to_evaluate):
            data = {"zichtjaar": year,
                    "dwarsprofiel": "Geen steenzetting",
                    "aantal deelvakken": 2,
                    "Zo": [self.cross_section.begin_grasbekleding-0.1, self.cross_section.begin_grasbekleding],
                    "Zb": [self.cross_section.begin_grasbekleding, self.cross_section.kruinhoogte],
                    "overgang huidig": [self.cross_section.begin_grasbekleding, self.cross_section.begin_grasbekleding],
                    "D huidig": [0.2, np.nan],
                    "tana": [1./3., 1./3.],
                    "toplaagtype": [27.1, 20.0],
                    "delta": [3., np.nan],
                    "ratio_voldoet": [8., np.nan]}
            data[f"deelvak 0"] = {"D_opt": [0.1, 0.2, 0.3, 0.4],
                                    "betaFalen": [8.0, 8.1, 8.2, 8.3]}
            data[f"deelvak 1"] = {"D_opt": [np.nan, np.nan, np.nan, np.nan],
                                    "betaFalen": [np.nan, np.nan, np.nan, np.nan]}
            write_JSON_to_file(data, self.output_path.joinpath("ZST_{}_{}.json".format(self.cross_section.doorsnede,
                                                                                    self.years_to_evaluate[i])))


    def evaluate_slope_part(self, slope_part_idx: int, p_grid: list[float]):
        #make grid of years and p_values
        combinations = list(product(self.years_to_evaluate, p_grid))
        #and for idx
        combination_idx = list(product(range(len(self.years_to_evaluate)), range(len(p_grid))))

        if self.cross_section.slope_parts[slope_part_idx].stone:
            #get D_sufficient for each combination
            D_sufficient = [self.get_D_sufficient(year_idx, p_idx, slope_part_idx) for year_idx, p_idx in combination_idx]
            #add as list of tuples to slope part with D_sufficient, year_idx and p_idx
            self.cross_section.slope_parts[slope_part_idx].add_block_revetment_relation(D_sufficient, combinations, self.fb_zst, self.N)
        else:
            #not stone, so no output
            pass

        

    def get_D_sufficient(self, year_idx: int, p_idx: int, slope_part_idx: int):

        #loads:
        Qvar_Hs = np.array(self.qvariant_results[f'Qvar {year_idx}_{p_idx}_zuilen']['Hs'])
        Qvar_h = np.array(self.qvariant_results[f'Qvar {year_idx}_{p_idx}_zuilen']['waterstand'])

        if (len(Qvar_Hs) == 1) and (Qvar_h > self.cross_section.slope_parts[slope_part_idx].Zo) and (Qvar_h < self.cross_section.slope_parts[slope_part_idx].Zb): #ensure there are 2 points such that it can be interpolated. Only if the load is on the slope part
            #load on the slope, but more points needed for interpolation
            Qvar_h = [Qvar_h[0]-0.25, Qvar_h[0], Qvar_h[0]+0.25]
            Qvar_Hs = [Qvar_Hs[0], Qvar_Hs[0], Qvar_Hs[0]]
            #interpolate to get relation between Hs and h
        elif len(Qvar_Hs) == 1:
            #no load on the slope part
            return 0.01
        elif len(Qvar_Hs) == 0:
            #no load for this probability
            return 0.01
        elif all(Qvar_h < self.cross_section.slope_parts[slope_part_idx].Zo):
            #load is below slope part
            return 0.01
        Qvar_relation = interp1d(Qvar_h, Qvar_Hs, kind='linear', fill_value=(0.0,0.0))

        #get h for relevant slope part range where there is load. We take 25 points in the range of the slope part and derive the relation between Hs and h
        if max(min(Qvar_h), self.cross_section.slope_parts[slope_part_idx].Zo) < min(max(Qvar_h), self.cross_section.slope_parts[slope_part_idx].Zb): # only if there is a range of h where there is load on the slope part
            h_range = np.linspace(max(min(Qvar_h), self.cross_section.slope_parts[slope_part_idx].Zo), min(max(Qvar_h), self.cross_section.slope_parts[slope_part_idx].Zb), 25)
            Hs_relation = Qvar_relation(h_range)
            #mode 1: extend current revetment
            if self.mode == 'uitbreiden':
                D_sufficient = max(Hs_relation/(self.cross_section.slope_parts[slope_part_idx].delta * self.cross_section.slope_parts[slope_part_idx].ratio_voldoet))
            elif self.mode == 'vervangen':
                #mode 2: standardized revetment with Hs/deltaD = new_ratio
                D_sufficient = max(Hs_relation/(self.new_ratio * self.cross_section.slope_parts[slope_part_idx].delta))

            return D_sufficient
        else:
            #loads available, but not on the slope part so the D_sufficient can be anything
            return 0.01 # or current?

       
    def postprocess_slope_parts(self):
        
        for slope_part in self.cross_section.slope_parts:
            if slope_part.stone:
                if not hasattr(slope_part, 'block_revetment_relation'):
                    raise ValueError("Block revetment relation not added for slope part. Use add_block_revetment_relation first.")
                

                #If the slope part is a stone slope part the current D should be in range of D_sufficient. If not, add it to the D_sufficient list
                #depending on the mode we pass D or D_effective
                if self.mode == 'vervangen':
                    slope_part.D_eff = slope_part.compute_effective_thickness(self.new_ratio)
                elif self.mode == 'uitbreiden':
                    slope_part.D_eff = slope_part.D
                slope_part.ensure_existing_thickness_in_relation()

                #For stone slope parts 2100 can not have a lower D_sufficient than 2023
                slope_part.ensure_future_D_sufficient_lower()

                #If we have equal D_sufficient in the same relation, we add a 0.01 increment such that values are increasing
                slope_part.ensure_D_sufficient_increases()

            else:
                print(slope_part.toplaagtype)


    def write_json_output(self):
        for year in self.years_to_evaluate:
            data = {"zichtjaar": year,
                    "dwarsprofiel": self.cross_section.dwarsprofiel,
                    "aantal deelvakken": len(self.cross_section.slope_parts),
                    "Zo": [slope_part.Zo for slope_part in self.cross_section.slope_parts],
                    "Zb": [slope_part.Zb for slope_part in self.cross_section.slope_parts],
                    "overgang huidig": [slope_part.overgang for slope_part in self.cross_section.slope_parts],
                    "D huidig": [slope_part.D for slope_part in self.cross_section.slope_parts],
                    "D effectief": [slope_part.D_eff for slope_part in self.cross_section.slope_parts],
                    "tana": [slope_part.tana for slope_part in self.cross_section.slope_parts],
                    "toplaagtype": [slope_part.toplaagtype for slope_part in self.cross_section.slope_parts],
                    "delta": [slope_part.delta for slope_part in self.cross_section.slope_parts],
                    "ratio_voldoet": [slope_part.ratio_voldoet for slope_part in self.cross_section.slope_parts]}
            #WRITE 27.1 for toplaagtype if issteen is true and self.mode = vervangen
            if self.mode == 'vervangen':
                data["toplaagtype"] = [27.1 if issteen(slope_part.toplaagtype) else slope_part.toplaagtype for slope_part in self.cross_section.slope_parts]
            else:
                steentypes = [slope_part.toplaagtype for slope_part in self.cross_section.slope_parts if issteen(slope_part.toplaagtype)]
                if not all(26.0 <= st <= 27.9 for st in steentypes):
                    raise ValueError(f"Toplaagtype steen is niet in de range van 26.0-27.9 voor dwarsprofiel {self.cross_section.dwarsprofiel}. Kies versterking_bekleding = 'vervangen'.")	
            for slope_part_idx, slope_part in enumerate(self.cross_section.slope_parts):
                if slope_part.stone:
                    data[f"deelvak {slope_part_idx}"] = {"D_opt": [D_sufficient for D_sufficient, _ in slope_part.block_revetment_relation[year]],
                                                        "betaFalen": [beta for _, beta in slope_part.block_revetment_relation[year]]}
            write_JSON_to_file(data, self.output_path.joinpath("ZST_{}_{}.json".format(self.cross_section.doorsnede, year)))
    
    def plot_slope_part_relations(self):
        # plot relation between beta and thickness
        colors = sns.color_palette("husl", len(self.cross_section.slope_parts))
        fig, ax = plt.subplots()
        linestyles = ['-', ':', '--', '-.']
        for j, slope_part in enumerate(self.cross_section.slope_parts):
            if slope_part.stone:
                for i, year in enumerate(self.years_to_evaluate):
                    D, beta = list(zip(*slope_part.block_revetment_relation[year]))
                    ax.plot(D, beta_to_pf(list(beta)), linestyle = linestyles[i], color = colors[j],marker= 'o',label = f'jaar {year} vlak {j}')
                    

        ax.grid()
        ax.legend(loc="center left")
        ax.set_xlabel('Toplaagdikte [m]')
        ax.set_ylabel('Faalkans [1/jaar]')
        ax.set_xlim(left=0.0)
        ax.set_yscale('log')
        plt.savefig(self.output_path.joinpath('figures_ZST','Dikte_vs_Faalkans_doorsnede={}.png'.format(self.cross_section.doorsnede)))
        plt.close()