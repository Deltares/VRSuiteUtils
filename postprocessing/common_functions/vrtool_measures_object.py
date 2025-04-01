import postprocessing.common_functions.database_access_functions as db_access
import postprocessing.common_functions.database_analytics as db_analytics
import copy
from vrtool.common.enums import MechanismEnum
from vrtool.orm.orm_controllers import open_database

import numpy as np
import pandas as pd
from vrtool.probabilistic_tools.probabilistic_functions import beta_to_pf, pf_to_beta
from pathlib import Path

from vrtool.orm.models import *


class VRTOOLMeasuresObject:
    db_path: Path
    design_year: int
    LE: int
    measures_for_all_sections: pd.DataFrame

    
    '''Object to get and store all relevant information on measures from a VRTOOL database. Not tested for revetment yet TODO'''
    def __init__(self, db_path, LE_scenario, design_year = 50) -> None:
        self.db_path = db_path

        self.design_year = design_year
        if LE_scenario == 'full':
            self.LE = 999
        elif LE_scenario == 'no':
            self.LE = -999
        else:
            self.LE = LE_scenario
        with open_database(db_path).connection_context():
            self.get_all_measures()

    # Define the function to get measures for all sections
    def get_measures_for_all_sections(self) -> None:
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
    
    def add_combined_vzg_soil(self) -> None:
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

    def add_section_lengths(self) -> None:
        #get the section lengths from the database
        section_lengths = pd.DataFrame([(section.id, section.section_length) for section in SectionData.select()],columns= ['section_id', 'section_length'])
        section_lengths.set_index('section_id', inplace=True)
        #merge lengths to measures_df
        self.measures_for_all_sections = self.measures_for_all_sections.merge(section_lengths, left_on='section_id', right_index=True)

    def compute_cs_betas(self) -> None:
        self.measures_for_all_sections['Overflow_dsn'] = self.measures_for_all_sections['Overflow']
        if self.LE == 999:
            self.full_LE_scenario()
        elif self.LE == -999:
            self.measures_for_all_sections['Piping_dsn'] = self.measures_for_all_sections['Piping']
            self.measures_for_all_sections['StabilityInner_dsn'] = self.measures_for_all_sections['StabilityInner']
        else: #numerical value for LE with which we upscale
            self.N_LE_scenario(self.LE)

    def N_LE_scenario(self, N) -> None:
        N_piping = self.measures_for_all_sections['section_length'] / 300
        N_piping = N_piping.apply(lambda x: max(x, 1)) #minimum 1
        N_piping = N_piping.apply(lambda x: min(x, self.LE)) #maximum LE
        self.measures_for_all_sections['Piping_dsn'] = pf_to_beta(beta_to_pf(self.measures_for_all_sections['Piping']) / N_piping)
        
        N_stability = self.measures_for_all_sections['section_length'] / 50
        N_stability = N_stability.apply(lambda x: max(x, 1))
        N_stability = N_stability.apply(lambda x: min(x, self.LE)) #maximum LE
        self.measures_for_all_sections['StabilityInner_dsn'] = pf_to_beta(beta_to_pf(self.measures_for_all_sections['StabilityInner']) / N_stability)

    def full_LE_scenario(self) -> None:
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

    def add_width_crest(self) -> None:
        #get berm width and crest heightening if applicable and add to the measures_for_all_sections dataframe
        #get the measure_type_id.id for which measure_type_id.name in MeasureType contains Soil reinforcement

        _soil_types = [entry.id for entry in MeasureType.select().where(MeasureType.name.contains('Soil reinforcement'))]
        _soil_measure_result_ids = self.measures_for_all_sections.loc[self.measures_for_all_sections.measure_type_id.isin(_soil_types)].index
        #for all _soil_measure_result_ids, get the MeasureResultParameter where measure_result_id is in _soil_measure_result_ids.
        _mrp_selection = MeasureResultParameter.select().where(MeasureResultParameter.measure_result_id.in_(_soil_measure_result_ids.values.tolist()))
        _soil_dimensions =[(_mrp.measure_result_id, _mrp.name, _mrp.value) for _mrp in _mrp_selection]
        _soil_dimensions_df = pd.DataFrame(_soil_dimensions, columns=['measure_result_id', 'type', 'value'])
        _soil_dimensions_df = _soil_dimensions_df.pivot(index='measure_result_id', columns='type', values='value')

        #merge to self.measures_for_all_sections
        self.measures_for_all_sections = self.measures_for_all_sections.merge(_soil_dimensions_df, left_on='measure_result', right_index=True, how='left')

