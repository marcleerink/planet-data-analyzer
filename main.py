import logging
from pandas import json_normalize
import pandas as pd
from pathlib import Path

from modules import data_api
from modules import processor
from modules import arg_parser
from modules import utils
from modules import exporter

# Logger
logging.basicConfig(level=logging.INFO, format="%(processName)s:%(message)s")
LOGGER = logging.getLogger(__name__)

def main(args):

    # import geometry from file
    geometry = utils.geojson_import(args.get('aoi_file'))
    
    # For each AOI, construct search
    items = data_api.searcher(args.get('api_key'),
                                 args.get('item_types'), 
                                 args.get('start_date'), 
                                 args.get('end_date'), 
                                 args.get('cc'),
                                 geometry)
    df_list = []
    for item in items:
        temp_df = json_normalize(item)
        df_list.append(temp_df)
    
    df =  pd.concat(df_list)
    
    exporter.export_reports(df,'test', args.get('out_dir'))
    print(df)

# run when file is directly executed
if __name__ == "__main__":
    # parse arguments and bundle
    args_bundle = arg_parser.parser()
    
    # output dir
    Path(args_bundle[0].get('out_dir')).mkdir(parents=True, exist_ok=True)

    #set up multiprocessing and call main module
    pool = processor.ReportPool(4)
    results = pool.map(main, args_bundle)
    pool.close()
    pool.join()