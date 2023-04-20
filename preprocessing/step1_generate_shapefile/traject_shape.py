import pandas as pd
from owslib.wfs import WebFeatureService
import geopandas as gpd
import numpy as np
from shapely import geometry, ops
import warnings
class TrajectShape:
    '''Class with functions to modify and fill the shape of a traject which is the basic reference for all preprocessing steps'''
    def __init__(self, traject):
        self.traject = traject

    def get_traject_shape_from_NBPW(self, NBWP_shape_path=False):
        if not NBWP_shape_path:
            # get from WFS
            wfs_nbpw = WebFeatureService(url='https://waterveiligheidsportaal.nl/geoserver/nbpw/ows/wfs',
                                         version='1.1.0')
            NBPW = gpd.read_file(wfs_nbpw.getfeature('nbpw:dijktrajecten', outputFormat='json'))
        else:
            NBPW = gpd.read_file(NBWP_shape_path)
        self.NBPW_shape = NBPW.loc[NBPW.TRAJECT_ID == self.traject].reset_index(drop=True)
        self.NBPW_shape = self.NBPW_shape[['TRAJECT_ID', 'NORM_SW','NORM_OG','geometry']]
        self.NBPW_shape = self.NBPW_shape.explode()
        if len(self.NBPW_shape)>1:
            warnings.warn('Warning: NBPW shape has more than 1 geometry')


    @staticmethod
    def check_vakindeling(df_vakindeling, traject_length):
        '''Function to check the integrity of a vakindeling df to be used to cut up the traject_shape of the NBPW'''
        # checks the integrity of the vakindeling as inputted.

        #required_headers
        set(['OBJECTID','VAKNUMMER', 'M_START', 'M_EIND']).issubset(df_vakindeling.columns)

        # check if OBJECTID and NUMMER have unique values
        try:
            if any(df_vakindeling['OBJECTID'].duplicated()): raise ('values in OBJECTID are not unique')
        except:
            df_vakindeling['OBJECTID'] = list(range(1,len(df_vakindeling+1)))

        if any(df_vakindeling['VAKNUMMER'].duplicated()): raise ('values in VAKNUMMER are not unique')

        # sort the df by OBJECTID:
        df_vakindeling = df_vakindeling.sort_values('OBJECTID')

        df_vakindeling = df_vakindeling.fillna(value=np.nan)
        # check if, if sorted on OBJECTID M_START and M_EIND are increasing
        if any(np.diff(df_vakindeling.M_EIND) < 0): raise ValueError(
            'M_EIND values are not always increasing if sorted on OBJECTID')
        if any(np.diff(df_vakindeling.M_START) < 0): raise ValueError(
            'M_START values are not always increasing if sorted on OBJECTID')
        if any(np.subtract(df_vakindeling.M_EIND, df_vakindeling.M_START) < 0.): raise ValueError(
            'M_START is higher than M_EIND for at least 1 section')

        # check if MEAS_END.max() is approx equal to traject_length
        np.testing.assert_approx_equal(df_vakindeling.M_EIND.max(), traject_length, significant=5)

        return df_vakindeling


    @staticmethod
    def cut(line, distance):
        # Cuts a line in two at a distance from its starting point
        if distance <= 0.0 or distance >= line.length:
            return [geometry.LineString(line)]
        coords = list(line.coords)
        for i, p in enumerate(coords):
            pd = line.project(geometry.Point(p))
            if pd == distance:
                return [
                    geometry.LineString(coords[:i + 1]),
                    geometry.LineString(coords[i:])]
            if pd > distance:
                cp = line.interpolate(distance)
                return [
                    geometry.LineString(coords[:i] + [(cp.x, cp.y)]),
                    geometry.LineString([(cp.x, cp.y)] + coords[i:])]

    def generate_vakindeling_shape(self, vakken_path):
        df_vakken = pd.read_excel(vakken_path,sheet_name='Algemeen',
                                  usecols = ['OBJECTID', 'VAKNUMMER', 'M_START', 'M_EIND', 'IN_ANALYSE'],
                                  dtype = {'OBJECTID':np.int64, 'VAKNUMMER':str,'M_START':np.float64,'M_EIND':np.float64,'IN_ANALYSE':np.int64})
        self.check_vakindeling(df_vakken,self.NBPW_shape.geometry.length.values[0])
        traject_geom = self.NBPW_shape.geometry[0][0]

        section_geom = []
        total_dist = 0.
        for count, row in df_vakken.iterrows():
            section, traject_geom = self.cut(traject_geom, row['M_EIND'] - total_dist)
            section_geom.append(section)
            total_dist += section.length
            # sanity check. VAKLENGTE column and section length should be almost equal
            np.testing.assert_approx_equal(section.length, row['M_EIND']-row['M_START'], significant=5)
        self.vakindeling_shape = gpd.GeoDataFrame(df_vakken, geometry=section_geom)
