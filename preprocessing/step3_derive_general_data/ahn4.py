import geopandas as gpd
import numpy as np
import time
from owslib.wcs import WebCoverageService
from PIL import Image
from io import BytesIO
from shapely.geometry import LineString
from scipy.interpolate import griddata
import logging
from preprocessing.common_functions import log_and_raise_error
import tqdm

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

