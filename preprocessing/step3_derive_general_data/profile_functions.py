import geopandas as gpd
import numpy as np
from owslib.wfs import WebFeatureService
from preprocessing.step3_derive_general_data.ahn4 import AHN4

from shapely.geometry import LineString, Point
from shapely import geometry
import logging
from preprocessing.common_functions import log_and_raise_error
import tqdm

class Traject:

    def __init__(self, traject_name):
        self.name = traject_name
        logging.info("Dijktraject :", self.name)


    def get_traject_data(self, NBWP_shape_path=False):
        if not NBWP_shape_path:
            # get from WFS
            wfs_nbpw = WebFeatureService(url='https://geo.rijkswaterstaat.nl/services/ogc/wvp/ows/wfs?version=1.1.0&request=GetCapabilities&Service=WFS',
                                         version='1.1.0')
            NBPW = gpd.read_file(wfs_nbpw.getfeature('dijktrajecten', outputFormat='json'))
            logging.info("NBPW geladen van WFS")
        else:
            NBPW = gpd.read_file(NBWP_shape_path)
            logging.info(f"NBPW geladen van lokale shape {NBWP_shape_path}")

        self.traject_shape = NBPW.loc[NBPW.TRAJECT_ID == self.name].reset_index(drop=True)

        self.traject_shape = self.traject_shape[
            ["TRAJECT_ID", "NORM_SW", "NORM_OG", "geometry"]
        ]
        self.traject_shape = self.traject_shape.explode(index_parts=True)
        if len(self.traject_shape) > 1:
            log_and_raise_error("NBPW shape geeft meer dan 1 geometrie. Controleer de shape.",
                                ValueError)
            

        self.length = self.traject_shape.geometry[0].length[0]
        logging.info(f"Totale lengte traject: {self.length}")
        return self.traject_shape, self.length

    def flip_traject(self):
        """function that reverts a line (self.NBPW_shape['geometry']) that contains a linestring of x and y coordinates.
         In other words: the function draws the line backwards. The geometry is updated in place.
        """
        self.traject_shape["geometry"] = self.traject_shape["geometry"].apply(
            lambda x: geometry.LineString(list(x.coords)[::-1]),
            lambda y: geometry.LineString(list(y.coords)[::-1]),
        )

    def generate_cross_section(self,
                               cross_section_distance: int = 25,
                               foreshore_distance: int = 50,
                               hinterland_distance: int = 75,
                               flip_water_side: bool = False,
                               ):
        # interpolate trajectory on regular intervals:
        break_points = []
        cross_sections = []
        profiles = []
        foreshore_coords = []
        hinterland_coords = []
        profile_coords = []

        # determine the m-values of the cross section break points
        m_value_bp = np.arange(0, self.length, cross_section_distance)
        if m_value_bp[-1] < self.length:
            m_value_bp = np.append(m_value_bp, self.length)

        # determine the angle of the dike, and the location of the foreshore and hinterland points
        # for each break point. Then create the cross section and get the profile from the AHN.
        for i, m_value in tqdm.tqdm(enumerate(m_value_bp), total=len(m_value_bp), desc = "Aanmaken dwarsprofielen uit AHN4"):
            if m_value < 1:
                dike_angle_points = [self.traject_shape.geometry[0].interpolate(m_value),
                                     self.traject_shape.geometry[0].interpolate(m_value+1)]
            elif (m_value >= 1) & (m_value <= self.length-1):
                dike_angle_points = [self.traject_shape.geometry[0].interpolate(m_value-1),
                                     self.traject_shape.geometry[0].interpolate(m_value + 1)]
            elif m_value > self.length-1:
                dike_angle_points = [self.traject_shape.geometry[0].interpolate(m_value-1),
                                     self.traject_shape.geometry[0].interpolate(m_value)]

            break_point = self.traject_shape.geometry[0].interpolate(m_value)
            dike_angle = Traject.determine_dike_angle(dike_angle_points[0], dike_angle_points[1])

            if flip_water_side:
                transect_point_right = Traject.create_transect_points(break_point,
                                                              dike_angle + .5 * np.pi,
                                                              foreshore_distance)
                transect_point_left = Traject.create_transect_points(break_point,
                                                             dike_angle - .5 * np.pi,
                                                             hinterland_distance)
            else:
                transect_point_right = Traject.create_transect_points(break_point,
                                                              dike_angle - .5 * np.pi,
                                                              foreshore_distance)
                transect_point_left = Traject.create_transect_points(break_point,
                                                             dike_angle + .5 * np.pi,
                                                             hinterland_distance)

            ahn4 = AHN4()
            transect = LineString([[float(transect_point_right.x), float(transect_point_right.y)],
                                                [float(transect_point_left.x), float(transect_point_left.y)]])
            profile = ahn4.get_elevation_from_line(transect, raster='dtm_05m', correction=foreshore_distance)

            break_points.append(break_point)
            profiles.append(profile)

            foreshore_point = transect_point_right
            hinterland_point = transect_point_left

            foreshore_coords.append(foreshore_point)
            hinterland_coords.append(hinterland_point)

        self.foreshore_coords = foreshore_coords
        self.hinterland_coords = hinterland_coords
        self.m_values = m_value_bp
        self.cross_sections = cross_sections
        self.break_points = break_points
        self.profiles = profiles
        self.profile_coords = profile_coords
        return
    
    @staticmethod
    def determine_dike_angle(point1, point2):
        """Calculate angle between two points in radians and degrees.
        East is 0, North is 0.5 pi, West is 1 pi, South is 1.5 pi"""

        angle = np.arctan2(point2.y - point1.y, point2.x - point1.x)
        return angle

    @staticmethod
    # create a function that draws points with a given angle and radius
    def create_transect_points(point, angle, radius):
        """Draw point with a given with a given angle and radius"""
        x = point.x + radius * np.cos(angle)
        y = point.y + radius * np.sin(angle)
        return Point(x, y)

    @staticmethod
    # create function that creates a line between two points and returns a linestring with points at each given step
    def create_cross_section_coordinates(transect_point1, transect_point2, step):
        """Create a line between two points and return a linestring with points at each given step"""
        temp_line = LineString([transect_point1, transect_point2])
        distance = temp_line.length
        x_coords = np.linspace(transect_point1.x, transect_point2.x, int(distance / step) + 1)
        y_coords = np.linspace(transect_point1.y, transect_point2.y, int(distance / step) + 1)
        return LineString([Point(x, y) for x, y in zip(x_coords, y_coords)])
