import pandas as pd
import os
from functools import partial
from database.db import ENGINE
from database.psql_insert_copy import psql_insert_copy

def gdf_to_postgis(gdf, name, if_exists):
    gdf.to_postgis(name=name, con=ENGINE, if_exists=if_exists)

def export_reports(df, export_filename, export_directory):
    """Saves the provided DataFrames in an excel workbook with separate sheets in the export_directory."""
    
    # write tables to an excel spreadsheet
    output_filename = "".join([export_filename, '_.xlsx'])
    output_path = os.path.join(export_directory, output_filename)
    writer = pd.ExcelWriter(output_path)
    with writer:
        df.to_excel(writer, sheet_name = 'sat_images', index=False)
            

def export_footprints(gdf, export_filename, export_directory):
    """Exports the footprints of the downloaded data as a geojson file.

    Parameters
    ----------
    gdf_all : GeoDataFrame
        Contains all footprints except for those that need to be ignored.
    export_directory : str
        Directory in which to save the footprints in (must already exist).
    """
    
    
    filename = "".join(["footprints_",'_', export_filename, ".geojson"])
    footprints_path = os.path.join(export_directory, filename)
    gdf.to_file(footprints_path, driver="GeoJSON")


def export_item_types_table(gdf):
    item_types_df = gdf[['item_type_id', 'sat_id']]
    item_types_df = item_types_df.drop_duplicates(subset='item_type_id')
    item_types_df = item_types_df.dropna(subset='item_type_id')
    item_types_df = item_types_df.rename(columns={'item_type_id' : 'id'})

    psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    item_types_df.to_sql(name='item_types', 
                        con=ENGINE, 
                        schema='public', 
                        method=psql_insert, 
                        if_exists='append', 
                        index=False)
    


def export_satellites_table(gdf):
    satellites_df = gdf[['sat_id', 'satellite', 'pixel_res']]
    satellites_df = satellites_df.drop_duplicates(subset='sat_id')
    satellites_df = satellites_df.dropna(subset='sat_id')
    satellites_df = satellites_df.rename(columns={'sat_id' : 'id', 'satellite' : 'name'})

    psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    satellites_df.to_sql(name='satellites', 
                        con=ENGINE, 
                        schema='public',
                        method=psql_insert,
                        if_exists='append', 
                        index=False)

def export_sat_images_table(gdf):
    sat_image_gdf = gdf[['id', 'clear_confidence_percent', 'cloud_cover', 'pixel_res', 'time_acquired', 'geom', 'sat_id', 'item_type_id']]
    psql_insert = partial(psql_insert_copy, on_conflict_ignore=True)
    sat_image_gdf.to_sql(name='sat_images',
                        con=ENGINE,
                        schema='public',
                        method=psql_insert,
                        if_exists='append',
                        index=False)

def exporter(gdf, export_filename, export_directory):
    export_reports(gdf,export_filename, export_directory)

    export_satellites_table(gdf)
    export_item_types_table(gdf)
    export_sat_images_table(gdf)
    
    
    # export_footprints(gdf, export_filename, export_directory)