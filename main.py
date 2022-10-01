import logging
from pathlib import Path
import geopandas as gpd

from modules import api_importer
from modules import arg_parser
from modules import utils
from modules import exporter
from modules import data_wrangler
from modules import plotter
from modules import postgis_exporter


# Logger
logging.basicConfig(level=logging.INFO, format="%(processName)s:%(message)s")
LOGGER = logging.getLogger(__name__)

def main(args):
    # import geometry from file
    geometry = utils.geojson_import(args.get('aoi_file'))
    
    # search items for provided AOI,TOI, item types and cloud cover threshold
    items_list = api_importer.searcher(args.get('api_key'),
                                args.get('item_types'), 
                                args.get('start_date'), 
                                args.get('end_date'), 
                                args.get('cc'),
                                geometry)

    # converts api response to cleaned dataframe
    df = utils.api_response_to_clean_df(items_list)

    # convert to gdf, split for postGIS tables
    gdf = data_wrangler.wrangler(df)
    
    # export to postgis
    postgis_exporter.postgis_exporter(gdf)

    # export to excel and footprints
    exporter.exporter(gdf, 'planet', args.get('out_dir'))

    # session = db.SESSION()
    # query = session.query(tables.SatImage).order_by(tables.SatImage.geom).all()
    # print(query)
    
    # # folium web_map
    # plotter.folium_web_map(gdf, 
    #                         export_filename='Planet', 
    #                         export_directory=args.get('out_dir'), 
    #                         time_interval='Day', 
    #                         start_date=args.get('start_date'), 
    #                         end_date=args.get('end_date'))

if __name__ == "__main__":
    args_bundle = arg_parser.parser()
    Path(args_bundle[0].get('out_dir')).mkdir(parents=True, exist_ok=True)
    pool = utils.ReportPool(4)
    results = pool.map(main, args_bundle)
    pool.close()
    pool.join()