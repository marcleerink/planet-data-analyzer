from pandas import json_normalize
from shapely.geometry import Polygon, MultiPolygon
import geopandas as gpd
from modules.utils import drop_columns
from modules import utils
import pandas as pd

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

def centroid_from_polygon(gdf):
    '''Gets centroid of polygon using Albers Equal Area proj'''
    # Project to equal-area projected crs
    gdf = gdf.to_crs({'proj':'cea'}) 

    # convert polygons to points and add as column
    gdf['centroid'] = gdf.centroid

    # Project back to WGS84 geographic crs
    gdf= gdf.to_crs(epsg=4326)
    gdf['centroid'] = gdf['centroid'].to_crs(epsg=4326)

    return gdf

def split_df_to_dict(df, column_name):
    unique_val = df[column_name].unique()

    df_dict = {elem : pd.DataFrame() for elem in unique_val}

    for key in df_dict.keys():
        df_dict[key] = df[:][df[column_name] == key]
    return df_dict

def gdf_creator(df, geom_column):
  
    # convert geometries from nested list for input in GeoDataFrame
    df[geom_column] = df[geom_column].apply(lambda row: list_to_polygon(row))
    
    gdf = gpd.GeoDataFrame(df, geometry=df[geom_column]).set_crs("epsg:4326").reset_index()

    # drop uneccesary colums and empty columns
    gdf = drop_columns(gdf, ['index', 
                            '_permissions',
                            'geometry.type',
                            geom_column])       
    #cleans df from geometry rows with NaNs
    gdf = gdf.dropna(how='any', subset=['geometry'])                
    return gdf

def wrangler(df):

    df = utils.build_timestamp(df,'properties.acquired')
    df = utils.build_timestamp(df,'properties.published')

    # # split df based on satellite provider and store in dict with satellite providers as keys
    # df_dict = split_df_to_dict(df, 'properties.provider')

    gdf = gdf_creator(df, 'geometry.coordinates')
    
    return gdf


