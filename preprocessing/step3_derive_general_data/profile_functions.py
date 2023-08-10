import geopandas as gpd
import numpy as np
import time
from owslib.wfs import WebFeatureService
# from wcf_ahn4 import AHN4
from owslib.wcs import WebCoverageService
from PIL import Image
from io import BytesIO
from shapely.geometry import LineString, Point
from scipy.interpolate import griddata


class Traject:

    def __init__(self, traject_name):
        self.name = traject_name
        print("Dike traject =", self.name)


    def get_traject_data(self, NBWP_shape_path=False):
        if not NBWP_shape_path:
            # get from WFS
            wfs_nbpw = WebFeatureService(url='https://waterveiligheidsportaal.nl/geoserver/nbpw/ows/wfs',
                                         version='1.1.0')
            NBPW = gpd.read_file(wfs_nbpw.getfeature('nbpw:dijktrajecten', outputFormat='json'))
        else:
            NBPW = gpd.read_file(NBWP_shape_path)

        self.traject_shape = NBPW.loc[NBPW.TRAJECT_ID == self.name].reset_index(drop=True)
        # self.traject_shape.geometry[0] = linemerge(self.traject_shape.geometry[0])
        self.length = self.traject_shape.geometry[0].length
        print("Total traject length =", self.length)
        return self.traject_shape, self.length

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
        m_value_bp = np.arange(0, self.traject_shape.geometry[0].length, cross_section_distance)
        if m_value_bp[-1] < self.length:
            m_value_bp = np.append(m_value_bp, self.length)

        # determine the angle of the dike, and the location of the foreshore and hinterland points
        # for each break point. Then create the cross section and get the profile from the AHN.
        for i in range(len(m_value_bp)):
            if m_value_bp[i] < 1:
                dike_angle_points = [self.traject_shape.geometry[0].interpolate(m_value_bp[i]),
                                     self.traject_shape.geometry[0].interpolate(m_value_bp[i]+1)]
            elif (m_value_bp[i] >= 1) & (m_value_bp[i] <= self.length-1):
                dike_angle_points = [self.traject_shape.geometry[0].interpolate(m_value_bp[i]-1),
                                     self.traject_shape.geometry[0].interpolate(m_value_bp[i] + 1)]
            elif m_value_bp[i] > self.length-1:
                dike_angle_points = [self.traject_shape.geometry[0].interpolate(m_value_bp[i]-1),
                                     self.traject_shape.geometry[0].interpolate(m_value_bp[i])]

            break_point = self.traject_shape.geometry[0].interpolate(m_value_bp[i])
            dike_angle = determine_dike_angle(dike_angle_points[0], dike_angle_points[1])

            if flip_water_side:
                transect_point_right = create_transect_points(break_point,
                                                              dike_angle + .5 * np.pi,
                                                              foreshore_distance)
                transect_point_left = create_transect_points(break_point,
                                                             dike_angle - .5 * np.pi,
                                                             hinterland_distance)
            else:
                transect_point_right = create_transect_points(break_point,
                                                              dike_angle - .5 * np.pi,
                                                              foreshore_distance)
                transect_point_left = create_transect_points(break_point,
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

class AHN4:

    def __init__(self):
        self.wcs = WebCoverageService('https://service.pdok.nl/rws/ahn/wcs/v1_0?SERVICE=WCS',
                                      version='1.0.0')  # Connect to the WCS service
        self.coverage_id = list(self.wcs.contents)  # Identify which layers are present
        self.resolution = 0.5  # Resolution of the raster

    def get_elevation_from_line(self, linestring, raster=None, correction=0.0):
        # correction is used if the distance L doesn't start at 0.0 but at a certain value
        x1, y1 = linestring.coords[0]
        x2, y2 = linestring.coords[1]

        margin = 2.5 # adds margin to bbox to prevent errors if linestring is close to the edge of the raster
        bbox = (min(x1,x2)-margin,
                min(y1,y2)-margin,
                max(x1,x2)+margin,
                max(y1,y2)+margin)

        data, (X, Y) = self.get_raster_from_wcs(bbox, raster=raster)
        density = 0.5
        linestring = LineString([linestring.interpolate(density * i) for i in np.arange(0, linestring.length // density + 1)])

        L = np.array([np.sqrt((x1 - x) ** 2 + (y1 - y) ** 2) for (x, y) in linestring.coords])-correction
        # print(data)
        Z = griddata(np.column_stack((X.flatten(), Y.flatten())), data.flatten(),
                     [(x, y) for (x, y) in linestring.coords], method='linear')
        # print(Z)

        return L, Z

    def get_raster_from_wcs(self, bbox, raster=None, getmap=False):
        if raster is None: # if None specified, the first raster is taken
            raster = self.coverage_id[0]
        elif type(raster) == int: #  user can also specify another value ['dsm_05m', 'dtm_05m']
            raster = self.coverage_id[raster]

        if bbox[2]-bbox[0]==0 or bbox[3]-bbox[1]==0:
            print('No 1D rasters are allowed. Increase the xmax or ymax of the boundingbox.')
            ValueError

        start_time = time.time()

        # InterpolationSupported: NEAREST, AVERAGE, BILINEAR
        output = self.wcs.getCoverage(identifier=raster,bbox=bbox,resx=self.resolution,resy=self.resolution,
                                      format='GeoTIFF',crs='EPSG:28992',interpolation='AVERAGE')

        try: # to get the coverage data as a numpy array
            im = Image.open(BytesIO(output.read()))
            data = np.array(im)
            data[data>9999]=np.nan
        except: # if the output is not a correct geotiff float file
            print(output.read())
            data = None

        x = np.resize( np.arange(bbox[0],bbox[2], self.resolution) , data.shape[1] )
        y = np.resize( np.arange(bbox[1],bbox[3], self.resolution) , data.shape[0] )

        duration = time.time() - start_time
        # print(duration)

        return data, np.meshgrid(x, np.flip(y))

def determine_dike_angle(point1, point2):
    """Calculate angle between two points in radians and degrees.
    East is 0, North is 0.5 pi, West is 1 pi, South is 1.5 pi"""

    angle = np.arctan2(point2.y - point1.y, point2.x - point1.x)
    return angle

# create a function that draws points with a given angle and radius
def create_transect_points(point, angle, radius):
    """Draw point with a given with a given angle and radius"""
    x = point.x + radius * np.cos(angle)
    y = point.y + radius * np.sin(angle)
    return Point(x, y)

# create function that creates a line between two points and returns a linestring with points at each given step
def create_cross_section_coordinates(transect_point1, transect_point2, step):
    """Create a line between two points and return a linestring with points at each given step"""
    temp_line = LineString([transect_point1, transect_point2])
    distance = temp_line.length
    x_coords = np.linspace(transect_point1.x, transect_point2.x, int(distance / step) + 1)
    y_coords = np.linspace(transect_point1.y, transect_point2.y, int(distance / step) + 1)
    return LineString([Point(x, y) for x, y in zip(x_coords, y_coords)])