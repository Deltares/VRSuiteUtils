import os
import sqlite3
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from vrtool.failure_mechanisms.stability_inner.stability_inner_functions import (
    calculate_reliability,
)
from vrtool.orm.models import *
from vrtool.probabilistic_tools.probabilistic_functions import beta_to_pf, pf_to_beta
from preprocessing import generic_data

def fill_diketrajectinfo_table(traject,length):
    traject_data = pd.read_csv(
        generic_data.joinpath("diketrajectinfo.csv"),
        index_col=0,
    ).loc[traject]
    if any(traject_data.isna()):
        raise Exception('Traject data in preprocessing/generic_data/diketrajectinfo.csv is niet compleet voor traject {}'.format(traject))
    DikeTrajectInfo.create(
        traject_name=traject,
        omega_piping=0.24,
        omega_stability_inner=0.04,
        omega_overflow=0.24,
        a_piping=traject_data["a_piping"],
        b_piping=300.,
        a_stability_inner=0.033,
        b_stability_inner=50.,
        p_max=traject_data["p_max"],
        p_sig=traject_data["p_sig"],
        flood_damage=traject_data["flood_damage"],  #Economische schade jaar 2050 uit factsheets
        n_overflow=traject_data["N_overflow"],
        n_revetment=3.,
        traject_length = length
    )


def fill_sectiondata_table(traject:str, shape_file: gpd.GeoDataFrame):

    # replace nans in pleistoceendiepte and deklaagdikte with default
    shape_file["pleistoceendiepte"] = shape_file["pleistoceendiepte"].fillna(
        SectionData.pleistocene_level.default
    )
    shape_file["deklaagdikte"] = shape_file["deklaagdikte"].fillna(
        SectionData.cover_layer_thickness.default
    )
    # replace nans in a_piping and a_stabiliteit with 1.0 so that upscaling is done for the entire section. We don't use the default of 0.0 here. First check if the column exists. If a_piping doesn't exist but a_stabiliteit does we don't detect it, but this should never be the case.
    #check if a_piping and a_stabiliteit are in the shape_file.columns
    if "a_piping" not in shape_file.columns and "a_stabiliteit" not in shape_file.columns:
        shape_file["a_piping"] = 1.0
        shape_file["a_stabiliteit"] = 1.0
    elif ("a_piping" in shape_file.columns) != ("a_stabiliteit" in shape_file.columns):
        # Only one of the columns is present
        raise ValueError("Both 'a_piping' and 'a_stabiliteit' must be present or absent together.")
    else:
        shape_file["a_piping"] = shape_file["a_piping"].fillna(
            1.0
        )
        shape_file["a_stabiliteit"] = shape_file["a_stabiliteit"].fillna(
            1.0
        )

    
    # remove rows with same index
    shape_file = shape_file.loc[~shape_file.index.duplicated(keep="first")]
    # remove rows with same vaknaam
    shape_file = shape_file.loc[~shape_file.vaknaam.duplicated(keep="first")]

    # merge on index

    # get the id of traject from DikeTrajectInfo
    traject_id = (
        DikeTrajectInfo.select(DikeTrajectInfo.id)
        .where(DikeTrajectInfo.traject_name == traject)
        .get()
        .id
    )
    for count, row in shape_file.iterrows():
        if row.in_analyse:
            SectionData.create(
                dike_traject_id=traject_id,
                section_name=row.vaknaam,
                meas_start=row.m_start,
                meas_end=row.m_eind,
                in_analysis=row.in_analyse,
                section_length=np.abs(row.m_eind - row.m_start),
                crest_height=row.dijkhoogte,
                annual_crest_decline=row.kruindaling,
                pleistocene_level=row.pleistoceendiepte,
                cover_layer_thickness=row.deklaagdikte,
                sensitive_fraction_piping=row.a_piping,
                sensitive_fraction_stability_inner=row.a_stabiliteit,

            )


def fill_buildings(buildings):
    ids = []
    for vaknaam, row in buildings.iterrows():
        try:
            vak_id = (
                SectionData.select(SectionData.id)
                .where(SectionData.section_name == vaknaam)
                .get()
                .id
            )

            for distance, number in row.items():
                Buildings.create(
                    section_data=vak_id,
                    distance_from_toe=distance,
                    number_of_buildings=number,
                )
        except:
            pass
            # warnings.warn("Dijkvak {} niet in SectionData".format(vaknaam))
    # TODO add check if all sections in SectionData have buildings


def fill_waterleveldata(waterlevel_table, shape_file):
    # get section_names from SectionData
    section_names = [
        name["section_name"]
        for name in SectionData.select(SectionData.section_name).dicts()
    ]

    for section_name in section_names:
        section_data_id = (
            SectionData.select(SectionData.id)
            .where(SectionData.section_name == section_name)
            .get()
            .id
        )
        # get the WaterLevelLocationId from shape_file
        waterlevel_location_id = shape_file.loc[shape_file["vaknaam"] == section_name][
            "overslag"
        ].values[0]
        # get all rows from waterlevel_table that have the same WaterLevelLocationId
        wl_table_data = waterlevel_table.loc[
            waterlevel_table["WaterLevelLocationId"] == waterlevel_location_id
        ]
        for count, row in wl_table_data.iterrows():
            # TODO check how to write waterlevel_location_id, it now gives an integrity error
            WaterlevelData.create(
                section_data=section_data_id,
                water_level=row["WaterLevel"],
                beta=row["Beta"],
                year=row["Year"],
                waterlevel_location_id=999,
            )  # , waterlevel_location_id=waterlevel_location_id)

def fill_profiles(profile_df):
    unique_points = profile_df.columns.get_level_values(0).unique().tolist()
    id_dict = {k: v for k, v in zip(unique_points, range(1, len(unique_points) + 1))}

    #Generate the CharacteristicPointType table
    for id in id_dict.keys():
        CharacteristicPointType.create(id=id_dict[id], name=id)

    #Add points for each section
    for section_name, row in profile_df.iterrows():
        try:
            section_data_id = (
                SectionData.select(SectionData.id)
                .where(SectionData.section_name == section_name)
                .get()
                .id
            )
            for pointtype in id_dict.keys():
                if not any(row[pointtype].isna()):
                    ProfilePoint.create(
                        section_data=section_data_id,
                        profile_point_type=id_dict[pointtype],
                        x_coordinate=row[pointtype]['X'],
                        y_coordinate=row[pointtype]['Z'],
                    )
                else:
                    pass
                    # warnings.warn("Skipped {} for section {}".format(pointtype,section_name))
        except:
            pass
            # warnings.warn("Dijkvak {} niet in vakindeling. Profiel wordt niet weggeschreven.".format(section_name))


def fill_profilepoints(profile_points, shape_file):
    # find unique values in CharacteristicPoint of profile_points
    unique_points = profile_points["CharacteristicPoint"].unique()
    id_dict = {k: v for k, v in zip(unique_points, range(1, len(unique_points) + 1))}
    for count, row in profile_points.iterrows():
        try:
            section_data_id = (
                SectionData.select(SectionData.id)
                .where(SectionData.section_name == row["vaknaam"])
                .get()
                .id
            )
            ProfilePoint.create(
                section_data=section_data_id,
                profile_point_type=id_dict[row["CharacteristicPoint"]],
                x_coordinate=row["x"],
                y_coordinate=row["z"],
            )
        except:
            warnings.warn("Dijkvak {} niet in SectionData".format(row.vaknaam))
    for id in id_dict.keys():
        CharacteristicPointType.create(id=id_dict[id], name=id)


def fill_mechanisms(mechanism_data,
    shape_file,
):
    default_mechanisms = [
        "Overflow",
        "Piping",
        "StabilityInner",
        "Revetment",
        "HydraulicStructures",
    ]
    header_names = ["overslag", "piping", "stabiliteit", "bekledingen", "kunstwerken"]
    # add default_mechanisms to the Mechanisms table
    for mechanism in default_mechanisms:
        Mechanism.create(name=mechanism)
    # first fill the MechanismsPerSection table
    for count, row in shape_file.loc[shape_file.in_analyse == 1].iterrows():
        section_data_id = (
            SectionData.select(SectionData.id)
            .where(SectionData.section_name == row["vaknaam"])
            .get()
            .id
        )
        for counter, header in enumerate(header_names):
            #check if header exists in row index
            if header in row.index:
                if row[header] is not None:
                    MechanismPerSection.create(
                        section=section_data_id,
                        mechanism=Mechanism.select(Mechanism.id)
                        .where(Mechanism.name == default_mechanisms[counter])
                        .get()
                        .id,
                    )
    # next fill ComputationScenario table and children for each mechanism
    # first fill the ComputationType table
    for computation_type in ["HRING", "SEMIPROB", "SIMPLE", "DSTABILITY"]:
        ComputationType.create(name=computation_type)
        #check if dict has key
    if 'overslag' in mechanism_data.keys():
        if isinstance(mechanism_data['overslag'], pd.DataFrame):
            fill_overflow(mechanism_data['overslag'], shape_file=shape_file)

    if 'stabiliteit' in mechanism_data.keys():
        if isinstance(mechanism_data['stabiliteit'], pd.DataFrame):
            fill_stability(mechanism_data['stabiliteit'], shape_file=shape_file)

    if 'piping' in mechanism_data.keys():
        if isinstance(mechanism_data['piping'], pd.DataFrame):
            fill_piping(mechanism_data['piping'], shape_file=shape_file)

    if 'slope_part_table' in mechanism_data.keys():
        if isinstance(mechanism_data['slope_part_table'], dict):
            fill_revetment(mechanism_data['slope_part_table'], mechanism_data['rel_GEBU_table'], mechanism_data['rel_ZST_table'], shape_file=shape_file)

def fill_overflow(overflow_table, shape_file, computation_type="HRING"):
    # get id of Overflow from Mechanism table
    overflow_id = (
        Mechanism.select(Mechanism.id).where(Mechanism.name == "Overflow").get().id
    )
    relevant_indices = [
        val
        for val in MechanismPerSection.select()
        .where(MechanismPerSection.mechanism == overflow_id)
        .dicts()
    ]
    section_names = [
        SectionData.select().where(SectionData.id == row["id"]).dicts()
        for row in relevant_indices
    ]
    # loop over relevant_indices
    for count, row in enumerate(relevant_indices):
        # sscenario name should be equal to LocationId in overflow_table
        section_name = (
            SectionData.select()
            .where(SectionData.id == row["section"])
            .get()
            .section_name
        )
        scenario_name = shape_file.loc[shape_file["vaknaam"] == section_name][
            "overslag"
        ].values[0]
        computation_type = (
            ComputationType.select().where(ComputationType.name == "HRING").get().id
        )
        ComputationScenario.create(
            mechanism_per_section=row["id"],
            mechanism=overflow_id,
            computation_name=scenario_name,
            scenario_name=scenario_name,
            scenario_probability=1.0,
            computation_type=computation_type,
            probability_of_failure=1.0,
        )
        # TODO: probability_of_failure should not be Required, but it is now.
        # TODO: scenario_name should not be Required, but it is now.

        # for overflow we fill MechanismTables
        # for each ComputationSceanrio for Overflow, fill the MechanismTable
        # find the ComputationName that belongs to row
        computation_name = (
            ComputationScenario.select()
            .where(ComputationScenario.mechanism_per_section == row["id"])
            .get()
            .computation_name
        )
        computation_id = (
            ComputationScenario.select()
            .where(ComputationScenario.mechanism_per_section == row["id"])
            .get()
            .id
        )
        for count, row in overflow_table.loc[computation_name].iterrows():
            # create a row in MechanismTable
            MechanismTable.create(
                computation_scenario=computation_id,
                year=row["Year"],
                value=row["CrestHeight"],
                beta=row["Beta"],
            )


def fill_piping(piping_table, shape_file):
    piping_id = (
        Mechanism.select(Mechanism.id).where(Mechanism.name == "Piping").get().id
    )
    if 'dh_exit' in piping_table.columns:
        piping_table = piping_table.rename(columns={'dh_exit': 'dh_exit(t)'})
    relevant_indices = [
        val
        for val in MechanismPerSection.select()
        .where(MechanismPerSection.mechanism == piping_id)
        .dicts()
    ]
    # iterrows over relevant_indices
    for count, row in enumerate(relevant_indices):
        section_name = (
            SectionData.select()
            .where(SectionData.id == row["section"])
            .get()
            .section_name
        )
        cross_section = shape_file.loc[shape_file["vaknaam"] == section_name][
            "piping"
        ].values[0]
        if isinstance(piping_table.loc[cross_section], pd.Series):
            add_computation_scenario(
                piping_table.loc[cross_section], row["id"], cross_section, piping_id
            )
        else:
            for scen_count, subset in piping_table.loc[cross_section].iterrows():
                add_computation_scenario(subset, row["id"], cross_section, piping_id)


def fill_stability(stability_table, shape_file):
    # get id of Stability from Mechanism table
    stability_id = (
        Mechanism.select(Mechanism.id)
        .where(Mechanism.name == "StabilityInner")
        .get()
        .id
    )
    relevant_indices = [
        val
        for val in MechanismPerSection.select()
        .where(MechanismPerSection.mechanism == stability_id)
        .dicts()
    ]
    # iterrows over relevant_indices
    for count, row in enumerate(relevant_indices):
        section_name = (
            SectionData.select()
            .where(SectionData.id == row["section"])
            .get()
            .section_name
        )
        cross_section = shape_file.loc[shape_file["vaknaam"] == section_name][
            "stabiliteit"
        ].values[0]
        if isinstance(stability_table.loc[cross_section], pd.Series):
            add_computation_scenario(
                stability_table.loc[cross_section],
                row["id"],
                cross_section,
                stability_id,
            )
        else:
            for scen_count, subset in stability_table.loc[cross_section].iterrows():
                add_computation_scenario(subset, row["id"], cross_section, stability_id)


def add_stability_scenario(
    data, mechanism_per_section_id, cross_section, mechanism_id, scenario_name
):
    if isinstance(data["stixnaam"], str):
        computation_type = (
            ComputationType.select().where(ComputationType.name == "DSTABILITY").get().id
        )
    else:
        computation_type = (
            ComputationType.select().where(ComputationType.name == "SIMPLE").get().id
        )

    beta_value = data["beta"]
    # if nan then get SF from data
    if np.isnan(beta_value):
        beta_value = calculate_reliability(data[["SF"]].values).item()

    ComputationScenario.create(
        mechanism_per_section=mechanism_per_section_id,
        mechanism=mechanism_id,
        computation_name=cross_section,
        scenario_name=scenario_name,
        scenario_probability=data["scenariokans"],
        computation_type=computation_type,
        probability_of_failure=beta_to_pf(beta_value),
    )
    # for each computation_scenario fill Parameter. first get the last computation_scenario_id that matches mechanism_per_section_id

    computation_scenario_id = [
        val
        for val in ComputationScenario.select()
        .where(ComputationScenario.mechanism_per_section == mechanism_per_section_id)
        .dicts()
    ][-1]["id"]


    ComputationScenarioParameter.create(
        computation_scenario=computation_scenario_id, parameter="beta", value=beta_value
    )
    if isinstance(data.stixnaam, str):
        SupportingFile.create(
            computation_scenario=computation_scenario_id, filename=data.stixnaam
        )


def add_piping_scenario(
    data, mechanism_per_section_id, cross_section, mechanism_id, scenario_name
):
    computation_type = (
        ComputationType.select().where(ComputationType.name == "SEMIPROB").get().id
    )
    ComputationScenario.create(
        mechanism_per_section=mechanism_per_section_id,
        mechanism=mechanism_id,
        computation_name=cross_section,
        scenario_name=scenario_name,
        scenario_probability=data["scenariokans"],
        computation_type=computation_type,
        probability_of_failure= 1.0,
    )
    # it was using probability of failure from default_piping (which is optional). This gives problems when it is not
    # filled in by the user. Therefore, dummy value used for now.
    # TODO: probability_of_failure should not be Required, but it is now.

    # for each computation_scenario fill Parameter
    computation_scenario_id = [
        val
        for val in ComputationScenario.select()
        .where(ComputationScenario.mechanism_per_section == mechanism_per_section_id)
        .dicts()
    ][-1]["id"]
    parameters_to_add = [
        "wbn",
        "polderpeil",
        "d_wvp",
        "d70",
        "d_cover",
        "h_exit",
        "r_exit",
        "l_voor",
        "l_achter",
        "k",
        "gamma_sat",
        "kwelscherm",
        "dh_exit(t)",
    ]
    for parameter_name in parameters_to_add:
        ComputationScenarioParameter.create(
            computation_scenario=computation_scenario_id,
            parameter=parameter_name,
            value=data[parameter_name],
        )


def add_computation_scenario(
    data, mechanism_per_section_id, cross_section, mechanism_id
):
    if (
        Mechanism.select().where(Mechanism.id == mechanism_id).get().name
        == "StabilityInner"
    ):
        scenario_name = data["scenarionaam"]
        add_stability_scenario(
            data, mechanism_per_section_id, cross_section, mechanism_id, scenario_name
        )
    elif Mechanism.select().where(Mechanism.id == mechanism_id).get().name == "Piping":
        scenario_name = "{}_{}".format(cross_section, data["scenario"])
        add_piping_scenario(
            data, mechanism_per_section_id, cross_section, mechanism_id, scenario_name
        )
    else:
        raise Exception("Unknown mechanism in ComputationScenario")


def fill_revetment(slope_part_table, rel_GEBU_table, rel_ZST_table, shape_file):
    
    # get id of Revetment from Mechanism table
    revetment_id = (
        Mechanism.select(Mechanism.id).where(Mechanism.name == "Revetment").get().id
    )
    relevant_indices = [
        val
        for val in MechanismPerSection.select()
        .where(MechanismPerSection.mechanism == revetment_id)
        .dicts()
    ]
    
    # loop over relevant_indices
    for count, row in enumerate(relevant_indices):
        # sscenario name should be equal to LocationId in overflow_table
        section_name = (
            SectionData.select()
            .where(SectionData.id == row["section"])
            .get()
            .section_name
        )
        scenario_name = shape_file.loc[shape_file["vaknaam"] == section_name][
            "bekledingen"
        ].values[0]
        
        computation_type = (
            ComputationType.select().where(ComputationType.name == "SEMIPROB").get().id
        )
        
        ComputationScenario.create(
            mechanism_per_section=row["id"],
            mechanism=revetment_id,
            computation_name=scenario_name,
            scenario_name=scenario_name,
            scenario_probability=1.0,
            computation_type=computation_type,
            probability_of_failure=1.0,
        )
        
        computation_id = (
            ComputationScenario.select()
            .where(ComputationScenario.mechanism_per_section == row["id"])
            .get()
            .id
        )

        index = np.argwhere(np.array(slope_part_table["location"])==scenario_name)
        for ind in index:
            #Temporary fix for Noorse steen:
            if slope_part_table["top_layer_type"][ind[0]]==28.6:
                slope_part_table["top_layer_type"][ind[0]] = 27.9
                
            current_slope_part = SlopePart.create(
                computation_scenario_id = computation_id,
                begin_part = slope_part_table["begin_part"][ind[0]],
                end_part = slope_part_table["end_part"][ind[0]],
                top_layer_type = slope_part_table["top_layer_type"][ind[0]],
                top_layer_thickness = slope_part_table["top_layer_thickness"][ind[0]],
                tan_alpha = slope_part_table["tan_alpha"][ind[0]],
            )

            if slope_part_table["top_layer_type"][ind[0]]>=26.0 and slope_part_table["top_layer_type"][ind[0]]<=27.9:
                index1 = np.argwhere((np.array(rel_ZST_table["location"])==scenario_name) & (np.array(rel_ZST_table["slope_part"])==slope_part_table["slope_part"][ind[0]]))
                for ind1 in index1:
                    BlockRevetmentRelation.create(
                        slope_part_id = current_slope_part.get_id(),
                        year = rel_ZST_table["year"][ind1[0]],
                        top_layer_thickness = rel_ZST_table["top_layer_thickness"][ind1[0]],
                        beta = rel_ZST_table["beta"][ind1[0]],
                    )

        index = np.argwhere(np.array(rel_GEBU_table["location"])==scenario_name)
        for ind in index:
            GrassRevetmentRelation.create(  
                computation_scenario_id = computation_id,
                year = rel_GEBU_table["year"][ind[0]],
                transition_level = rel_GEBU_table["transition_level"][ind[0]],
                beta = rel_GEBU_table["beta"][ind[0]],
            )

def fill_structures():
    pass


def fill_measures(measure_table, list_of_sections = []):

    # fill MeasureType if they are not already in the database
    for type in measure_table["measure_type"].unique():
        if not MeasureType.select().where(MeasureType.name == type).exists():
            MeasureType.create(name=type)

    # fill CombinableType if they are not already in the database
    for combinable_types in ["full", "combinable", "partial", "revetment"]:
        if not CombinableType.select().where(CombinableType.name == combinable_types).exists():
            CombinableType.create(name=combinable_types)

    # fill StandardMeasure
    measure_ids = []
    for idx, row in measure_table.iterrows():
        measure_type_id = (
            MeasureType.select().where(MeasureType.name == row["measure_type"]).get().id
        )
        combinable_type_id = (
            CombinableType.select().where(CombinableType.name == row["combinable_type"]).get().id
        )
        Measure.create(
            name=idx,
            measure_type=measure_type_id,
            combinable_type=combinable_type_id,
            year=row["year"],
        )
        #only the just added measure_id is added to the list
        measure_ids.append(Measure.select().dicts()[-1]["id"])
        
        row = row.fillna(-999)
        #set row'pipe_reduction_factor' to None if it is -999
        row['piping_reduction_factor'] = None if row['piping_reduction_factor'] == -999 else row['piping_reduction_factor']
        
        StandardMeasure.create(
            measure=measure_ids[-1],
            max_inward_reinforcement=row["max_inward_reinforcement"],
            max_outward_reinforcement=row["max_outward_reinforcement"],
            direction=row["direction"],
            crest_step=row["crest_step"],
            max_crest_increase=row["max_crest_increase"],
            stability_screen=row["stability_screen"],
            transition_level_increase_step=row["transition_level_increase_step"],
            max_pf_factor_block=row["max_pf_factor_block"],
            n_steps_block=row["n_steps_block"],
            piping_reduction_factor = row["piping_reduction_factor"],
        )


    if len(list_of_sections) == 0:
        section_ids = [val["id"] for val in SectionData.select().dicts()]
    else:
        section_ids = [val["id"] for val in SectionData.select().where(SectionData.section_name << list_of_sections).dicts()]
    for section_id in sorted(section_ids):
        kerende_hoogte = get_kerende_hoogte(section_id)
        revetment = check_if_revetment(section_id)

        #get from MechanismPerSection whether section_id has revetment
        for measure_id in measure_ids:
            #get name from Measure
            measure_name = Measure.select().where(Measure.id == measure_id).get().name
            if kerende_hoogte >2:
                if "Kruinverhoging" in measure_name:
                    continue
            elif kerende_hoogte <=2:
                if "Grondversterking" in measure_name:
                    continue
            if not revetment:
                if "Aanpassing bekleding" in measure_name:
                    continue

            #Include measure:
            MeasurePerSection.create(section=section_id, measure=measure_id)
def check_if_revetment(section_id):
    try:
        MechanismPerSection.select().where(
            (MechanismPerSection.section == section_id) & (MechanismPerSection.mechanism == 4)).get()
        return True
    except:
        return False
def get_kerende_hoogte(section_id):
    # get id of BIT and BIK from CharacteristicPointType
    BIT_id = CharacteristicPointType.select().where(CharacteristicPointType.name == "BIT").get().id
    BIK_id = CharacteristicPointType.select().where(CharacteristicPointType.name == "BIK").get().id
    # get y_coordinate of BIT and BIK for section_data_id=section_id from ProfilePoints
    BIT_y = ProfilePoint.select().where(
        (ProfilePoint.section_data == section_id) & (ProfilePoint.profile_point_type_id == BIT_id)).get().y_coordinate
    BIK_y = ProfilePoint.select().where(
        (ProfilePoint.section_data == section_id) & (ProfilePoint.profile_point_type_id == BIK_id)).get().y_coordinate
    return BIK_y - BIT_y
def compare_databases(path_to_generated_db, path_to_reference_db):

    # Step 1: Connect to databases
    generated_db_conn = sqlite3.connect(path_to_generated_db)
    reference_db_conn = sqlite3.connect(path_to_reference_db)

    # Step 2: Fetch table information
    generated_tables = generated_db_conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    reference_tables = reference_db_conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    #check if the tables are equal and write to log
    comparison_message = ""
    if not generated_tables == reference_tables:
        comparison_message += "The generated database and the reference database do not have the same tables \n"
    # Step 3: Compare table structure
    for table_name in generated_tables:
        # Fetch table structure from generated database
        generated_table_structure = generated_db_conn.execute(f"PRAGMA table_info({table_name[0]});").fetchall()

        # Fetch table structure from reference database
        reference_table_structure = reference_db_conn.execute(f"PRAGMA table_info({table_name[0]});").fetchall()

        # Compare the structures
        if not generated_table_structure == reference_table_structure:
            comparison_message += "The generated database and the reference database do not have the same table structure for table {} \n".format(table_name[0])
    # Step 4: Compare table contents
    for table_name in generated_tables:
        # Fetch all rows from the generated database
        generated_rows = generated_db_conn.execute(f"SELECT * FROM {table_name[0]};").fetchall()

        # Fetch all rows from the reference database
        try:
            reference_rows = reference_db_conn.execute(f"SELECT * FROM {table_name[0]};").fetchall()
        except:
            reference_rows = []
        # Compare the rows and columns
        if not generated_rows == reference_rows:
            comparison_message += "The generated database and the reference database do not have the same table contents for table {} \n".format(table_name[0])
            continue
    # Step 5: Perform assertions
    if len(comparison_message)>0:
        raise AssertionError(comparison_message)

    # Close the database connections
    generated_db_conn.close()
    reference_db_conn.close()
