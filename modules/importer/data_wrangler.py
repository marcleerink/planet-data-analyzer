from pandas import json_normalize
from shapely.geometry import Polygon, MultiPolygon
import geopandas as gpd
from modules import utils
from modules.logger import LOGGER

def rename_columns(df):
    df.columns = df.columns.str.replace\
                    ('properties.', '', regex=False)
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
    '''convert nested lists to polygons, skip other geometries or emtpy rows'''
    
    if len(row) == 1:
        return Polygon(row[0])
    else:
        LOGGER.error('Couldnt transform geometry coordinates to polygon')
        return
    


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

    #only keep rows with Polygon geometries
    gdf = gdf[gdf.geom_type == 'Polygon']
    
    gdf = rename_columns(gdf)

    #cleans df from geometry rows with NaNs
    gdf = gdf.dropna(how='any', subset=['geom', 'clear_confidence_percent'])  

    # drop duplicates
    gdf = gdf.drop_duplicates(subset=['id'])
    
    return gdf


