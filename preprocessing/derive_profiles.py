import geopandas as gpd
from owslib.wfs import WebFeatureService
from shapely import geometry, ops
from typing import List, Tuple, Union, Dict, Optional
from pathlib import Path
from shapely.geometry import LineString, Point, Polygon, MultiPolygon
from shapely.ops import linemerge, substring, unary_union
import numpy as np
from pandas import DataFrame
import matplotlib.pyplot as plt

def get_traject_shape_from_NBPW(traject,NBWP_shape_path=False):
    if not NBWP_shape_path:
        #get from WFS
        wfs_nbpw = WebFeatureService(url='https://waterveiligheidsportaal.nl/geoserver/nbpw/ows/wfs', version='1.1.0')
        NBPW = gpd.read_file(wfs_nbpw.getfeature('nbpw:dijktrajecten',outputFormat='json'))
    else:
        NBPW = gpd.read_file(NBWP_shape_path)

    traject_shape = NBPW.loc[NBPW.TRAJECT_ID==traject].reset_index(drop=True)
    return traject_shape

traject = get_traject_shape_from_NBPW("38-1")

traject.geometry[0] = linemerge(traject.geometry[0])



class Trace:
    def __init__(self, trajectory: List[Tuple[float, float]]):
        self.trajectory: List = trajectory  # x/y coordinates

        self.clip_binnen_and_buiten_lines()  # Set the attributes BUK, BIK, BIT, BUT as LineStrings

    def __repr__(self):
        return f"Dijkvak {self.vak_id}"

    @classmethod
    def from_geojson(cls, path_geojson: Path, vak_id: Union[int, List[int]], densify: bool = False):
        """
        Build a Dijkvak object from a shapefile with either a single vak ID or multiple vak id combined
        :param shape: shape file "Dijkvakindeling 2019" from SAFE GIS portal containing information of all the vakken.
        :param vak_id: ID of list of vak IDs present in the shapefile which constitutes the dijkvak
        :param: if False, the trajectory is as dense as the original linestring from the shapefile. If True, the
        trajectory is densified.
        :return: Instanciation of the class Dijkvak
        """
        df = geopandas.read_file(path_geojson)

        if isinstance(vak_id, int):
            row = df.loc[df['dijkvak'] == str(vak_id)]
            points = [(pt[1], pt[0]) for pt in row['geometry'].iloc[0].coords]

        elif isinstance(vak_id, list):
            # Return row of the vak_id:
            vak_id_str = [str(id) for id in vak_id]  # comparison of IDs with string!
            subdf = df.loc[df['dijkvak'].isin(vak_id_str)]
            list_lines = subdf['geometry'].tolist()
            line = linemerge(list_lines)  # Merge all selected vak into a single linestring
            points = [(lat, lon) for lon, lat in zip(*line.coords.xy)]
        else:
            raise TypeError("vak_id must be of type List[int] or int")

        if densify:
            # if the initial trajectory needs to be densified
            linestring_rd = LineString([GWSRDConvertor().to_rd(latin=point[0], lonin=point[1]) for point in points])
            densified_linestring = densify_linestring(linestring_rd)
            return Trace(trajectory=[GWSRDConvertor().to_wgs(x, y) for x, y in zip(*densified_linestring.coords.xy)],
                         vak_id=vak_id)

        # else use the base trajectory
        return Trace(points, vak_id)

    def clip_binnen_and_buiten_lines(self) -> Tuple[LineString, LineString, LineString, LineString]:
        """"
        Clip the Binnenkruinlijn, Buitenkruinlijn, Binnenteen and Buitenteen to the trajectory of the dijkvak
        :return: Tuple of the clipped linestrings in the order BUK, BIK, BIT, BUT in WGS coordinates
        """
        path_BIK = Path(__file__).parent.parent / 'shapefiles' / 'Binnenkruinlijn.json'
        path_BUK = Path(__file__).parent.parent / 'shapefiles' / 'Buitenkruinlijn (WSRL).json'
        path_BIT = Path(__file__).parent.parent / 'shapefiles' / 'Binnenteen aangepast scope.json'
        path_BUT = Path(__file__).parent.parent / 'shapefiles' / 'Buitenteen aangepast scope.json'

        ls_BUK = LineString([GWSRDConvertor().to_rd(latin=point[1], lonin=point[0]) for point in
                             merge_linestrings_from_multistrings(
                                 geopandas.read_file(path_BUK)['geometry'].iloc[0]).coords])
        ls_BIK = LineString([GWSRDConvertor().to_rd(latin=point[1], lonin=point[0]) for point in
                             merge_linestrings_from_multistrings(
                                 geopandas.read_file(path_BIK)['geometry'].iloc[0]).coords])
        ls_BIT = LineString([GWSRDConvertor().to_rd(latin=point[1], lonin=point[0]) for point in
                             merge_linestrings_from_multistrings(
                                 geopandas.read_file(path_BIT)['geometry'].iloc[0]).coords])
        ls_BUT = LineString([GWSRDConvertor().to_rd(latin=point[1], lonin=point[0]) for point in
                             merge_linestrings_from_multistrings(
                                 geopandas.read_file(path_BUT)['geometry'].iloc[0]).coords])

        clipping_polygon = LineString(self.trajectory_rd).buffer(50)
        ls_BIK_clipped = ls_BIK.intersection(clipping_polygon)
        ls_BUK_clipped = ls_BUK.intersection(clipping_polygon)
        ls_BIT_clipped = merge_linestrings_from_multistrings(
            ls_BIT.intersection(clipping_polygon))  # The intersection sometimes return a multistring here
        ls_BUT_clipped = ls_BUT.intersection(clipping_polygon)

        self.BIK_rd = ls_BIK_clipped
        self.BUK_rd = ls_BUK_clipped
        self.BIT_rd = ls_BIT_clipped
        self.BUT_rd = ls_BUT_clipped

        self.BIK = LineString([GWSRDConvertor().to_wgs(xin=point[0], yin=point[1]) for point in ls_BIK_clipped.coords])
        self.BUK = LineString([GWSRDConvertor().to_wgs(xin=point[0], yin=point[1]) for point in ls_BUK_clipped.coords])
        self.BIT = LineString([GWSRDConvertor().to_wgs(xin=point[0], yin=point[1]) for point in ls_BIT_clipped.coords])
        self.BUT = LineString([GWSRDConvertor().to_wgs(xin=point[0], yin=point[1]) for point in ls_BUT_clipped.coords])
        return ls_BUK_clipped, ls_BIK_clipped, ls_BIT_clipped, ls_BUT_clipped

    def generate_cross_section(self, number_cross_section: int = 10) -> List['CrossSection']:
        # interpolate trajectory on regular intervals:
        cross_sections = []
        for i in range(10, int(LineString(self.trajectory_rd).length) - 1, number_cross_section):
            point = LineString(self.trajectory_rd).interpolate(i)
            try:
                cs = CrossSection(self, point, f"{i}")
                cross_sections.append(cs)
            except AttributeError:
                continue
        return cross_sections

class CrossSection:

    def __init__(self, trace: Trace, BUK_point: Point, name: str, right_extension: float = 50,
                 left_extension: float = 50, ):
        """

        :param trace: trace from which originates the cross-section
        :param BUK_point: shapely Point on the trace where the cross-section is located in RD coordinates
        :param name:
        """
        self.trace = trace
        self.name = name
        self.reference_point_rd = BUK_point
        self.right_extension = right_extension
        self.left_extension = - left_extension
        dijkvak_traj = LineString(trace.trajectory_rd)

        projected_distance_to_ls = dijkvak_traj.project(BUK_point)
        dijkvak_traj_sub = substring(dijkvak_traj, start_dist=0, end_dist=projected_distance_to_ls)

        cross_section_coord = self.get_perpendicular_cross_section(dijkvak_traj_sub, hinterland_length=right_extension,
                                                                   foreland_length=left_extension,
                                                                   distance_between_points=2)
        self.coord: List = cross_section_coord
        self.coord_rd: List = [GWSRDConvertor().to_rd(latin=point[0], lonin=point[1]) for point in self.coord]

    @classmethod
    def from_end_start(cls):
        raise NotImplementedError

    def plot_map(self):
        mapbox_access_token = open(Path(__file__).parent / "mapbox_token.txt").read()

        fig = go.Figure()
        fig.add_trace(go.Scattermapbox(
            name="Cross_section",
            lat=[pt[0] for pt in self.coord],
            lon=[pt[1] for pt in self.coord],
            mode='lines',
        ))
        fig.update_layout(mapbox=dict(
            accesstoken=mapbox_access_token,
            center=dict(lat=self.coord[0][0], lon=self.coord[0][1]),
            zoom=15,
        ))

        fig.show()

    @property
    def BIK(self) -> Point:
        BIK_line = self.trace.BIK
        return LineString(self.coord).intersection(BIK_line)

    @property
    def BIK_rd(self) -> Point:
        return Point(GWSRDConvertor().to_rd(latin=self.BIK.x, lonin=self.BIK.y))

    @property
    def BIK_local(self) -> float:
        return LineString([self.reference_point_rd, self.BIK_rd]).length

    @property
    def BUT(self) -> Point:
        BUT_line = self.trace.BUT
        return LineString(self.coord).intersection(BUT_line)

    @property
    def BUT_rd(self) -> Point:
        return Point(GWSRDConvertor().to_rd(latin=self.BUT.x, lonin=self.BUT.y))

    @property
    def BUT_local(self) -> float:
        """Return the distance of the Buitenteen from the reference point of the cross-section (is negative)"""

        return - LineString([self.reference_point_rd, self.BUT_rd]).length

    @property
    def BIT(self) -> Point:
        BIT_line = self.trace.BIT
        return LineString(self.coord).intersection(BIT_line)

    @property
    def BIT_rd(self) -> Point:
        return Point(GWSRDConvertor().to_rd(latin=self.BIT.x, lonin=self.BIT.y))

    @property
    def BIT_local(self) -> float:
        return LineString([self.reference_point_rd, self.BIT_rd]).length

    # @property
    # def BUK(self) -> Point:

    @property
    def BUK_rd(self) -> Point:
        return self.reference_point_rd

    @property
    def BUK_local(self) -> float:
        return 0

    @property
    def distance_from_start_vak(self) -> float:
        """Return the distance between the reference point of the cross-section and the start of the dijkvak"""
        return LineString(self.trace.trajectory_rd).project(self.reference_point_rd)

    @property
    def direction(self) -> np.array:
        """Return the (normalized) direction vector of the cross-section"""
        start_cs, end_cs = self.coord_rd[0], self.coord_rd[-1]
        direction = np.array([end_cs[0] - start_cs[0], end_cs[1] - start_cs[1]])
        return direction / np.linalg.norm(direction)

    @property
    def angle(self) -> float:
        """Return the angle (-pi, pi] between the unit vector u(1,0) and the direction of the cross-section, positive
        angle is counted CCW, negative angle is CW"""
        return np.angle(self.direction[0] + 1j * self.direction[1])

    def get_local_coord(self, coord_rd) -> List[float]:
        """Return a list of local 1D coordinates of the cross-section, along its trajectory. Rotation + translation"""
        linestring_rd = LineString(coord_rd)
        rotated_ls = rotate(linestring_rd, - self.angle,
                            origin=self.reference_point_rd, use_radians=True)
        return [(x - self.reference_point_rd.x) for x, _ in zip(*rotated_ls.coords.xy)]

    def get_elevation(self, coord_rd: List) -> List[float]:
        ahn_data = parallel_getvalue(coord_rd, data_type='AHN4_DTM_50cm')
        return [pt[2] for pt in ahn_data]


    @staticmethod
    def get_perpendicular_cross_section(dijkvak_traj_sub: LineString, hinterland_length: float,
                                        foreland_length: float, distance_between_points: float = 2) -> List:
        # TODO: How to determine if hinterland is left or right automatically? # dijkvak.trajectory_rd.reverse()
        left = dijkvak_traj_sub.parallel_offset(hinterland_length, 'left')
        right = dijkvak_traj_sub.parallel_offset(foreland_length, 'right')
        c = left.boundary.geoms[1]
        d = right.boundary.geoms[1]
        cross_section_ls = LineString([c, d])
        cross_section_coord = [GWSRDConvertor().to_wgs(xin=x, yin=y) for x, y in
                               zip(*densify_linestring(cross_section_ls,
                                                       distance_between_points).coords.xy)]  # only 2 points at this stages
        # The method above seems to create cross-section with the following orientation: voorland -> Hinterland.
        # This needs to be swapped, hence .reverse()
        cross_section_coord.reverse()

        return cross_section_coord

    @property
    def get_df_cross_section(self) -> DataFrame:
        """Return a dataframe with the cross-section coordinates and local coordinates"""
        df_points = DataFrame({'lat': [pt[0] for pt in self.coord],
                               'lon': [pt[1] for pt in self.coord],
                               'x': [pt[0] for pt in self.coord_rd],
                               'y': [pt[1] for pt in self.coord_rd],
                               'dist_local': self.get_local_coord(self.coord_rd)})
        df_char_points = DataFrame({'lat': [self.BUT.x, self.BIK.x, self.BIT.x, None],
                                    'lon': [self.BUT.y, self.BIK.y, self.BIT.y, None],
                                    'x': [self.BUT_rd.x, self.BIK_rd.x, self.BIT_rd.x, self.BUK_rd.x],
                                    'y': [self.BUT_rd.y, self.BIK_rd.y, self.BIT_rd.y, self.BUK_rd.y],
                                    'dist_local': [self.BUT_local, self.BIK_local, self.BIT_local, self.BUK_local]})

        df_points = pd.concat([df_points, df_char_points], ignore_index=True).sort_values(by='dist_local')
        elevation_list = [z if (z > -100) & (z < 100) else None for z in
                          self.get_elevation(df_points[['x', 'y']].values.tolist())]
        # Interpolate nan values:

        df_points['z'] = pd.Series(elevation_list).interpolate().to_list()
        self.BUT_z = df_points[df_points['dist_local'] == self.BUT_local]['z'].values[0]
        self.BIK_z = df_points[df_points['dist_local'] == self.BIK_local]['z'].values[0]
        self.BIT_z = df_points[df_points['dist_local'] == self.BIT_local]['z'].values[0]
        self.BUK_z = df_points[df_points['dist_local'] == self.BUK_local]['z'].values[0]
        self.left = df_points['dist_local'].min()
        self.right = df_points['dist_local'].max()
        self.top_profile = [(x, y) for x, y in zip(df_points['dist_local'], df_points['z'])]

        return df_points

def generate_and_run_cross_section(traject):
    trace = Trace(traject)
    cs_collection = trace.generate_cross_section()

    for cs in cs_collection:
        # if float(cs.name) > 1540 or float(cs.name) < 410:
        # if float(cs.name) != 1460:  #1460 is an example of a troublesome schematization: bad connectivity of the polygons
        #     continue
        # try:
        if float(cs.name) == 1000:
            cs.plot_plotly_profile()
            cs.d_stability_profile()
        # stop
        # except:
        #     print(f"{cs.name} failed")

generate_and_run_cross_section(traject)
