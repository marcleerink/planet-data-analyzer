
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString, Polygon, MultiPolygon
from modules.database.db import AssetType, ItemType, SatImage, Satellite,\
                                 Country, City, LandCoverClass, get_db_session
from shapely import wkt
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

   
def get_asset_types_data(gdf):
    asset_types_df = gdf['assets']
    return pd.DataFrame(set(asset_types_df.explode().to_list()), columns=['id'])

def import_asset_types_table(session, asset_types_df):
    for i in asset_types_df['id']:
        asset_type = AssetType(id = i)
        session.add(asset_type)
        session.commit()
    

def import_item_types_table(session, r):
    item_types = ItemType(id = r.item_type_id,
                        sat_id = r.sat_id
                        )
    session.add(item_types)
    session.commit()

def import_satellites_table(session, r):
    satellites = Satellite(
                id = r.sat_id,
                name = r.satellite,
                pixel_res = r.pixel_res
                )
    session.add(satellites)
    session.commit()

def import_sat_images_table(session, r):
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


def postgis_importer(gdf):
    session = get_db_session()

    import_countries_table(session, get_data_countries())
    export_cities_table(session, get_data_cities())

    gdf_land_cover_class = concat_land_cover_class_data()
    export_land_cover_class_table(session, gdf_land_cover_class)
    
    for r in gdf.itertuples():
        import_satellites_table(session, r)
        import_item_types_table(session, r)
        import_sat_images_table(session, r)
    
    import_asset_types_table(session, get_asset_types_data(gdf))

  
