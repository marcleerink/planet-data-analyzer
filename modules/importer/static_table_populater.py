from functools import partial
import geopandas as gpd
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from geoalchemy2 import Geometry

from modules.database.db import ENGINE
from psql_insert_copy import psql_insert_copy

def export_countries_table():
    gdf_countries = gpd.read_file('data/World_Countries_(Generalized).geojson')
    gdf_countries.columns = gdf_countries.columns.str.lower()
    gdf_countries = gdf_countries.rename_geometry('geom')
    gdf_countries = gdf_countries[['iso', 'country', 'geom']]
    gdf_countries = gdf_countries.rename(columns={'country' : 'name'})
    
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
    gdf_cities = gpd.read_file('data/cities.geojson')
    gdf_cities = gdf_cities.rename_geometry('geom')
    gdf_cities.columns = gdf_cities.columns.str.lower()
    gdf_cities['name'] = gdf_cities['name'].str.lower()
    gdf_cities = gdf_cities.reset_index(names='id')

    psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    gdf_cities.to_sql(name='cities',
                        con=ENGINE,
                        schema='public',
                        method=psql_insert,
                        if_exists='append',
                        index=False,
                        dtype={'geom': Geometry('Polygon', srid=4326)})

if __name__ == "__main__":
    export_countries_table()
    export_cities_table()