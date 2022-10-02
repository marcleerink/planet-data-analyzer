import logging
from pathlib import Path

from modules import api_importer
from modules import arg_parser
from modules import utils
from modules import data_wrangler
from modules import to_postgis
from modules.Logger import LOGGER

def importer(args):
    '''imports satellite imagery metadata for the given AOI, TOI.
     Exports all unique rows to tables (satellites, sat_images, item_types, asset_types) in PostGIS.
     '''

    # import geometry from file
    geometry = utils.geojson_import(args.get('aoi_file'))
    
    LOGGER.info(f"The TOI is: {args.get('start_date')}/{args.get('end_date')}...")
    LOGGER.info("Requesting metadata from Planets Data API...")
    items_list = api_importer.searcher(args.get('api_key'),
                                args.get('item_types'), 
                                args.get('start_date'), 
                                args.get('end_date'), 
                                args.get('cc'),
                                geometry)

    # converts api response to cleaned dataframe
    df = utils.api_response_to_clean_df(items_list)

    # convert to gdf and wrangle data
    gdf = data_wrangler.wrangler(df)
    
    LOGGER.info('Exporting to postgis tables')
    to_postgis.postgis_exporter(gdf)

if __name__ == "__main__":
    args_bundle = arg_parser.parser()
    Path(args_bundle[0].get('out_dir')).mkdir(parents=True, exist_ok=True)
    pool = utils.ReportPool(4)
    results = pool.map(importer, args_bundle)
    pool.close()
    pool.join()