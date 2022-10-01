from functools import partial
from geoalchemy2 import Geometry
import pandas as pd
import geopandas as gpd

from database.db import ENGINE
from database.psql_insert_copy import psql_insert_copy


def export_asset_types_table(gdf):
    asset_types_df = gdf['assets']
    asset_types_df = pd.DataFrame(set(asset_types_df.explode().to_list()), columns=['id'])

    psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    asset_types_df.to_sql(name='asset_types', 
                        con=ENGINE, 
                        schema='public', 
                        method=psql_insert, 
                        if_exists='append', 
                        index=False)

def export_item_types_table(gdf):
    item_types_df = gdf[['item_type_id', 'sat_id']]
    item_types_df = item_types_df.drop_duplicates(subset='item_type_id')
    item_types_df = item_types_df.dropna(subset='item_type_id')
    item_types_df = item_types_df.rename(columns={'item_type_id' : 'id'})

    psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    item_types_df.to_sql(name='item_types', 
                        con=ENGINE, 
                        schema='public', 
                        method=psql_insert, 
                        if_exists='append', 
                        index=False)
    

def export_satellites_table(gdf):
    satellites_df = gdf[['sat_id', 'satellite', 'pixel_res']]
    satellites_df = satellites_df.drop_duplicates(subset='sat_id')
    satellites_df = satellites_df.dropna(subset='sat_id')
    satellites_df = satellites_df.rename(columns={'sat_id' : 'id', 'satellite' : 'name'})

    psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    satellites_df.to_sql(name='satellites', 
                        con=ENGINE, 
                        schema='public',
                        method=psql_insert,
                        if_exists='append', 
                        index=False)

def export_sat_images_table(gdf):
    sat_image_gdf = gdf[['id', 'clear_confidence_percent', 'cloud_cover', 'pixel_res', 'time_acquired', 'geom', 'sat_id', 'item_type_id']]
    psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    sat_image_gdf.to_sql(name='sat_images',
                        con=ENGINE,
                        schema='public',
                        method=psql_insert,
                        if_exists='append',
                        index=False,
                        dtype={'geom': Geometry('Polygon', srid=4326)})

def export_countries_table():
    gdf_world = gpd.read_file('data/World_Countries_(Generalized).geojson')
    gdf_world = gdf_world.rename_geometry('geom')
    gdf_world = gdf_world[['COUNTRY', 'ISO', 'geom']]
    gdf_world = gdf_world.rename(columns={'ISO' : 'iso',
                                        'COUNTRY' : 'formal_name'})
    psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    gdf_world.to_sql(name='countries',
                        con=ENGINE,
                        schema='public',
                        method=psql_insert,
                        if_exists='append',
                        index=False,
                        dtype={'geom': Geometry('MultiPolygon', srid=4326)})

    
    

def postgis_exporter(gdf):
    export_countries_table()
    export_satellites_table(gdf)
    export_item_types_table(gdf)
    export_asset_types_table(gdf)
    export_sat_images_table(gdf)