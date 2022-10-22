from pandas import json_normalize
from shapely.geometry import Polygon
import geopandas as gpd
from modules.importer import utils
from modules.config import LOGGER
import pandas as pd

def build_timestamp(df, date_col):
    """Converts a column with a timestamp (in string format) into a column with the same name but in datetime format without timezone.

    """
    # convert the Timestamp column into a datetime object
    df[date_col] = pd.to_datetime(df[date_col], infer_datetime_format=True)

    # remove the timezone from the Timestamp column
    df[date_col] = df[date_col].dt.tz_localize(None)

    return df

def drop_columns(df, columns=None):
    '''Drops all empty columns in df.
    Optional. Drops columns passed as arguments'''
    
    #get list of all empty columns
    columns_to_drop = [col for col in df.columns if df[col].isnull().all()]
    
    # append columns from arg
    if columns:
        for col in columns:
            columns_to_drop.append(col)

    # drop all
    df.drop(columns_to_drop, axis=1, inplace=True, errors="ignore")

    return df

def move_column(df, cols_to_move=[], ref_col='', place='After'):
    
    cols = df.columns.tolist()
    if place == 'After':
        seg1 = cols[:list(cols).index(ref_col) + 1]
        seg2 = cols_to_move
    if place == 'Before':
        seg1 = cols[:list(cols).index(ref_col)]
        seg2 = cols_to_move + [ref_col]
    
    seg1 = [i for i in seg1 if i not in seg2]
    seg3 = [i for i in cols if i not in seg1 + seg2]
    
    return(df[seg1 + seg2 + seg3])
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
    '''convert nested lists to polygons, skip other geometries or empty rows'''
    if len(row) == 1:
        return Polygon(row[0])
    else:
        LOGGER.error(f'Couldnt transform geometry coordinates to polygon{row}')
        return



def df_cleaner(df):
    # replace NaN values with None (this also converts empty values which have a type to None)
    return df.replace({None : None})
    
def gdf_creater(df, geom_column):
    df = df.dropna(subset=geom_column, axis=0)
    # convert geometries from nested list for input in GeoDataFrame
    df[geom_column] = df[geom_column].apply(lambda row: list_to_polygon(row))
    
    gdf = gpd.GeoDataFrame(df, geometry=df[geom_column]).set_crs("epsg:4326").reset_index(drop=True)
    
    #only keep rows with Polygon geometries
    gdf = gdf[gdf.geom_type == 'Polygon']

    return gdf.rename_geometry('geom')

def api_response_to_clean_df(response):
    df = json_normalize(response)
    
    # clean df from empty values
    df = df_cleaner(df)

    return df

def drop_nan_rows_duplicates(df):
    df = df.dropna(how='any', subset=['geom'])  
    return df.drop_duplicates(subset=['id'])

def wrangler(items_list):
    
    # converts api response lists to cleaned dataframe
    df = api_response_to_clean_df(items_list)

    df = build_timestamp(df,'properties.acquired')
    df = build_timestamp(df,'properties.published')

    gdf = gdf_creater(df, 'geometry.coordinates')
    
    gdf = rename_columns(gdf)

    gdf = drop_nan_rows_duplicates(gdf)
    gdf['satellite'] = gdf['satellite'].str.title()
    
    return gdf


