import logging
from pathlib import Path

from modules.importer import arg_parser, postgis_importer, data_wrangler, api_importer
from modules.importer import utils
from modules.config import LOGGER

def importer(args):
    '''imports satellite imagery metadata for the given AOI, TOI.
     Exports all non-exisisting metadata to tables in PostGIS.
     '''

    # import geometry from file
    geometry = utils.geojson_import(args.get('aoi_file'))
    
    LOGGER.info(f"The TOI is: {args.get('start_date')}/{args.get('end_date')}...")
    LOGGER.info("Requesting metadata from Planets Data API...")
    items_list = api_importer.api_importer(args.get('api_key'),
                                args.get('item_types'), 
                                args.get('start_date'), 
                                args.get('end_date'), 
                                args.get('cc'),
                                geometry)

    # convert to gdf and wrangle data
    gdf = data_wrangler.wrangler(items_list)
    
    LOGGER.info('Exporting to postgis tables')
    postgis_importer.postgis_importer(gdf)

if __name__ == "__main__":
    args_bundle = arg_parser.parser()
    pool = utils.ReportPool(4)
    results = pool.map(importer, args_bundle)
    pool.close()
    pool.join()