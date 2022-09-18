import logging
from pathlib import Path
import geopandas as gpd
import geoalchemy2

from modules import data_api
from modules import processor
from modules import arg_parser
from modules import utils
from modules import exporter
from modules import data_wrangler
from modules import db


# Logger
logging.basicConfig(level=logging.DEBUG, format="%(processName)s:%(message)s")
LOGGER = logging.getLogger(__name__)

def main(args):

    # import geometry from file
    geometry = utils.geojson_import(args.get('aoi_file'))
    
    # search items for provided AOI,TOI, item types and cloud cover threshold
    items_list = data_api.searcher(args.get('api_key'),
                                 args.get('item_types'), 
                                 args.get('start_date'), 
                                 args.get('end_date'), 
                                 args.get('cc'),
                                 geometry)

    # converts api response to cleaned dataframe
    df = utils.api_response_to_clean_df(items_list)

    gdf = data_wrangler.wrangler(df)
    
    engine = db.db_engine()

    # store in postgis
    gdf.to_postgis(name='planet', con= engine, if_exists='append')
    
    # export df to excel
    exporter.export_reports(gdf,'test', args.get('out_dir'))

# run when file is directly executed
if __name__ == "__main__":
    # parse arguments and bundle
    args_bundle = arg_parser.parser()
    
    # set/create output dir
    Path(args_bundle[0].get('out_dir')).mkdir(parents=True, exist_ok=True)

    #set up multiprocessing and call main module
    pool = processor.ReportPool(4)
    results = pool.map(main, args_bundle)
    pool.close()
    pool.join()