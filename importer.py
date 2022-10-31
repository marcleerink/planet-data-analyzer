from modules.importer import arg_parser
from modules.importer.clients import data, geojson_xyz
from modules.config import LOGGER
from modules.database import db
from concurrent.futures import ThreadPoolExecutor
import json


def geojson_import(aoi_file):
    with open(aoi_file) as f:
        geometry = json.load(f)
    return geometry['features'][0]['geometry']

def data_api_importer(args):
    """
    Imports features from Planets Data API in AOI,TOI, below provided cloud cover threshold
    If item types are provided only searches for those, otherwise searches all available item_types

    :param object args
        ArgumentParser object containing:
        str aoi_file
            Path to geojson file containing AOIs
        str api_key
            Planet's API key
        str start_date
            Start date of the time interval in ISO (YYYY-MM-DD) format (gte).
        str end_date
            End date of the time interval in ISO (YYYY-MM-DD) format (lte).
        float cc
            Cloud cover value (0.0 - 1.0)
    """
    
    client = data.DataAPIClient(api_key=args.api_key)
    geometry = geojson_import(args.aoi_file)

    features = client.get_features(start_date=args.start_date,
                                end_date=args.end_date, 
                                cc=args.cc,
                                geometry=geometry)  

    def to_postgis(feature):
        feature.to_satellite_model()
        feature.to_item_type_model()
        feature.to_sat_image_model()
        feature.to_asset_type_model()    
    
    for feature in features:
        to_postgis(feature)
    # with ThreadPoolExecutor(16) as executor:
    #     executor.map(to_postgis, features)

                    

def country_table_import():
    client = geojson_xyz.GeojsonXYZClient()
    features = client.get_countries()

    def to_postgis(feature):
        feature.to_country_model()

    with ThreadPoolExecutor(16) as executor:
        executor.map(to_postgis, features)

def city_table_import():
    client = geojson_xyz.GeojsonXYZClient()
    features = client.get_cities()

    def to_postgis(feature):
        feature.to_city_model()

    with ThreadPoolExecutor(16) as executor:
        executor.map(to_postgis, features)

def river_lake_import():
    client = geojson_xyz.GeojsonXYZClient()
    features = client.get_rivers_lakes()

    with ThreadPoolExecutor(16) as executor:
        executor.map(land_cover_to_postgis, features)

def land_cover_to_postgis(feature):
    feature.to_land_cover_model()
    
def importer(args):
    '''
    Imports satellite imagery metadata for the given AOI, TOI and cloud cover.
    Only imports static land cover class metadata (cities/countries/rivers_lakes) if not done before.
    Imports all non-exisisting metadata to tables in PostGIS.

    :param object args 
        ArgumentParser object containing:
            str aoi_file
                Path to geojson file containing AOIs
            str api_key
                Planet's API key
            str start_date
                Start date of the time interval in ISO (YYYY-MM-DD) format (gte).
            str end_date
                End date of the time interval in ISO (YYYY-MM-DD) format (lte).
            float cc
                Cloud cover value (0.0 - 1.0)
     '''
    session = db.get_db_session()

    if not session.query(db.Country.iso).first():
        country_table_import()
    if not session.query(db.City.id).first():
        city_table_import()

    if not session.query(db.LandCoverClass.id).first():
        river_lake_import()

    data_api_importer(args)
    
    LOGGER.info('Total of {} countries in db'.format(session.query(db.Country).count()))
    LOGGER.info('Total of {} cities in db'.format(session.query(db.City).count()))
    LOGGER.info('Total of {} landcoverclasses in db'.format(session.query(db.LandCoverClass).count()))
    LOGGER.info('Total of {} satellites in db'.format(session.query(db.Satellite).count()))
    LOGGER.info('Total of {} item types in db'.format(session.query(db.ItemType).count()))
    LOGGER.info('Total of {} sat images in db'.format(session.query(db.SatImage).count()))
    LOGGER.info('Total of {} asset types in db'.format(session.query(db.AssetType).count()))
    
    
if __name__ == "__main__":
    args = arg_parser.parser()
    importer(args)
    