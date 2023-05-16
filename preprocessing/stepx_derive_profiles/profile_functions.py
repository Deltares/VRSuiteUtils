import geopandas as gpd
from owslib.wfs import WebFeatureService
from shapely.ops import linemerge, substring, unary_union
from shapely.geometry import LineString, Point, Polygon, MultiPolygon
import numpy as np
import requests
import concurrent.futures

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

    def generate_cross_section(self, option,
                               cross_section_distance: int = 30,
                               foreshore_distance=50,
                               hinterland_distance=50):
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

        show_progress = 5 # show progress every 5%

        for i in range(len(m_value_bp)):
            if i%(np.ceil(len(m_value_bp)/(100/show_progress)))==0:
                print(i/(np.ceil(len(m_value_bp)/(100/show_progress)))*show_progress, "%")

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

            transect_point_right = create_transect_points(break_point,
                                                          dike_angle - .5 * np.pi,
                                                          foreshore_distance)
            transect_point_left = create_transect_points(break_point,
                                                         dike_angle + .5 * np.pi,
                                                         hinterland_distance)


            if option == "line":
                profile = self.get_values_polyline([[float(transect_point_right.x), float(transect_point_right.y)],
                                                    [float(transect_point_left.x), float(transect_point_left.y)]])
            elif option == "point":
                cs = create_cross_section_coordinates(transect_point_right, transect_point_left, step=1)
                cross_sections.append(cs)
                listed_coordinates = list(zip(list(cs.xy[0]), list(cs.xy[1])))
                profile = self.parallel_getvalue(listed_coordinates, 'AHN4_DTM_50cm') # ['AHN4_DTM_50cm', 'AHN4_DSM_50cm', 'AHN3_r', 'AHN3_i']
                profile_coords.append(listed_coordinates)

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

        return # self.m_values, self.cross_sections, self.break_points, self.profiles

    def get_values_polyline(self, coordinate_list: list, ):
        '''
        Service Description: Bereken het profiel van een input lijn op basis van het AHN4.
        Voor lijnen van 500 meter en korter wordt het AHN4 50cm ruwe bestand gebruikt en
        voor lijnen langer dan 500 meter wordt het AHN4 5 meter maaiveld bestand gebruikt.
        URL: https://ahn.arcgisonline.nl/arcgis/rest/services/Geoprocessing/Profile_AHN4/GPServer
        URL: https://ahn.arcgisonline.nl/arcgis/rest/services/Geoprocessing/Profile_AHN3/GPServer
        '''
        url = "https://ahn.arcgisonline.nl/arcgis/rest/services/Geoprocessing/Profile_AHN4/GPServer/Profile/execute"
        params = {"f": "json",
                  "env:outSR": 28992,
                  "InputLineFeatures": '{"fields":[{"name":"OID","type":"esriFieldTypeObjectID","alias":"OID"}],"geometryType":"esriGeometryPolyline","features":[{"geometry":{"spatialReference":{"wkid":28992},"paths":[' + str(
                      coordinate_list) + ']},"attributes":{"OID":1}}],"sr":{"wkid":28992}}',
                  "ProfileIDField": "OID",
                  "DEMResolution": "FINEST",
                  "MaximumSampleDistance": 0.5,
                  "MaximumSampleDistanceUnits": "Meters",
                  "returnZ": True,
                  "returnM": True}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            # try:
                # print(result['message'])
            # except:
                # print(result['messages'])
        else:
            print("Failed to get response from the API")
        xyzl_data = np.array(result['results'][0]['value']['features'][0]['geometry']['paths'][0])
        return xyzl_data

    def get_value(self, x: float, y: float, data_type: str, i: int, ):
        if i is None:
            i = 0
        pixelSize = 0.1
        url = f"https://ahn.arcgisonline.nl/arcgis/rest/services/AHNviewer/{data_type}/ImageServer/identify?f=json&" \
              f"geometry={{\"x\":{x},\"y\":{y},\"spatialReference\":{{\"wkid\":28992,\"latestWkid\":28992}}}}&" \
              f"returnGeometry=true&returnCatalogItems=true&geometryType=esriGeometryPoint&" \
              f"pixelSize={{\"x\":{pixelSize},\"y\":{pixelSize},\"spatialReference\":{{\"wkid\":28992,\"latestWkid\":28992}}}}&" \
              f"renderingRules=[{{\"rasterFunction\":\"Color Ramp D\"}}]"
        response = requests.get(url)
        data = response.json()
        if data["value"] == 'NoData':
            value = np.nan
        else:
            value = float(data["value"])
        return [x, y, value]

    def parallel_getvalue(self, coordinates: list, data_type: str):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=500) as executor:
            futures = [executor.submit(self.get_value, x, y, data_type, i, ) for i, (x, y) in enumerate(coordinates)]
        for future in futures:
            # Looping over the future list preserves the order of creation. No sorting required.
            results.append(future.result())
        return results


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