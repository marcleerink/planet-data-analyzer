import logging
from pathlib import Path

from modules.importer import arg_parser, clients, postgis_importer, clients
from modules.importer import utils
from modules.importer import data_models
from modules.config import LOGGER
def api_importer(args):
    """
    Imports features from Planets Data API for all features in AOI,TOI, below provided cloud cover threshold
    If item types are provided only searches for those, otherwise searches all available item_types
    """
    client = clients.DataAPIClient()
    geometry = utils.geojson_import(args.get('aoi_file'))
    
    
    features = client.get_features(start_date=args.get('start_date'),
                                end_date=args.get('end_date'), 
                                cc=args.get('cc'),
                                geometry=geometry)
    
    for f in features:
        print(f.id)
        f.to_satellite_model()
        f.to_item_type_model()
        f.to_sat_image_model()
        f.to_asset_type_model()
    
    
    
    
    
    return features
    
def importer(args):
    '''imports satellite imagery metadata for the given AOI, TOI and cloud cover.
     Exports all non-exisisting metadata to tables in PostGIS.
     '''

     
    
    LOGGER.info(f"The TOI is: {args['start_date']}/{args['end_date']}...")
    LOGGER.info("Requesting metadata from Planets Data API...")
    features_list = clients.api_importer(args)

    if len(features_list) == 0:
        LOGGER.warning("No images found within AOI, TOI and CC filter")
        return
        
    LOGGER.info('Exporting to postgis tables')
    postgis_importer.postgis_importer(features_list)
    

if __name__ == "__main__":
    args_bundle = arg_parser.parser()
    pool = utils.ReportPool(4)
    results = pool.map(importer, args_bundle)
    pool.close()
    pool.join()