import postprocessing.database_access_functions as db_access
import postprocessing.database_analytics as db_analytics
import copy
from vrtool.common.enums import MechanismEnum
import numpy as np
import pandas as pd
from vrtool.probabilistic_tools.probabilistic_functions import beta_to_pf, pf_to_beta

from vrtool.orm.models import *


class VRTOOLMeasuresObject:
    '''Object to get and store all relevant information on measures from a VRTOOL database. Not suitable for revetment yet TODO'''
    def __init__(self, db_path, LE_scenario, design_year = 50):
        self.db_path = db_path
        self.design_year = design_year
        self.LE = LE_scenario
        self.get_all_measures()

    # Define the function to get measures for all sections
    def get_measures_for_all_sections(self):
        # Fetch all MeasureResultMechanism records for the specified year
        measures_for_all_sections_beta = (MeasureResultMechanism
                                        .select(MeasureResultMechanism, MechanismPerSection, Mechanism.name)
                                        .join(MechanismPerSection, on=(MechanismPerSection.id == MeasureResultMechanism.mechanism_per_section_id))
                                        .join(Mechanism, on=(Mechanism.id == MechanismPerSection.mechanism_id))
                                        .where(MeasureResultMechanism.time == self.design_year))

        # Fetch all MeasureResultSection records for the specified year
        measures_for_all_sections_cost = (MeasureResultSection
                                        .select()
                                        .where(MeasureResultSection.time == self.design_year))
        
        measure_types_for_all_sections = (MeasureResult
                                        .select(MeasureResult, MeasurePerSection, Measure, MeasureType)
                                            .join(MeasurePerSection, on=(MeasurePerSection.id == MeasureResult.measure_per_section_id))
                                            .join(Measure, on=(Measure.id == MeasurePerSection.measure_id))
                                            .join(MeasureType, on=(MeasureType.id == Measure.measure_type_id)))

        # Convert the beta query results to a list of dictionaries
        beta_data_list = []
        for measure in measures_for_all_sections_beta:
            data = measure.__data__
            data['mechanism_name'] = measure.mechanism_per_section.mechanism.name
            data['section_id'] = measure.mechanism_per_section.section_id
            beta_data_list.append(data)
        
        measure_type_data_list = []
        for measure in measure_types_for_all_sections:
            data = measure.__data__
            data['measure_type_id'] = measure.measure_per_section.measure.measure_type.id
            measure_type_data_list.append(data)

        # Convert to Pandas DataFrame
        beta_df = pd.DataFrame(beta_data_list)
        beta_df.drop(columns=['id', 'mechanism_per_section'], inplace=True)
        beta_df = beta_df.pivot(index=['section_id','measure_result'], columns=['mechanism_name'], values='beta')
        #remove mechanism_name from the index
        beta_df.reset_index(inplace=True)
        beta_df.set_index('measure_result', inplace=True)
        
        # Convert the cost query results to a list of dictionaries
        cost_data_list = []
        for measure in measures_for_all_sections_cost:
            cost_data_list.append({'measure_result_id': measure.measure_result_id, 'cost': measure.cost})
        # Convert to Pandas DataFrame
        cost_df = pd.DataFrame(cost_data_list)
        cost_df.set_index('measure_result_id', inplace=True)
        
        #measure type list
        measure_type_data = pd.DataFrame(measure_type_data_list)[['id', 'measure_type_id']].rename(columns={'id':'measure_result'})
        measure_type_data.drop_duplicates(inplace=True)
        df = beta_df.join(measure_type_data.set_index('measure_result'))
        # Join the beta and cost DataFrames
        df = df.join(cost_df)
        self.measures_for_all_sections = df
    
    def add_combined_vzg_soil(self):
        #copy original dataframe
        df = self.measures_for_all_sections.copy()

        for section in df.section_id.unique():
            #we get all soil reinforcements (all measures with measure_type_id 1) and make a new df of it. Make sur it is a copy
            soil = df[(df.section_id == section) & (df.measure_type_id == 1)].copy()
            vzg = df[(df.section_id == section) & (df.measure_type_id == 3)].copy()
            soil.loc[:,'cost'] = np.add(soil.cost, vzg['cost'].values[0])

            beta_piping = soil.Piping
            new_beta_piping = pf_to_beta(beta_to_pf(beta_piping)/1000.)
            soil.loc[:,'Piping'] = new_beta_piping
            soil.loc[:,'measure_type_id'] = 99
            self.measures_for_all_sections = pd.concat([self.measures_for_all_sections, soil])

    def add_section_lengths(self):
        #get the section lengths from the database
        section_lengths = pd.DataFrame([(section.id, section.section_length) for section in SectionData.select()],columns= ['section_id', 'section_length'])
        section_lengths.set_index('section_id', inplace=True)
        #merge lengths to measures_df
        self.measures_for_all_sections = self.measures_for_all_sections.merge(section_lengths, left_on='section_id', right_index=True)

    def compute_cs_betas(self):
        self.measures_for_all_sections['Overflow_dsn'] = self.measures_for_all_sections['Overflow']
        if self.LE == 'full':
            self.full_LE_scenario()
        elif self.LE == 'no':
            self.measures_for_all_sections['Piping_dsn'] = self.measures_for_all_sections['Piping']
            self.measures_for_all_sections['StabilityInner_dsn'] = self.measures_for_all_sections['StabilityInner']
        else: #numerical value for LE with which we upscale
            self.N_LE_scenario(self.LE)

    def N_LE_scenario(self, N):
        N_piping = self.measures_for_all_sections['section_length'] / 300
        N_piping = N_piping.apply(lambda x: max(x, 1)) #minimum 1
        N_piping = N_piping.apply(lambda x: min(x, self.LE)) #maximum LE
        self.measures_for_all_sections['Piping_dsn'] = pf_to_beta(beta_to_pf(self.measures_for_all_sections['Piping']) / N_piping)
        
        N_stability = self.measures_for_all_sections['section_length'] / 50
        N_stability = N_stability.apply(lambda x: max(x, 1))
        N_stability = N_stability.apply(lambda x: min(x, self.LE)) #maximum LE
        self.measures_for_all_sections['StabilityInner_dsn'] = pf_to_beta(beta_to_pf(self.measures_for_all_sections['StabilityInner']) / N_stability)

    def full_LE_scenario(self):
        N_piping = self.measures_for_all_sections['section_length'] / 300
        N_piping = N_piping.apply(lambda x: max(x, 1))
        self.measures_for_all_sections['Piping_dsn'] = pf_to_beta(beta_to_pf(self.measures_for_all_sections['Piping']) / N_piping)
        N_stability = self.measures_for_all_sections['section_length'] / 50
        N_stability = N_stability.apply(lambda x: max(x, 1))
        self.measures_for_all_sections['StabilityInner_dsn'] = pf_to_beta(beta_to_pf(self.measures_for_all_sections['StabilityInner']) / N_stability)

    def get_all_measures(self):
        self.get_measures_for_all_sections()
        self.add_combined_vzg_soil()
        self.add_section_lengths()

        self.compute_cs_betas()

        
        pass