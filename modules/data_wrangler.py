from pandas import json_normalize
from shapely.geometry import Polygon, MultiPolygon
import geopandas as gpd
from modules.utils import drop_columns
from modules import utils

def list_to_polygon(row):
    '''convert nested lists to polygons'''
    # skip None values
    if row == None:
        return
    if len(row) == 1:
        g = Polygon(row[0])
    else:
        g = MultiPolygon([Polygon(r[0]) for r in row])
    
    return g

def wrangler(df):
    # convert geometries in nested list for input in GeoDataFrame
    df['geometry.coordinates'] = df['geometry.coordinates'].apply(
                                lambda row: list_to_polygon(row))

    gdf = gpd.GeoDataFrame(df, geometry=df['geometry.coordinates']).set_crs("epsg:4326").reset_index()

    gdf = drop_columns(gdf, ['index', 
                            '_permissions',
                            'geometry.type',
                            'geometry.coordinates'])
    
    return gdf


