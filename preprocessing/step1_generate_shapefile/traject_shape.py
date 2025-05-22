import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
from owslib.wfs import WebFeatureService
from shapely import geometry, ops


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
        else:
            NBPW = gpd.read_file(NBWP_shape_path)
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
                raise ("values in OBJECTID are not unique")
        except:
            df_vakindeling["objectid"] = list(range(1, len(df_vakindeling + 1)))

        if any(df_vakindeling["vaknaam"].duplicated()):
            raise ("values in VAKNAAM are not unique")

        # sort the df by OBJECTID:
        df_vakindeling = df_vakindeling.sort_values("objectid")

        df_vakindeling = df_vakindeling.fillna(value=np.nan)
        # check if, if sorted on OBJECTID M_START and M_EIND are increasing
        if any(np.diff(df_vakindeling.m_eind) < 0):
            raise ValueError(
                "m_eind values are not always increasing if sorted on objectid"
            )
        if any(np.diff(df_vakindeling.m_start) < 0):
            raise ValueError(
                "m_start values are not always increasing if sorted on objectid"
            )
        if any(np.subtract(df_vakindeling.m_eind, df_vakindeling.m_start) < 0.0):
            raise ValueError("m_eind is higher than m_eind for at least 1 section")

        # check if MEAS_END.max() is approx equal to traject_length
        np.testing.assert_approx_equal(
            df_vakindeling.m_eind.max(), traject_length, significant=5
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
        #get the vakindeling shape from the vakken_path
        df_vakken = pd.read_csv(vakken_path)
        try:
            #check if vakken_path contains "pleistoceendiepte" and "deklaagdikte" columns
            if "pleistoceendiepte" in df_vakken.columns and "deklaagdikte" in df_vakken.columns:
                #new format: select the columns and set dtypes
                df_vakken = df_vakken[["objectid", "vaknaam", "m_start", "m_eind", "in_analyse", "van_dp", "tot_dp", "stabiliteit", "piping", "overslag", "bekledingen", "pleistoceendiepte", "deklaagdikte"]]
                df_vakken = df_vakken.astype({"objectid": int, "vaknaam": object, "m_start": float, "m_eind": float, "in_analyse": int, "van_dp": object, "tot_dp": object, "stabiliteit": object, "piping": object, "overslag": object, "bekledingen": object, "pleistoceendiepte": float, "deklaagdikte": float})
            else:
                df_vakken = df_vakken[["objectid", "vaknaam", "m_start", "m_eind", "in_analyse", "van_dp", "tot_dp", "stabiliteit", "piping", "overslag", "bekledingen",]]
                df_vakken = df_vakken.astype({"objectid": int, "vaknaam": object, "m_start": float, "m_eind": float, "in_analyse": int, "van_dp": object, "tot_dp": object, "stabiliteit": object, "piping": object, "overslag": object, "bekledingen": object})
        except:
            raise ValueError(f"Vakindeling bestand {vakken_path} kon niet worden gelezen. Controleer het bestand op de juiste indeling, bijvoorbeeld op lege rijen.")
        
        self.check_vakindeling(df_vakken, self.NBPW_shape.geometry.length.values[0])
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
            np.testing.assert_approx_equal(
                row["m_eind"] - row["m_start"], section.length, significant=5
            )
        self.vakindeling_shape = gpd.GeoDataFrame(
            df_vakken, geometry=section_geom, crs=self.NBPW_shape.crs
        )
