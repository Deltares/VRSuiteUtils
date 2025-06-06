import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
from owslib.wfs import WebFeatureService
from shapely import geometry, ops
import logging

from common_functions import log_and_raise_error

class TrajectShape:
    """Class with functions to modify and fill the shape of a traject which is the basic reference for all preprocessing steps"""

    def __init__(self, traject):
        self.traject = traject

    def get_traject_shape_from_NBPW(self, NBWP_shape_path=False):
        if not NBWP_shape_path:
            # get from WFS
            wfs_nbpw = WebFeatureService(
                url="https://geo.rijkswaterstaat.nl/services/ogc/wvp/ows/wfs",
                # url="https://waterveiligheidsportaal.nl/geoserver/nbpw/ows/wfs",
                version="1.1.0",
            )
            NBPW = gpd.read_file(
                wfs_nbpw.getfeature("dijktrajecten", outputFormat="json")
            )
            logging.info("NBPW geladen van WFS server")
        else:
            NBPW = gpd.read_file(NBWP_shape_path)
            logging.info("NBPW geladen van lokale file {}".format(NBWP_shape_path))
        self.NBPW_shape = NBPW.loc[NBPW.TRAJECT_ID == self.traject].reset_index(
            drop=True
        )
        self.NBPW_shape = self.NBPW_shape[
            ["TRAJECT_ID", "NORM_SW", "NORM_OG", "geometry"]
        ]
        self.NBPW_shape = self.NBPW_shape.explode(index_parts=True)
        if len(self.NBPW_shape) > 1:
            warnings.warn("Warning: NBPW shape has more than 1 geometry")
        self.ondergrens = self.NBPW_shape["NORM_OG"].iloc[0]
        self.signaleringswaarde = self.NBPW_shape["NORM_SW"].iloc[0]
    def flip_traject(self):
        """function that reverts a line (self.NBPW_shape['geometry']) that contains a linestring of x and y coordinates.
         In other words: the function draws the line backwards. The geometry is updated in place.
        """
        self.NBPW_shape["geometry"] = self.NBPW_shape["geometry"].apply(
            lambda x: geometry.LineString(list(x.coords)[::-1]),
            lambda y: geometry.LineString(list(y.coords)[::-1]),
        )


    @staticmethod
    def check_vakindeling(df_vakindeling, traject_length):
        """Function to check the integrity of a vakindeling df to be used to cut up the traject_shape of the NBPW"""
        # checks the integrity of the vakindeling as inputted.
    

        # required_headers
        set(["objectid", "vaknaam", "m_start", "m_eind", "in_analyse"]).issubset(
            df_vakindeling.columns
        )

        # check if OBJECTID and NUMMER have unique values
        try:
            if any(df_vakindeling["objectid"].duplicated()):
                log_and_raise_error("values in OBJECTID are not unique", ValueError)
        except:
            df_vakindeling["objectid"] = list(range(1, len(df_vakindeling + 1)))

        if any(df_vakindeling["vaknaam"].duplicated()):
            log_and_raise_error("values in VAKNAAM are not unique", ValueError)

        # sort the df by OBJECTID:
        df_vakindeling = df_vakindeling.sort_values("objectid")

        df_vakindeling = df_vakindeling.fillna(value=np.nan)
        # check if, if sorted on OBJECTID M_START and M_EIND are increasing
        if any(np.diff(df_vakindeling.m_eind) < 0):
            log_and_raise_error(
                "m_eind values zijn niet altijd toenemend als gesorteerd op objectid", ValueError
            )
        if any(np.diff(df_vakindeling.m_start) < 0):
            log_and_raise_error(
                "m_start values zijn niet altijd toenemend als gesorteerd op objectid", ValueError
            )
        if any(np.subtract(df_vakindeling.m_eind, df_vakindeling.m_start) < 0.0):
            log_and_raise_error(
                "m_start is hoger dan m_eind voor tenminste 1 dijkvak", ValueError
            )
        # check if MEAS_END.max() is approx equal to traject_length
        try:
            np.testing.assert_approx_equal(
                df_vakindeling.m_eind.max(), traject_length, significant=5
            )
        except AssertionError as e:
            log_and_raise_error(
                f"Traject heeft een andere lengte dan opgegeven in de vakindeling csv. Controleer de m_start en m_eind waarden in de csv: {e}", AssertionError
            )
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
                    geometry.LineString(coords[: i + 1]),
                    geometry.LineString(coords[i:]),
                ]
            if pd > distance:
                cp = line.interpolate(distance)
                return [
                    geometry.LineString(coords[:i] + [(cp.x, cp.y)]),
                    geometry.LineString([(cp.x, cp.y)] + coords[i:]),
                ]

    def generate_vakindeling_shape(self, vakken_path):
        def check_column_presence(df):
            required_columns = {
                "objectid": int,
                "vaknaam": str,
                "m_start": float,
                "m_eind": float,
                "in_analyse": bool,
                "stabiliteit": str,
                "piping": str,
                "overslag": str,
                "bekledingen": str,
            }
            optional_columns = {
                "van_dp": str,
                "tot_dp": str,
                "pleistoceendiepte": float,
                "deklaagdikte": float,
                "a_piping": float,
                "a_stabiliteit": float,
            }            #check if all required columns are present. Otherwise return a ValueError
            for col in required_columns:
                if col not in df.columns:
                    raise log_and_raise_error(f"Kolom {col} ontbreekt in de vakindeling csv. Deze is verplicht en moet worden toegevoegd.", ValueError)
            #check which optional columns are present and put them in a list. Print a warning if they are not present.
            _present_optional_columns = {}
            for item in optional_columns.items():
                if item[0] in df.columns:
                    _present_optional_columns[item[0]] = item[1]
                else:
                    logging.warning(f"Optionele kolom {item[0]} ontbreekt in de vakindeling csv. ")
            #combine both dicts
            present_columns = {**required_columns, **_present_optional_columns}
            return present_columns
        
        def check_column_content(df, present_columns_types):
            #check for each column if there are None/NaN values. Log separate warnings for each column depending on one or multiple values being NaN/None
            for col, col_type in present_columns_types.items():
                if df[col].isnull().all():
                    logging.warning(f"Kolom {col} in vakindeling_csv bevat geen waarden (alle waarden NaN of None).")
                elif df[col].isnull().any():
                    logging.warning(f"Kolom {col} in vakindeling_csv bevat enkele NaN of None waarden. Controleer de input data.")

        #get the vakindeling shape from the vakken_path
        df_vakken = pd.read_csv(vakken_path)
        _present_columns_types = check_column_presence(df_vakken)
        logging.info("Controle op de aanwezigheid van de vereiste kolommen in de vakindeling csv is uitgevoerd. \n")

        check_column_content(df_vakken, _present_columns_types)
        logging.info("Controle op de inhoud van de kolommen in de vakindeling csv is uitgevoerd. \n")
        
        df_vakken = df_vakken[_present_columns_types.keys()]
        #check if the columns have the right types
        df_vakken = df_vakken.astype(_present_columns_types)


        self.check_vakindeling(df_vakken, self.NBPW_shape.geometry.length.values[0])
        logging.info("Vakindeling shape is gecontroleerd op juiste geometrische waarden. \n")
        traject_geom = self.NBPW_shape.geometry[0][0]

        section_geom = []
        total_dist = 0.0
        for count, row in df_vakken.iterrows():
            try:
                section, traject_geom = self.cut(traject_geom, row["m_eind"] - total_dist)
            except: # catch the case where the last section ends exactly at the end of the traject
                section = self.cut(traject_geom, row["m_eind"] - total_dist)[0]
            total_dist += section.length
            section_geom.append(section)
            # sanity check. VAKLENGTE column and section length should be almost equal
            try:
                np.testing.assert_approx_equal(
                    row["m_eind"] - row["m_start"], section.length, significant=5
                )
            except AssertionError as e:
                logging.error(
                    f"Traject heeft een andere lengte dan opgegeven in de vakindeling csv. Controleer de m_start en m_eind waarden in de csv: {e}" 
                )
                raise
        self.vakindeling_shape = gpd.GeoDataFrame(
            df_vakken, geometry=section_geom, crs=self.NBPW_shape.crs
        )
        logging.info("Shapefile succesvol opgeknipt. \n")
