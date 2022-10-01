from pandas import json_normalize
from shapely.geometry import Polygon, MultiPolygon
import geopandas as gpd
from modules import utils
import pandas as pd

def rename_columns(df):

    df.columns = df.columns.str.replace('properties.', '')
    columns = {
        'acquired' : 'time_acquired',
        'pixel_resolution' : 'pixel_res',
        'provider' : 'satellite',
        'satellite_id' : 'sat_id',
        'item_type' : 'item_type_id',
    }
    df = df.rename(columns=columns)
    return df
    

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


def gdf_creator(df, geom_column):
    df = df.dropna(subset=geom_column, axis=0)
    # convert geometries from nested list for input in GeoDataFrame
    df[geom_column] = df[geom_column].apply(lambda row: list_to_polygon(row))
    
    gdf = gpd.GeoDataFrame(df, geometry=df[geom_column]).set_crs("epsg:4326").reset_index(drop=True)
    gdf = gdf.rename_geometry('geom')
              
    return gdf

def wrangler(df):

    df = utils.build_timestamp(df,'properties.acquired')
    df = utils.build_timestamp(df,'properties.published')

    gdf = gdf_creator(df, 'geometry.coordinates')

    
    gdf = rename_columns(gdf)

    #cleans df from geometry rows with NaNs
    gdf = gdf.dropna(how='any', subset=['geom', 'clear_confidence_percent'])  

    # drop duplicates
    gdf = gdf.drop_duplicates(subset=['id'])
    
    return gdf


