import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
from shapely.ops import linemerge
from shapely.ops import split
from shapely.ops import nearest_points
from pathlib import Path


def count_buildings_per_vak(traject_name,
                            teenlijn_geojson,
                            vakindeling_geojson,
                            output_dir,
                            all_buildings_filename):

    # read teenlijn and vakindeling
    teenlijn_gdf = gpd.read_file(teenlijn_geojson)
    vakindeling_gdf = gpd.read_file(vakindeling_geojson)



    def create_bounding_box(input_shape, margin=250):
        """
        This creates a bounding box around the shape of the dike traject of interest. This bounding box is used to limit the
        amount of data obtained from importing data, limiting the computational time.
        """
        shape_bounds = input_shape.bounds

        xmin_bound = np.min(shape_bounds.minx) - margin
        ymin_bound = np.min(shape_bounds.miny) - margin
        xmax_bound = np.max(shape_bounds.maxx) + margin
        ymax_bound = np.max(shape_bounds.maxy) + margin

        return xmin_bound, ymin_bound, xmax_bound, ymax_bound

    # Create bounding box around dike segment
    bounding_box = create_bounding_box(vakindeling_gdf, margin=100)


    # determine the coordinates of where the dike segment splits into a new section. Make sure both the first and last
    # coordinate of the dike segment are included
    section_break_points = []
    for geometrie in vakindeling_gdf.geometry:
        section_break_points.append(geometrie.coords[0])
    # add last point of last section to section_break_points
    section_break_points.append(vakindeling_gdf.geometry.iloc[-1].coords[-1])

    # split teenlijn_gdf into separate lines, cut them where the line is closest to breakpoints of  of vakindeling_gdf
    # create a line with the geometry of the teenlijn

    line_teen = teenlijn_gdf.geometry[0]

    # for each breakpoint, find the nearest point on line, and split line at that point
    splits = []
    for breakpoint in section_break_points:
        bp = nearest_points(Point(breakpoint), line_teen)[1]
        splits.append(bp)

    # check if all break points are on the teenlijn, and give a warning if breakpoints are not on the line
    points_on_line = []
    for i in range(len(splits)):
        points_on_line.append(teenlijn_gdf.geometry.distance(splits[i]) < 1e-8)
    if np.sum(points_on_line) != len(points_on_line):
        print("not all the break points are on the line!")

    # split teenlijn_gdf into separate lines, cut the line between splits, give each line the vaknaam of the section in
    # vakindeling_gdf. Write the lines to a new geodataframe and save as geojson
    # create an empty geodataframe called teenvakken_gdf with column for vaknaam and geometry
    teenvakken_gdf = gpd.GeoDataFrame(columns=["vaknaam", "geometry"])

    result = split(line_teen, splits[1].buffer(1.0E-10))
    if len(result.geoms) == 3:
        line = linemerge([result.geoms[0],result.geoms[1]])
        remainder = result.geoms[2]
    elif len(result.geoms) == 2:
        line = result.geoms[0]
        remainder = result.geoms[1]
    elif len(result.geoms) == 1:
        line = None
        remainder = result.geoms[0]
    else:
        #remove parts where line_teen has crossed itself
        #raise Exception that there are unexpectedly many parts and that the teenlijn should be inspected for crossings
        raise Exception("Knippen van teenlijn levert onverwacht veel delen op. Controleer teenlijn op kruisingen.")

    teenvakken_gdf = gpd.GeoDataFrame(columns=["vaknaam", "geometry"])
    teenvakken_gdf = pd.concat([teenvakken_gdf, pd.DataFrame({"vaknaam": vakindeling_gdf.vaknaam[0], "geometry": line}, index=[0])])

    for i in range(2, len(splits)):
        result = split(remainder, splits[i].buffer(1.0E-10))
        if len(result.geoms) == 3:
            line = linemerge([result.geoms[0], result.geoms[1]])
            remainder = result.geoms[2]
        elif len(result.geoms) == 2:
            remainder = result.geoms[1]
        elif len(result.geoms) == 1:

            line = None
            remainder = result.geoms[0]

        teenvakken_gdf = pd.concat([teenvakken_gdf, pd.DataFrame({"vaknaam": vakindeling_gdf.vaknaam[i-1], "geometry": line}, index=[i-1])])

    # write to geojson with crs epsg:28992
    teenvakken_gdf.crs = "epsg:28992"
    teenvakken_gdf.to_file(output_dir.joinpath("teenlijn_vakindeling.geojson"), driver="GeoJSON")

    buildings_gdf = gpd.read_file(all_buildings_filename, bbox=bounding_box, engine="fiona")
    buildings_gdf.to_file(output_dir.joinpath("buildings_traject{0}.geojson".format(traject_name)), driver='GeoJSON')

    def count_buildings(building_shape, buffer_shape):
        #     counted_buildings = np.zeros(len(buffer_shape))
        sum_buildings = []
        for i in range(len(buffer_shape)):
            # filter out buffer_shape.loc[i].geometry.intersects(geom) is None
            if buffer_shape.loc[i].geometry is not None:
                # Counts buildings that intersect with the buffer:
                a = building_shape.geometry.apply(lambda geom: buffer_shape.loc[i].geometry.intersects(geom))
                sum_buildings.append(np.sum(a))
                print("DIJKVAK", buffer_shape.vaknaam[i], "contains", int(sum_buildings[i]), "buildings")
            else:
                sum_buildings.append(0)
                print("DIJKVAK", buffer_shape.vaknaam[i], "contains", int(sum_buildings[i]), "buildings")
        return sum_buildings

    def create_buffer(input_shapefile, buffer_width=100, direction=1):
        buffer_shape = input_shapefile.copy()
        buffer_width_dir = buffer_width * direction # takes into account the direction, 1 is right side, -1 is left side
        buffer_shape.geometry = buffer_shape.geometry.buffer(buffer_width_dir, single_sided=True)
        return buffer_shape

    # create range of buffers
    buffersize = np.arange(1, 51, 1)

    # create dataframe, with VAKNAAM as index. Each buffer size will be added as column
    building_matrix = pd.DataFrame(index=teenvakken_gdf.vaknaam)

    # determine amount of buildings in each dike section for each buffer size
    for i in range(len(buffersize)):
        print("Within", buffersize[i], "meters from the toe:")
        # creates a buffer along a shape with a given buffer size
        teenvak_buffer = create_buffer(teenvakken_gdf, buffersize[i])
        # count the amount of buildings within a buffer
        counted_buildings = count_buildings(buildings_gdf, teenvak_buffer)
        print()
        building_matrix["{}".format(buffersize[i])] = counted_buildings

    print(building_matrix)

    # save to csv
    building_matrix.to_csv(output_dir.joinpath("building_count_traject{0}.csv".format(traject_name)))


if __name__ == '__main__':
    # traject_name = "38-1"
    # teenlijn_geojson = Path(r"c:\VRM\Gegevens 38-1\profiles\teenlijn\teenlijn traject_38-1_line2.geojson")
    # vakindeling_geojson = Path(r"c:\VRM\test_vakindeling_workflow\result\Vakindeling_38-1_original.geojson")
    # intermediate_dir = Path(r"c:\VRM\Gegevens 38-1\profiles\teenlijn")
    # all_buildings_filename = Path("c://GIS//Achtergrond//bag-light.gpkg")

    count_buildings_per_vak(
        traject_name="38-1",
        teenlijn_geojson=Path(r"c:\VRM\Gegevens 38-1\profiles\teenlijn\teenlijn traject_38-1_line2.geojson"),
        vakindeling_geojson=Path(r"c:\VRM\test_vakindeling_workflow\result\Vakindeling_38-1_original.geojson"),
        output_dir=Path(r"c:\VRM\Gegevens 38-1\profiles\teenlijn"),
        all_buildings_filename=Path("c://GIS//Achtergrond//bag-light.gpkg"))
