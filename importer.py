import logging
from pathlib import Path

from modules.importer import arg_parser, postgis_importer, data_wrangler, api_importer
from modules.importer import utils
from modules.importer import data_models
from modules.config import LOGGER

def importer(args):
    '''imports satellite imagery metadata for the given AOI, TOI and cloud cover.
     Exports all non-exisisting metadata to tables in PostGIS.
     '''
    
    LOGGER.info(f"The TOI is: {args['start_date']}/{args['end_date']}...")
    LOGGER.info("Requesting metadata from Planets Data API...")
    features_list = api_importer.api_importer(args)

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