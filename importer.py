from modules.importer import arg_parser, utils
from modules.importer.clients import data, geojson_xyz
from modules.config import LOGGER
from modules.database import db
from concurrent.futures import ThreadPoolExecutor

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

    client = data.DataAPIClient()
    geometry = utils.geojson_import(args.aoi_file)

    features = client.get_features(start_date=args.start_date,
                                end_date=args.end_date, 
                                cc=args.cc,
                                geometry=geometry)

    def to_postgis(feature):
        feature.to_satellite_model()
        feature.to_item_type_model()
        feature.to_sat_image_model()
        feature.to_asset_type_model()    
        
    LOGGER.info('Exporting images to postgis tables')
    with ThreadPoolExecutor(16) as executor:
        executor.map(to_postgis, features)
                    

def country_table_import():
    client = geojson_xyz.GeojsonXYZClient()
    features = client.get_countries()
    
    def to_postgis(feature):
        feature.to_country_model()

    LOGGER.info('Exporting countries to postgis tables')
    with ThreadPoolExecutor(16) as executor:
        executor.map(to_postgis, features)

def city_table_import():
    client = geojson_xyz.GeojsonXYZClient()
    features = client.get_cities()
    
    def to_postgis(feature):
        feature.to_city_model()

    LOGGER.info('Exporting cities to postgis tables')
    with ThreadPoolExecutor(16) as executor:
        executor.map(to_postgis, features)


def importer(args):
    '''Imports satellite imagery metadata for the given AOI, TOI and cloud cover.
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
    
    if session.query(db.Country).first():
        country_table_import()
    if session.query(db.City).first():
        city_table_import()

    data_api_importer(args)
    
    LOGGER.info('All features imported!')
    
if __name__ == "__main__":
    args = arg_parser.parser()
    importer(args)
    