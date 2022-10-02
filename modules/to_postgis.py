from functools import partial
from geoalchemy2 import Geometry
import pandas as pd
import geopandas as gpd
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon

from database.db import ENGINE
from database.psql_insert_copy import psql_insert_copy

def export_cities_table():
    gdf_cities = gpd.read_file('data/countries_cities_shp 2/ne_50m_populated_places.shp')
    gdf_cities.columns = gdf_cities.columns.str.lower()
    gdf_cities = gdf_cities.rename_geometry('geom')

    gdf_cities = gdf_cities[['name', 'sov_a3', 'geom']]
    gdf_cities = gdf_cities.dropna(subset=['geom', 'sov_a3'])
    gdf_cities = gdf_cities.rename(columns={'sov_a3' : 'country_iso3'})
    gdf_cities = gdf_cities.reset_index(names='id')

    psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    gdf_cities.to_sql(name='cities',
                        con=ENGINE,
                        schema='public',
                        method=psql_insert,
                        if_exists='append',
                        index=False,
                        dtype={'geom': Geometry('Point', srid=4326)})

def export_countries_table():
    gdf_countries = gpd.read_file('data/countries_cities_shp 2/ne_110m_admin_0_countries.shp')
    gdf_countries = gdf_countries.rename_geometry('geom')
    gdf_countries = gdf_countries[['sov_a3', 'name_sort', 'continent', 'geom']]
    gdf_countries = gdf_countries.rename(columns={'sov_a3' : 'iso3',
                                                'name_sort' : 'name',
                                                })
    gdf_countries = gdf_countries.dropna(subset=['geom', 'iso3'])

    gdf_countries['geom'] = [MultiPolygon([feature]) if isinstance(feature, Polygon) \
    else feature for feature in gdf_countries['geom']]
    
    print(gdf_countries.dtypes)
    psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    gdf_countries.to_sql(name='countries',
                        con=ENGINE,
                        schema='public',
                        method=psql_insert,
                        if_exists='append',
                        index=False,
                        dtype={'geom': Geometry('MultiPolygon', srid=4326)})

    

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


def postgis_exporter(gdf):
    
    export_countries_table()
    export_cities_table()
    export_satellites_table(gdf)
    export_item_types_table(gdf)
    export_asset_types_table(gdf)
    export_sat_images_table(gdf)