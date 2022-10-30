
import pandas as pd
import geopandas as gpd
from modules.database.db import AssetType, ItemType, SatImage, Satellite,\
                                 Country, City, LandCoverClass, get_db_session
from modules.importer.data_models import ImageDataFeature
from geoalchemy2.shape import from_shape

def get_data_countries():
    gdf_countries = gpd.read_file('https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson')
    gdf_countries.columns = gdf_countries.columns.str.lower()
    gdf_countries = gdf_countries.rename_geometry('geom')
    gdf_countries = gdf_countries.rename(columns={'iso_a2' : 'iso'})
    return gdf_countries[['iso', 'name', 'geom']]

def import_countries_table(session, gdf_countries):
    for r in gdf_countries.itertuples():
        country = Country(
                        iso = r.iso,
                        name = r.name,
                        geom = from_shape(r.geom, srid=4326))
        session.add(country)
        session.commit()
    

def get_data_cities():
    gdf_cities = gpd.read_file('https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_populated_places_simple.geojson')
    gdf_cities.columns = gdf_cities.columns.str.lower()
    gdf_cities = gdf_cities.rename_geometry('geom')
    gdf_cities = gdf_cities[['name', 'geom']]
    return gdf_cities.reset_index(names='id')

def export_cities_table(session, gdf_cities):
    
    for r in gdf_cities.itertuples():
        city = City(id = r.id,
                    name = r.name,
                    geom = from_shape(r.geom, srid=4326))
        session.add(city)
        session.commit()
    
def export_land_cover_class_table(session, gdf):
    for r in gdf.itertuples():
        featureclass = LandCoverClass(id = r.id,
                                    featureclass=r.featureclass,
                                    geom=from_shape(r.geom, srid=4326)
                                )
        session.add(featureclass)
        session.commit()

def concat_land_cover_class_data():
    gdf_list = [get_data_rivers_lakes(), get_data_urban_areas()]
    gdf = pd.concat(gdf_list, ignore_index=True, axis=0)
    return gdf.reset_index(names='id')
    

def get_data_rivers_lakes():
    gdf_rivers_lakes = gpd.read_file('https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_rivers_lake_centerlines.geojson')
    gdf_rivers_lakes = gdf_rivers_lakes.rename_geometry('geom')
    gdf_rivers_lakes = gdf_rivers_lakes[['featureclass', 'geom']]
    return gdf_rivers_lakes.dropna(subset=['geom', 'featureclass'])


def get_data_urban_areas():
    gdf_urban_areas = gpd.read_file('https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_urban_areas.geojson')
    gdf_urban_areas = gdf_urban_areas.rename_geometry('geom')
    gdf_urban_areas = gdf_urban_areas[['featureclass', 'geom']]
    return gdf_urban_areas.dropna(subset=['geom', 'featureclass'])


def postgis_image_data_import(features_list):
    
    for i in features_list:
        image_data= ImageDataFeature(i)
        image_data.to_satellite_model()
        image_data.to_item_type_model()
        image_data.to_sat_image_model()
        image_data.to_asset_type_model()

def postgis_importer(features_list):
    """
    Import data into postgis. Only fill static tables (countries, cities) if table is empty
    All inserts are set to ON CONFLICT DO NOTHING to skip over duplicate rows efficiently

    :param list features_list
        List containing the features from Planets Data API.
    """
    postgis_image_data_import(features_list)
    
    session = get_db_session()
    
    if session.query(Country).first() is not None:
        import_countries_table(session, get_data_countries())
    if session.query(City).first() is not None:
        export_cities_table(session, get_data_cities())

    gdf_land_cover_class = concat_land_cover_class_data()
    export_land_cover_class_table(session, gdf_land_cover_class)
    

  
