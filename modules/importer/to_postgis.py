
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString, Polygon, MultiPolygon
from modules.database.db import AssetType, ItemType, SatImage, Satellite,\
                                 Country, City, RiverLake, UrbanArea, LandCoverClass, get_db_session()
from shapely import wkt
from geoalchemy2.shape import from_shape

session = get_db_session()

def export_countries_table():
    gdf_countries = gpd.read_file('https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson')
    gdf_countries.columns = gdf_countries.columns.str.lower()
    gdf_countries = gdf_countries.rename_geometry('geom')
    gdf_countries = gdf_countries.rename(columns={'iso_a2' : 'iso'})
    gdf_countries = gdf_countries[['iso', 'name', 'geom']]

    for r in gdf_countries.itertuples():
        country = Country(
                        iso = r.iso,
                        name = r.name,
                        geom = from_shape(r.geom, srid=4326))
        session.add(country)
        session.commit()
    

def export_cities_table():
    gdf_cities = gpd.read_file('https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_populated_places_simple.geojson')
    gdf_cities.columns = gdf_cities.columns.str.lower()
    gdf_cities = gdf_cities.rename_geometry('geom')
    gdf_cities = gdf_cities[['name', 'geom']]
    gdf_cities = gdf_cities.reset_index(names='id')
    
    for r in gdf_cities.itertuples():
        city = City(id = r.id,
                    name = r.name,
                    geom = from_shape(r.geom, srid=4326))
        session.add(city)
        session.commit()
    
def export_land_cover_class_table(r):
    featureclass = LandCoverClass(featureclass = r.featureclass)
    session.add(featureclass)
    session.commit()

def export_rivers_lakes_table():
    gdf_rivers_lakes = gpd.read_file('https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_rivers_lake_centerlines.geojson')
    gdf_rivers_lakes = gdf_rivers_lakes.rename_geometry('geom')
    gdf_rivers_lakes = gdf_rivers_lakes[['featureclass', 'name', 'geom']]
    gdf_rivers_lakes = gdf_rivers_lakes.reset_index(names='id')
    gdf_rivers_lakes = gdf_rivers_lakes.dropna(subset=['geom', 'featureclass'])

    for r in gdf_rivers_lakes.itertuples():
        export_land_cover_class_table(r)
        river_lake = RiverLake(id = r.id,
                                name = r.name,
                                featureclass = r.featureclass,
                                geom = from_shape(r.geom, srid=4326))
        session.add(river_lake)
        session.commit()



def export_urban_areas_table():
    gdf_urban_areas = gpd.read_file('https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_urban_areas.geojson')
    gdf_urban_areas = gdf_urban_areas.rename_geometry('geom')
    gdf_urban_areas = gdf_urban_areas.drop('scalerank', axis=1)
    gdf_urban_areas = gdf_urban_areas.reset_index(names='id')
    gdf_urban_areas = gdf_urban_areas.dropna(subset=['geom', 'featureclass'])

    for r in gdf_urban_areas.itertuples():
        export_land_cover_class_table(r)
        urban_area = UrbanArea(id = r.id,
                                area_sqkm = r.area_sqkm,
                                featureclass = r.featureclass,
                                geom = from_shape(r.geom, srid=4326))
   

def export_asset_types_table(gdf):
    asset_types_df = gdf['assets']
    asset_types_df = pd.DataFrame(set(asset_types_df.explode().to_list()), columns=['id'])

    for i in asset_types_df['id']:
        asset_type = AssetType(id = i)
        session.add(asset_type)
        session.commit()
    

def export_item_types_table(r):
    item_types = ItemType(id = r.item_type_id,
                        sat_id = r.sat_id
                        )
    session.add(item_types)
    session.commit()

def export_satellites_table(r):
    satellites = Satellite(
                id = r.sat_id,
                name = r.satellite,
                pixel_res = r.pixel_res
                )
    session.add(satellites)
    session.commit()

def export_sat_images_table(r):
    sat_image = SatImage(
                id = r.id, 
                clear_confidence_percent = r.clear_confidence_percent,
                cloud_cover = r.cloud_cover,
                pixel_res = r.pixel_res,
                time_acquired = r.time_acquired,
                centroid = from_shape(r.geom, srid=4326),
                geom = from_shape(r.geom, srid=4326),
                sat_id = r.sat_id,
                item_type_id = r.item_type_id
                )
    session.add(sat_image)
    session.commit()


def postgis_exporter(gdf):
    
    export_countries_table()
    export_cities_table()
    export_urban_areas_table()
    export_rivers_lakes_table()
    
    for r in gdf.itertuples():
        export_satellites_table(r)
        export_item_types_table(r)
        export_sat_images_table(r)
    
    export_asset_types_table(gdf)

  
