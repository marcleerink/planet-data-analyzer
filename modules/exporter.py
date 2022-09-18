import pandas as pd
import os
from pathlib import Path


def export_path_maker(dir_name, file_name , start_date, end_date):
    char_replace = {' ':'_', ',':'_', '.': '_', '/':'_', '$':'_','*':'_'}
    file_name = str(file_name.translate(str.maketrans(char_replace))).lower()
    export_filename = file_name + '_' + start_date + "_to_" + end_date
    export_directory = os.path.join(dir_name,file_name)
    Path(export_directory).mkdir(parents=True, exist_ok=True)

    return export_filename, export_directory

def export_reports(df, export_filename, export_directory, df2=None, df3=None):
    """Saves the provided DataFrames in an excel workbook with separate sheets in the export_directory."""
    
    # write tables to an excel spreadsheet
    output_filename = "".join([export_filename, '_.xlsx'])
    output_path = os.path.join(export_directory, output_filename)
    writer = pd.ExcelWriter(output_path)
    with writer:
        df.to_excel(writer, sheet_name = 'quick_search', index=False)
        if df2:
            df2.to_excel(writer, sheet_name = '2', index=False)
        if df3:
            df3.to_excel(writer, sheet_name = '3', index=False)
        


def export_footprints(gdf, export_filename, export_directory, entity):
    """Exports the footprints of the downloaded data as a geojson file.

    Parameters
    ----------
    gdf_all : GeoDataFrame
        Contains all footprints except for those that need to be ignored.
    start_date : str
        Start date of the time interval to create a report for, in ISO ("
        "YYYY-MM-DD) format.
    end_date : str
        End date of the time interval to create a report for, in ISO ("
        "YYYY-MM-DD) format.
    export_directory : str
        Directory in which to save the footprints in (must already exist).
    """
    
    # drop columns that cannot be exported as geojson
    gdf = gdf.drop(['centroid', 'fulfilled_geometry'], axis=1, errors='ignore')
    
    filename = "".join(["footprints_",entity,'_', export_filename, ".geojson"])
    footprints_path = os.path.join(export_directory, filename)
    gdf.to_file(footprints_path, driver="GeoJSON")

