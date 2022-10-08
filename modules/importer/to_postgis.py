from functools import partial
from geoalchemy2 import Geometry
import pandas as pd
import geopandas as gpd
from shapely.geometry.linestring import LineString
from shapely.geometry.multilinestring import MultiLineString
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from modules.database.db import ENGINE, SatImage, SESSION
from modules.database.psql_insert_copy import psql_insert_copy
from shapely import wkt


session = SESSION()

def export_countries_table():
    gdf_countries = gpd.read_file('https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson')
    gdf_countries.columns = gdf_countries.columns.str.lower()
    gdf_countries = gdf_countries.rename_geometry('geom')
    gdf_countries = gdf_countries.rename(columns={'iso_a2' : 'iso'})
    gdf_countries = gdf_countries[['iso', 'name', 'geom']]
    
    
    gdf_countries['geom'] = [MultiPolygon([feature]) if isinstance(feature, Polygon) \
    else feature for feature in gdf_countries['geom']]
    
    psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    gdf_countries.to_sql(name='countries',
                        con=ENGINE,
                        schema='public',
                        method=psql_insert,
                        if_exists='append',
                        index=False,
                        dtype={'geom': Geometry('MultiPolygon', srid=4326)})

def export_cities_table():
    gdf_cities = gpd.read_file('https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_populated_places_simple.geojson')
    gdf_cities.columns = gdf_cities.columns.str.lower()
    gdf_cities = gdf_cities.rename_geometry('geom')
    gdf_cities = gdf_cities[['name', 'geom']]
    gdf_cities = gdf_cities.reset_index(names='id')
    
    psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    gdf_cities.to_sql(name='cities',
                        con=ENGINE,
                        schema='public',
                        method=psql_insert,
                        if_exists='append',
                        index=False,
                        dtype={'geom': Geometry('Polygon', srid=4326)})

def export_land_cover_class_table(df_land_cover):
    psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    df_land_cover.to_sql(name='land_cover_classes',
                        con=ENGINE,
                        schema='public',
                        method=psql_insert,
                        if_exists='append',
                        index=False)

def export_rivers_lakes_table():
    gdf_rivers_lakes = gpd.read_file('https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_rivers_lake_centerlines.geojson')
    gdf_rivers_lakes = gdf_rivers_lakes.rename_geometry('geom')
    gdf_rivers_lakes = gdf_rivers_lakes[['featureclass', 'name', 'geom']]
    gdf_rivers_lakes = gdf_rivers_lakes.reset_index(names='id')
    gdf_rivers_lakes = gdf_rivers_lakes.dropna(subset=['geom', 'featureclass'])

    gdf_rivers_lakes['geom'] = [MultiLineString([feature]) if isinstance(feature, LineString) \
    else feature for feature in gdf_rivers_lakes['geom']]

    export_land_cover_class_table(gdf_rivers_lakes['featureclass'])
    psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    gdf_rivers_lakes.to_sql(name='rivers_lakes',
                        con=ENGINE,
                        schema='public',
                        method=psql_insert,
                        if_exists='append',
                        index=False,
                        dtype={'geom': Geometry('MultiLineString', srid=4326)})


def export_urban_areas_table():
    gdf_urban_areas = gpd.read_file('https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_urban_areas.geojson')
    gdf_urban_areas = gdf_urban_areas.rename_geometry('geom')
    gdf_urban_areas = gdf_urban_areas.drop('scalerank', axis=1)
    gdf_urban_areas = gdf_urban_areas.reset_index(names='id')
    gdf_urban_areas = gdf_urban_areas.dropna(subset=['geom', 'featureclass'])

    export_land_cover_class_table(gdf_urban_areas['featureclass'])
    psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    gdf_urban_areas.to_sql(name='urban_areas',
                        con=ENGINE,
                        schema='public',
                        method=psql_insert,
                        if_exists='append',
                        index=False,
                        dtype={'geom': Geometry('Polygon', srid=4326)})

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
    # gdf['centroid_test'] = gdf['geom']
    # sat_image_gdf = gdf[['id', 'clear_confidence_percent', 'cloud_cover', 
    #                     'pixel_res', 'time_acquired', 'centroid', 'centroid_test', 
    #                     'geom', 'sat_id', 'item_type_id']]
    
    # psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    # sat_image_gdf.to_sql(name='sat_images',
    #                     con=ENGINE,
    #                     schema='public',
    #                     method=psql_insert,
    #                     if_exists='append',
    #                     index=False,
    #                     dtype={'geom': Geometry('Polygon', srid=4326)})

    for i in gdf.index:
        sat_image = SatImage(id = gdf.loc[i,'id'], 
                        clear_confidence_percent = gdf.loc[i,'clear_confidence_percent'],
                        cloud_cover = gdf.loc[i,'cloud_cover'],
                        pixel_res = gdf.loc[i,'pixel_res'],
                        time_acquired = gdf.loc[i, 'time_acquired'],
                        centroid = wkt.dumps(gdf.loc[i, 'geom']),
                        geom = wkt.dumps(gdf.loc[i, 'geom']),
                        sat_id = gdf.loc[i, 'sat_id'],
                        item_type_id = gdf.loc[i, 'item_type_id'])

        
        session.add(sat_image)
        session.commit()
    

def postgis_exporter(gdf):
  
    export_countries_table()
    export_cities_table()
    export_urban_areas_table()
    export_rivers_lakes_table()
    export_satellites_table(gdf)
    export_item_types_table(gdf)
    export_asset_types_table(gdf)
    export_sat_images_table(gdf)
  
