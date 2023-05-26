import pandas as pd
from pathlib import Path
import sqlite3
import geopandas as gpd
import os
import numpy as np
from vrtool.orm.models import *
import warnings
from vrtool.probabilistic_tools.probabilistic_functions import beta_to_pf, pf_to_beta
from vrtool.failure_mechanisms.stability_inner.stability_inner_functions import calculate_reliability
def fill_diketrajectinfo_table(traject):
    traject_data = pd.read_csv(Path(os.getcwd()).parent.joinpath('preprocessing', 'generic_data', 'diketrajectinfo.csv'), index_col=0).loc[traject]

    DikeTrajectInfo.create(traject_name=traject, omega_piping=traject_data['omega_piping'],omega_stability_inner= traject_data['omega_stability_inner'],omega_overflow=traject_data['omega_overflow'],a_piping=traject_data['a_piping'],b_piping=traject_data['b_piping'],
                           a_stability_inner=traject_data['a_stability_inner'],b_stability_inner=traject_data['b_stability_inner'],
                           p_max=traject_data['p_max'],p_sig=traject_data['p_sig'], flood_damage=traject_data['flood_damage'],
                           N_overflow=traject_data['N_overflow'], N_blockrevetment=traject_data['N_blockrevetment'])

def fill_sectiondata_table(traject,shape_file,HR_input,geo_input):
    #merge HR_input['dijkhoogte'] with shape_file based on doorsnede and overslag
    shape_file = shape_file.merge(HR_input[['doorsnede','dijkhoogte']],left_on=['overslag'],right_on=['doorsnede'],how='left').drop(columns=['doorsnede'])
    #merge pleistoceendiepte and deklaagdiepte from geo_input with shape_file based on doorsnede
    shape_file = shape_file.merge(geo_input[['pleistoceendiepte','deklaagdikte']],left_on=['stabiliteit'],right_index=True,how='left')
    #replace nans in pleistoceendiepte and deklaagdikte with default
    shape_file['pleistoceendiepte'] = shape_file['pleistoceendiepte'].fillna(SectionData.pleistocene_level.default)
    shape_file['deklaagdikte'] = shape_file['deklaagdikte'].fillna(SectionData.cover_layer_thickness.default)
    #remove rows with same index
    shape_file = shape_file.loc[~shape_file.index.duplicated(keep='first')]
    #merge on index

    #get the id of traject from DikeTrajectInfo
    traject_id = DikeTrajectInfo.select(DikeTrajectInfo.id).where(DikeTrajectInfo.traject_name == traject).get().id
    for count, row in shape_file.iterrows():
        if row.in_analyse:
            SectionData.create(dike_traject_id=traject_id,section_name=row.vaknaam, meas_start=row.m_start,meas_end=row.m_eind,
                               in_analysis=row.in_analyse,section_length=np.abs(row.m_eind-row.m_start),crest_height=row.dijkhoogte,
                               annual_crest_decline=0.005)
def fill_buildings(buildings):
    ids = []
    for count, row in buildings.iterrows():
        try:
            vak_id = SectionData.select(SectionData.id).where(SectionData.section_name == row.NUMMER).get().id

            row_filtered = row.drop(index=['OBJECTID','NUMMER'])
            for distance, number in row_filtered.iteritems():
                Buildings.create(section_data = vak_id,distance_from_toe=distance,number_of_buildings = number)
        except:
            warnings.warn('Dijkvak {} niet in SectionData'.format(row.NUMMER))
    # TODO check if all sections in SectionData have buildings


def fill_waterleveldata(waterlevel_table,shape_file):
    #get section_names from SectionData
    section_names = [name['section_name'] for name in SectionData.select(SectionData.section_name).dicts()]

    for section_name in section_names:
        section_data_id = SectionData.select(SectionData.id).where(SectionData.section_name == section_name).get().id
        #get the WaterLevelLocationId from shape_file
        waterlevel_location_id = shape_file.loc[shape_file['vaknaam'] == section_name]['overslag'].values[0]
        #get all rows from waterlevel_table that have the same WaterLevelLocationId
        wl_table_data = waterlevel_table.loc[waterlevel_table['WaterLevelLocationId'] == waterlevel_location_id]
        for count, row in wl_table_data.iterrows():
            #TODO check how to write waterlevel_location_id, it now gives an integrity error
            WaterlevelData.create(section_data=section_data_id, water_level=row['WaterLevel'], beta=row['Beta'], year=row['Year'],
                                  waterlevel_location_id = 999)#, waterlevel_location_id=waterlevel_location_id)

def fill_profilepoints(profile_points,shape_file):
    #find unique values in CharacteristicPoint of profile_points
    unique_points = profile_points['CharacteristicPoint'].unique()
    id_dict = {k:v for k,v in zip(unique_points,range(1,len(unique_points)+1))}
    for count, row in profile_points.iterrows():
        section_data_id = SectionData.select(SectionData.id).where(SectionData.section_name == row['ProfileName']).get().id
        ProfilePoint.create(section_data=section_data_id,profile_point_type=id_dict[row['CharacteristicPoint']],
                            x_coordinate=row['x'],y_coordinate=row['z'])
    for id in id_dict.keys():
        CharacteristicPointType.create(id = id_dict[id],name = id)

def fill_mechanisms(shape_file, overflow_table=None,piping_table=None,stability_table=None, revetment_table = None, structures_table = None):
    default_mechanisms = ['Overflow','Piping','StabilityInner','Revetment','HydraulicStructures']
    header_names = ['overslag','piping','stabiliteit','bekledingen','kunstwerken']
    #add default_mechanisms to the Mechanisms table
    for mechanism in default_mechanisms:
        Mechanism.create(name=mechanism)
    #first fill the MechanismsPerSection table
    for count, row in shape_file.loc[shape_file.in_analyse==1].iterrows():
        section_data_id = SectionData.select(SectionData.id).where(SectionData.section_name == row['vaknaam']).get().id
        for count, header in enumerate(header_names):
            if isinstance(row[header],str):
                MechanismPerSection.create(section=section_data_id,mechanism=Mechanism.select(Mechanism.id).where(Mechanism.name == default_mechanisms[count]).get().id)
    #next fill ComputationScenario table and children for each mechanism
    #first fill the ComputationType table
    for computation_type in ['HRING','SEMIPROB','SIMPLE','DSTABILITY']:
        ComputationType.create(name=computation_type)
    if isinstance(overflow_table,pd.DataFrame):
        fill_overflow(overflow_table,shape_file=shape_file)

    if isinstance(stability_table,pd.DataFrame):
        fill_stability(stability_table,shape_file=shape_file)

    if isinstance(piping_table,pd.DataFrame):
        fill_piping(piping_table,shape_file=shape_file)

def fill_overflow(overflow_table,shape_file,computation_type = 'HRING'):
    #get id of Overflow from Mechanism table
    overflow_id = Mechanism.select(Mechanism.id).where(Mechanism.name == 'Overflow').get().id
    relevant_indices = [val for val in MechanismPerSection.select().where(MechanismPerSection.mechanism == overflow_id).dicts()]
    section_names = [SectionData.select().where(SectionData.id == row['id']).dicts() for row in relevant_indices]
    #loop over relevant_indices
    for count, row in enumerate(relevant_indices):
        #sscenario name should be equal to LocationId in overflow_table
        section_name = SectionData.select().where(SectionData.id == row['section']).get().section_name
        scenario_name = shape_file.loc[shape_file['vaknaam'] == section_name]['overslag'].values[0]
        computation_type = ComputationType.select().where(ComputationType.name == 'HRING').get().id
        ComputationScenario.create(mechanism_per_section=row['id'], mechanism=overflow_id,
                                   computation_name=scenario_name, scenario_name=scenario_name,
                                   scenario_probability=1.0, computation_type=computation_type,
                                   probability_of_failure=1.)
        #TODO: probability_of_failure should not be Required, but it is now.
        #TODO: scenario_name should not be Required, but it is now.

        #for overflow we fill MechanismTables
        #for each ComputationSceanrio for Overflow, fill the MechanismTable
        #find the ComputationName that belongs to row
        computation_name = ComputationScenario.select().where(ComputationScenario.mechanism_per_section == row['id']).get().computation_name
        computation_id = ComputationScenario.select().where(ComputationScenario.mechanism_per_section == row['id']).get().id
        for count, row in overflow_table.loc[computation_name].iterrows():
            #create a row in MechanismTable
            MechanismTable.create(computation_scenario=computation_id, year=row['Year'],value=row['CrestHeight'], beta=row['Beta'])


def fill_piping(piping_table,shape_file):
    piping_id = Mechanism.select(Mechanism.id).where(Mechanism.name == 'Piping').get().id
    relevant_indices = [val for val in MechanismPerSection.select().where(MechanismPerSection.mechanism == piping_id).dicts()]
    # iterrows over relevant_indices
    for count, row in enumerate(relevant_indices):
        section_name = SectionData.select().where(SectionData.id == row['section']).get().section_name
        cross_section = shape_file.loc[shape_file['vaknaam'] == section_name]['piping'].values[0]
        if isinstance(piping_table.loc[cross_section],pd.Series):
            add_computation_scenario(piping_table.loc[cross_section],row['id'],cross_section,piping_id)
        else:
            for scen_count, subset in piping_table.loc[cross_section].iterrows():
                add_computation_scenario(subset,row['id'],cross_section,piping_id)

def fill_stability(stability_table,shape_file):
    #get id of Stability from Mechanism table
    stability_id = Mechanism.select(Mechanism.id).where(Mechanism.name == 'StabilityInner').get().id
    relevant_indices = [val for val in MechanismPerSection.select().where(MechanismPerSection.mechanism == stability_id).dicts()]
    # iterrows over relevant_indices
    for count, row in enumerate(relevant_indices):
        section_name = SectionData.select().where(SectionData.id == row['section']).get().section_name
        cross_section = shape_file.loc[shape_file['vaknaam'] == section_name]['stabiliteit'].values[0]
        if isinstance(stability_table.loc[cross_section],pd.Series):
            add_computation_scenario(stability_table.loc[cross_section],row['id'],cross_section,stability_id)
        else:
            for scen_count, subset in stability_table.loc[cross_section].iterrows():
                add_computation_scenario(subset,row['id'], cross_section,stability_id)

def add_stability_scenario(data, mechanism_per_section_id, cross_section, mechanism_id, scenario_name):
    if isinstance(data['stixnaam'], str):
        computation_type = ComputationType.select().where(ComputationType.name == 'SIMPLE').get().id
    else:
        computation_type = ComputationType.select().where(ComputationType.name == 'SIMPLE').get().id
    ComputationScenario.create(mechanism_per_section=mechanism_per_section_id, mechanism=mechanism_id,
                               computation_name=cross_section, scenario_name=scenario_name,
                               scenario_probability=data['scenariokans'], computation_type=computation_type,
                               probability_of_failure=beta_to_pf(data['beta']))
    # for each computation_scenario fill Parameter. first get the last computation_scenario_id that matches mechanism_per_section_id


    computation_scenario_id = [val for val in ComputationScenario.select().where(
        ComputationScenario.mechanism_per_section == mechanism_per_section_id).dicts()][-1]['id']

    beta_value = data['beta']
    # if nan then get SF from data
    if np.isnan(beta_value):
        beta_value = calculate_reliability(data['SF'])
    Parameter.create(computation_scenario=computation_scenario_id,
                     parameter='beta', value=beta_value)
    if isinstance(data.stixnaam, str):
        SupportingFile.create(computation_scenario=computation_scenario_id, filename=data.stixnaam)

def add_piping_scenario(data, mechanism_per_section_id, cross_section, mechanism_id, scenario_name):
    computation_type = ComputationType.select().where(ComputationType.name == 'SEMIPROB').get().id
    ComputationScenario.create(mechanism_per_section=mechanism_per_section_id, mechanism=mechanism_id,
                                 computation_name=cross_section, scenario_name=scenario_name,
                                 scenario_probability=data['scenariokans'], computation_type=computation_type,
                                 probability_of_failure=data['pf_s'])
    # for each computation_scenario fill Parameter
    computation_scenario_id = [val for val in ComputationScenario.select().where(
        ComputationScenario.mechanism_per_section == mechanism_per_section_id).dicts()][-1]['id']
    parameters_to_add = ['wbn', 'polderpeil', 'd_wvp', 'd70', 'd_cover', 'h_exit', 'r_exit', 'l_voor', 'l_achter', 'k', 'gamma_sat', 'kwelscherm', 'dh_exit(t)']
    for parameter_name in parameters_to_add:
        Parameter.create(computation_scenario=computation_scenario_id,
                         parameter=parameter_name, value=data[parameter_name])

def add_computation_scenario(data, mechanism_per_section_id, cross_section, mechanism_id):
    if Mechanism.select().where(Mechanism.id == mechanism_id).get().name == 'StabilityInner':
        scenario_name = data['scenarionaam']
        add_stability_scenario(data, mechanism_per_section_id, cross_section, mechanism_id, scenario_name)
    elif Mechanism.select().where(Mechanism.id == mechanism_id).get().name == 'Piping':
        scenario_name = '{}_{}'.format(cross_section, data['scenario'])
        add_piping_scenario(data, mechanism_per_section_id, cross_section, mechanism_id, scenario_name)
    else:
        raise Exception('Unknown mechanism in ComputationScenario')

def fill_revetment():
    pass

def fill_structures():
    pass

def fill_measures(measure_table):

    #fill MeasureType
    MeasureType.create(name='Soil reinforcement')
    MeasureType.create(name='Soil reinforcement with stability screen')
    MeasureType.create(name='Stability Screen')
    MeasureType.create(name='Vertical Geotextile')
    MeasureType.create(name='Diaphragm Wall')
    #fill CombinableType
    CombinableType.create(name='full')
    CombinableType.create(name='combinable')
    CombinableType.create(name='partial')

    #fill StandardMeasure
    for idx, row in measure_table.iterrows():
        measure_type_id = MeasureType.select().where(MeasureType.name == row['Type']).get().id
        combinable_type_id = CombinableType.select().where(CombinableType.name == row['Class']).get().id
        Measure.create(name=idx, measure_type=measure_type_id, combinable_type=combinable_type_id,year = row['year'])
        measure_id = [val for val in Measure.select().dicts()][-1]['id']
        row = row.fillna(-999)
        StandardMeasure.create(measure=measure_id, max_inward_reinforcement=row['max_inward'],max_outward_reinforcement=row['max_outward'],direction=row['Direction'],
                               crest_step=.5,max_crest_increase=row['dcrest_max'],stability_screen=row['StabilityScreen'],
                               prob_of_solution_failure=row['P_solution'],failure_probability_with_solution=row['Pf_solution'],stability_screen_s_f_increase=row['dSF'])

    #all id from Measure
    measure_ids = [val['id'] for val in Measure.select().dicts()]
    section_ids = [val['id'] for val in SectionData.select().dicts()]
    for section_id in section_ids:
        for measure_id in measure_ids:
            MeasurePerSection.create(section=section_id, measure=measure_id)
