import json
import pandas as pd
from pandas import json_normalize

def geojson_import(aoi_file):
    with open(aoi_file) as f:
        geometry = json.load(f)
    return geometry['features'][0]['geometry']


def api_response_to_clean_df(response):
    '''saves response as pandas dataframe'''
    df = json_normalize(response)
    
    # drop empty columns
    df = drop_columns(df)
    
    # clean df from empty values
    df = df_cleaner(df)

    return df

def df_cleaner(df):
    # replace NaN values with None (this also converts empty values which have a type to None)
    df = df.replace({None : None})
    return df

def build_timestamp(df, date_col):
    """Converts a column with a timestamp (in string format) into a column with the same name but in datetime format without timezone.

    Parameters
    ----------
    df : (Geo)DataFrame
        A pandas (Geo)DataFrame.
    date_col : str, optional
        Column name of timestamp column

    Returns
    -------
    GeoDataFrame
        A geopandas GeoDataFrame with the provided timestamp column in datetime format.
    """
    # convert the Timestamp column into a datetime object
    df[date_col] = pd.to_datetime(df[date_col], infer_datetime_format=True)

    # remove the timezone from the Timestamp column
    df[date_col] = df[date_col].dt.tz_localize(None)

    return df

def col_to_drop():
    return ['index', 
            '_permissions',
            'geometry.type',
            'geometry.coordinates']

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

# multiprocessing tool
import multiprocessing.pool

class ReportProcess(multiprocessing.Process):
    @property
    def daemon(self):
        return False

    @daemon.setter
    def daemon(self, value):
        pass


class ReportContext(type(multiprocessing.get_context())):
    Process = ReportProcess


class ReportPool(multiprocessing.pool.Pool):
    def __init__(self, *args, **kwargs):
        kwargs['context'] = ReportContext()
        super(ReportPool, self).__init__(*args, **kwargs)


