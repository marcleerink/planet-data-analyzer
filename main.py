import os
import logging
from datetime import datetime, timedelta


from modules import data_api
from modules import processor
from modules import arg_parser

# Logger
logging.basicConfig(level=logging.INFO, format="%(processName)s:%(message)s")
LOGGER = logging.getLogger(__name__)

def geojson_import(aoi_file):
    import json
    with open(aoi_file) as f:
        geometry = json.load(f)
    return geometry['features'][0]['geometry']

def main(args):

    # import geometry from file
    geometry = geojson_import(args.get('aoi_file'))
    print(geometry)
    # For each AOI, construct search
    data_df = data_api.do_search(args.get('api_key'),
                                 args.get('item_types'), 
                                 args.get('start_date'), 
                                 args.get('end_date'), 
                                 args.get('cc'),
                                 geometry)
    print(data_df)

# run when file is directly executed
if __name__ == "__main__":
    # parse arguments and bundle
    args_bundle = arg_parser.parser()

    #set up multiprocessing and call main module
    pool = processor.ReportPool(4)
    results = pool.map(main, args_bundle)
    pool.close()
    pool.join()