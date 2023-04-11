import numpy as np
import geopandas as gpd
import pandas as pd
import warnings
import sqlite3

class OverflowInput:
    def __init__(self,traject_shape,kind='weakest'):
        self.traject = gpd.read_file(traject_shape)
        self.kind = kind
    def get_mvalue_of_locs(self,hring_locs,gekb_shape=False):
        #gets M_VALUES for a gekb_shape with sections with bounds M_VAN and M_TOT
        gekb_shape = gekb_shape
        gekb_shape['M_VALUE'] = np.add(gekb_shape.M_VAN, gekb_shape.M_TOT) / 2
        self.hring_data = pd.merge(hring_locs.drop(columns=['M_VALUE']),gekb_shape[['OBJECTID','M_VALUE']],left_on='nr',right_on='OBJECTID')

    @staticmethod
    def select_weakest(section_set,section_name):
        weakest_cs = section_set[section_set.faalkans == section_set.faalkans.max()]
        if len(weakest_cs) > 1: warnings.warn('Warning multiple weakest cs for section {}, returning first'.format(section_name))
        return weakest_cs.index.values[-1]

    @staticmethod
    def select_closest(section,locs):
        #distance to midpoint of section:
        distance = np.abs(np.subtract(locs.M_VALUE, np.mean([section.M_START, section.M_EIND])))
        return np.argmin(distance)

    def get_HRLocation(self,db_location):
        cnx = sqlite3.connect(db_location)
        # TODO make cnx flexible
        locs = pd.read_sql_query("SELECT * FROM HRDLocations", cnx)
        for count, line in self.hring_data.iterrows():
            self.hring_data.loc[count,'HRLocation'] = locs.loc[locs['Name'] == line['HR koppel']]['HRDLocationId'].values[0]
        self.hring_data['HRLocation'] = self.hring_data['HRLocation'].astype(np.int64)
    def select_locs(self):
        #for each section
        indices = []
        for count, section in self.traject.iterrows():
            # get subset of GEKB locations
            subset = self.hring_data.loc[(self.hring_data.M_VALUE > section.M_START) & (self.hring_data.M_VALUE < section.M_EIND)]
            if self.kind == 'weakest':
                #take closest if subset is empty
                if subset.shape[0] == 0:
                    index_val = self.select_closest(section,self.hring_data)
                else:
                #get weakest
                    index_val = self.select_weakest(subset,section.VAKNUMMER)
            else:
                raise Exception('No method found for kind: {}'.format(self.kind))
            indices.append(index_val)
        self.hring_data = self.hring_data.iloc[indices].reset_index().rename(columns={'index': 'ID'})

    def verify_and_filter_columns(self):
        required_cols = ['M_VALUE','bovengrens','ondergrens','prfl_bestand','orientatie','dijkhoogte','zodeklasse','golfhoogteklasse','kruindaling','HRLocation']
        optional_cols = ['dijkvak','faalkans']
        if hasattr(self,'hring_data'):
            for column in self.hring_data.columns:
                if column not in required_cols + optional_cols:
                    self.hring_data = self.hring_data.drop(columns=column)

            #TODO verify values in columns
        else:
            raise Exception('hring_data not present, verification of columns is not possible')