import pandas as pd
from pathlib import Path
import sqlite3
import geopandas as gpd
import os
import numpy as np
from vrtool.orm.models import *
import warnings
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

            row_filtered = row.drop(columns=['OBJECTID','NUMMER'])
            for distance, number in row_filtered.iteritems():
                Buildings.create(section_data = vak_id,distance_from_toe=distance,number_of_buildings = number)
        except:
            warnings.warn('Dijkvak {} niet in SectionData'.format(row.NUMMER))
    pass

def fill_waterleveldata(waterleveldata):
    pass

class SQLiteDatabase:
    def __init__(self, db_path, traject):
        self.db_path = db_path
        self.cnx = sqlite3.connect(db_path)
        self.traject = traject
        self.diketrajectinfo = pd.read_csv(Path(__file__).parent.joinpath('generic_data','diketrajectinfo.csv'),index_col=0).loc[self.traject]\
            .to_frame().transpose().reset_index().rename(columns={'index':'traject_name','level_0':'id'})
    def load_vakindeling_shape(self,shape_path):
        #load shape
        self.vakindeling_shape = gpd.read_file(shape_path)
        self.diketrajectinfo
    def write_diketrajectinfo_table(self):
        #write trajectinfo
        self.diketrajectinfo.to_sql('DikeTrajectInfo',self.cnx,if_exists='replace',index_label='id')

    def write_sectiondata_table(self):
        '''Writes the section data to a sqlite database'''
        section_data = pd.DataFrame(
            columns=['id', 'section_name', 'dijkpaal_start', 'dijkpaal_end', 'meas_start', 'meas_end',
                     'section_length', 'in_analysis', 'crest_height', 'annual_crest_decline',
                     'cover_layer_thickness', 'pleistocene_level'])
        section_data['id'] = self.vakindeling_shape['OBJECTID']
        section_data['section_name'] = self.vakindeling_shape['VAKNUMMER']
        section_data['meas_start'] = self.vakindeling_shape['M_START']
        section_data['meas_end'] = self.vakindeling_shape['M_EIND']
        section_data['section_length'] = self.vakindeling_shape['M_EIND'] - self.vakindeling_shape['M_START']
        section_data['in_analysis'] = self.vakindeling_shape['IN_ANALYSE']

        section_data.to_sql('SectionData', self.cnx, if_exists='replace', index=False,index_label='id')

    def write_waterleveldata_table(self, waterleveldata):
        '''Writes the waterleveldata to a sqlite database'''
        pass

    def write_mechanismspersection_table(self, mechanismspersection):
        '''Writes the mechanismspersection to a sqlite database'''
        pass
