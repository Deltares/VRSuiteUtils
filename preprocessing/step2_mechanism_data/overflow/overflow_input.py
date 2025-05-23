import sqlite3
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd


class OverflowInput:
    def __init__(self, kind="weakest"):
        self.kind = kind

    def add_traject_shape(self, traject_shape):
        # add the shape of the traject
        self.traject = gpd.read_file(traject_shape)

    def get_mvalue_of_locs(self, hring_locs, gekb_shape):
        # gets M_VALUES for a gekb_shape with sections with bounds M_VAN and M_TOT
        gekb_shape["m_value"] = np.add(gekb_shape.M_VAN, gekb_shape.M_TOT) / 2
        self.add_hring_data(
            pd.merge(
                hring_locs.drop(columns=["m_value"]),
                gekb_shape[["OBJECTID", "m_value"]],
                left_on="nr",
                right_on="OBJECTID",
            )
        )

    def add_hring_data(self, dataset):
        self.hring_data = dataset

    @staticmethod
    def select_weakest(section_set, section_name):
        weakest_cs = section_set[section_set.faalkans == section_set.faalkans.max()]
        if len(weakest_cs) > 1:
            warnings.warn(
                "Warning multiple weakest cs for section {}, returning first".format(
                    section_name
                )
            )
        return weakest_cs.index.values[-1]

    @staticmethod
    def select_closest(section, locs):
        # distance to midpoint of section:
        distance = np.abs(
            np.subtract(locs.m_value, np.mean([section.m_start, section.m_eind]))
        )
        return np.argmin(distance)

    @staticmethod
    def get_HRLocation(hrd_db_location, hlcd_db_location, hring_data):
        hrd_cnx = sqlite3.connect(hrd_db_location)
        hlcd_cnx = sqlite3.connect(hlcd_db_location)
        hrd_locs = pd.read_sql_query("SELECT * FROM HRDLocations", hrd_cnx)
        track_id = pd.read_sql_query("SELECT TrackID FROM General", hrd_cnx).values[0][0]
        hlcd_locs = pd.read_sql_query("SELECT * FROM Locations", hlcd_cnx)
        for count, line in hring_data.iterrows():
            try:
                hrd_location = hrd_locs.loc[
                    hrd_locs["Name"] == line["hr_koppel"]
                ]["HRDLocationId"].values[0]
            except IndexError:
                raise Exception(
                    "HRDLocationId niet gevonden voor {}. Check in de bekledingen CSV of de namen voor 'hr_koppel' wel "
                    "voorkomen in de database.".format(line["hr_koppel"])
                )

            hlcd_location = hlcd_locs.loc[
                (hlcd_locs["HRDLocationId"] == hrd_location) & (hlcd_locs["TrackId"] == track_id)]["LocationId"].values[0]
            if (not np.isnan(hring_data.loc[count, "hrlocation"])) & (hring_data.loc[count, "hrlocation"] != hlcd_location):
                raise Exception("HRLocation in input sheet is different from  HLCDLocation found in database for {}".format(line["hr_koppel"]))
            else:
                hring_data.loc[count, "hrlocation"] = hlcd_location

        hring_data["hrlocation"] = hring_data["hrlocation"].astype(np.int64)
        return hring_data

    def select_locs(self):
        # for each section
        indices = []
        for count, section in self.traject.iterrows():
            # get subset of GEKB locations
            subset = self.hring_data.loc[
                (self.hring_data.m_value > section.m_start)
                & (self.hring_data.m_value < section.m_eind)
            ]
            if self.kind == "weakest":
                # take closest if subset is empty
                if subset.shape[0] == 0:
                    index_val = self.select_closest(section, self.hring_data)
                else:
                    # get weakest
                    index_val = self.select_weakest(subset, section.vaknaam)
            else:
                raise Exception("No method found for kind: {}".format(self.kind))
            indices.append(index_val)
        self.hring_data = (
            self.hring_data.iloc[indices]
            .reset_index()
            .rename(columns={"index": "ID"})
            .drop_duplicates(subset=["ID"])
        )

    def verify_and_filter_columns(self):
        required_cols = [
            "doorsnede",
            "bovengrens",
            "ondergrens",
            "prfl_bestand",
            "orientatie",
            "dijkhoogte",
            "zodeklasse",
            "bovengrens_golfhoogteklasse",
            "kruindaling",
            "hrlocation",
        ]
        optional_cols = ["m_value", "faalkans", "LocationId"]
        if hasattr(self, "hring_data"):
            for column in self.hring_data.columns:
                if column not in required_cols + optional_cols:
                    self.hring_data = self.hring_data.drop(columns=column)
            for column in required_cols:
                if column not in self.hring_data.columns:
                    raise Exception(
                        "Column {} is required but not present in hring_data".format(
                            column
                        )
                    )
        else:
            raise Exception(
                "hring_data not present, verification of columns is not possible"
            )
        self.hring_data.reset_index(drop=True, inplace=True)
