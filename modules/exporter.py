import pandas as pd
import os
from pathlib import Path
from modules import db


def export_path_maker(dir_name, file_name , start_date, end_date):
    char_replace = {' ':'_', ',':'_', '.': '_', '/':'_', '$':'_','*':'_'}
    file_name = str(file_name.translate(str.maketrans(char_replace))).lower()
    export_filename = file_name + '_' + start_date + "_to_" + end_date
    export_directory = os.path.join(dir_name,file_name)
    Path(export_directory).mkdir(parents=True, exist_ok=True)

    return export_filename, export_directory

def gdf_to_postgis(gdf, name='Berlin', if_exists='fail'):
    engine = db.db_engine()
    gdf.to_postgis(name=name, con=engine, if_exists=if_exists)

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


def exporter(gdf,export_filename, export_directory):
    
    gdf_to_postgis(gdf,'sat_images_staging', if_exists='replace')
    export_reports(gdf,export_filename, export_directory)
    export_footprints(gdf, export_filename, export_directory)