from datetime import datetime
import pytest
import pandas as pd
from pandas import json_normalize
import geopandas as gpd
from shapely.geometry import Polygon


import logging
from modules.importer.data_wrangler import api_response_to_clean_df, build_timestamp, drop_nan_rows_duplicates, gdf_creater, list_to_polygon, rename_columns, wrangler
from tests.importer.fixtures import fake_response

@pytest.fixture()
def fake_item_list():
    return [{'_links': {'_self': 'https://api.planet.com/data/v1/item-types/Landsat8L1G/items/LC91940242022294LGN01', 
            'assets': 'https://api.planet.com/data/v1/item-types/Landsat8L1G/items/LC91940242022294LGN01/assets/', 
            'thumbnail': 'https://tiles.planet.com/data/v1/item-types/Landsat8L1G/items/LC91940242022294LGN01/thumb'},
            '_permissions': ['assets.analytic_b1:download', 'assets.analytic_b10:download', 'assets.analytic_b11:download',
            'assets.analytic_b2:download', 'assets.analytic_b3:download', 'assets.analytic_b4:download', 'assets.analytic_b5:download',
            'assets.analytic_b6:download', 'assets.analytic_b7:download', 'assets.analytic_b8:download', 'assets.analytic_b9:download',
            'assets.analytic_bqa:download', 'assets.metadata_txt:download', 'assets.visual:download'], 'assets': ['analytic_b1', 'analytic_b10',
            'analytic_b11', 'analytic_b2', 'analytic_b3', 'analytic_b4', 'analytic_b5', 'analytic_b6', 'analytic_b7', 'analytic_b8', 'analytic_b9', 
            'analytic_bqa', 'metadata_txt', 'visual'], 'geometry': {'coordinates': [[[10.307355831126545, 52.75793769619655], [12.971259174213147, 52.30053811911451], 
            [12.159870763630481, 50.61073431631686], [9.592408111069357, 51.06027798821833], [10.307355831126545, 52.75793769619655]]],
            'type': 'Polygon'}, 'id': 'LC91940242022294LGN01', 'properties': {'acquired': '2022-10-21T10:09:35.457782Z', 'anomalous_pixels': 0,
            'cloud_cover': 0.94, 'collection': '2', 'columns': 7781, 'data_type': 'L1TP', 'epsg_code': 32632, 'gsd': 30, 'instrument': 'OLI_TIRS',
            'item_type': 'Landsat8L1G', 'origin_x': 539085, 'origin_y': 5846715, 'pixel_resolution': 30, 'processed': '2022-10-21T15:31:51Z',
            'product_id': 'LC09_L1TP_194024_20221021_20221021_02_T1', 'provider': 'usgs', 'published': '2022-10-22T13:33:26Z', 'quality_category': 'standard',
            'rows': 7871, 'satellite_id': 'Landsat9', 'sun_azimuth': 166.2, 'sun_elevation': 26.6, 'updated': '2022-10-22T13:33:26Z', 'usable_data': 0.667,
            'view_angle': 0, 'wrs_path': 194, 'wrs_row': 24}, 'type': 'Feature'}]

@pytest.fixture()
def fake_df(fake_item_list):
    return json_normalize(fake_item_list)

@pytest.fixture()
def fake_geometry_list_correct(fake_df):
    return fake_df['geometry.coordinates'][0]

@pytest.fixture()
def fake_geometry_list_multipolygon():
    return [[[12.51994065442387, 52.39176303252264], [12.560597894914874, 52.49421353945495],\
            [12.890812378786498, 52.44348145364647], [12.890812378786498, 52.39176303252264],\
            [12.51994065442387, 52.39176303252264]]], [[[12.890812378786498, 52.558432760906044],\
            [12.603630917810015, 52.60189154935561], [12.612400393305046, 52.62350491918347],\
            [12.890812378786498, 52.62350491918347], [12.890812378786498, 52.558432760906044]]]


def test_api_response_to_clean_df(fake_item_list):
    """
    Test that api response is returned as filled DataFrame with same index lenght.
    Sample test that columns are filled with correct data
    """
    #act
    result = api_response_to_clean_df(fake_item_list)

    #assert
    assert isinstance(result, pd.DataFrame)
    assert len(result.index) == len(fake_item_list)
    assert result['properties.acquired'][0] == '2022-10-21T10:09:35.457782Z'
    assert isinstance(result['geometry.coordinates'][0], list)

def test_build_timestamp(fake_df):
    """Test if string column is converted to datetime without timezone"""
    #act
    result = build_timestamp(fake_df, 'properties.acquired')
    #assert
    assert result['properties.acquired'].dtype == 'datetime64[ns]'
    assert 'Z' not in result['properties.acquired'].astype(str)

def test_list_to_polygon_success(fake_geometry_list_correct):
    """Check if list is transferred to shapely Polygon """
    result = list_to_polygon(fake_geometry_list_correct)

    assert isinstance(result, Polygon)

def test_list_to_polygon_exception(fake_geometry_list_multipolygon, caplog: pytest.LogCaptureFixture):
    """
    Test that no result is returned when geometry is not polygon and logging is done.
    """
    #act
    result = list_to_polygon(fake_geometry_list_multipolygon)
    
    #assert
    assert result == None
    assert len(caplog.records) == 1
    

def test_gdf_creater_success(fake_df):
    """
    Test if gdf is created with correct CRS. 
    Test if geom_type is Polygon for all geom rows.
    Test if index is sorted.
    """
    #act
    result = gdf_creater(fake_df, 'geometry.coordinates')
    #assert
    assert isinstance(result, gpd.GeoDataFrame)
    assert isinstance(result.geometry.all(), Polygon)
    assert result['geom'].crs == 4326
    assert result.index.is_monotonic_increasing

def test_rename_columns(fake_df):
    """
    Test that properties is removed from all column names
    Test that all renamed columns are in dataframe and renamed ones dropped
    """
    #arrange
    dropped_columns = ['acquired', 'pixel_resolution', 'provider', 'satellite_id', 'item_type']
    correct_columns = ['time_acquired', 'pixel_res', 'satellite', 'sat_id', 'item_type_id' ]
    
    #act
    result = rename_columns(fake_df)

    #assert
    assert all('properties' not in i for i in result.columns)
    assert all(i not in result.columns for i in dropped_columns)
    assert all(i in result.columns for i in correct_columns)

def test_drop_nan_rows_duplicates():
    #arrange
    fake_df_duplicates = pd.DataFrame({'geom': [1,1,3,2],
                                        'id': ['id1', 'id2', 'id1', 'id3']})

    #act
    result = drop_nan_rows_duplicates(fake_df_duplicates)

    #assert
    assert len(result.index) == 3
    assert result['id'].is_unique

    

def test_wrangler(fake_item_list):
    """
    Test if satellite column is converted to title.
    Test if index is sorted.
    """
    #act
    result = wrangler(fake_item_list)
    #assert
    assert all(i.istitle() for i in result['satellite'])
    assert result.index.is_monotonic_increasing
    
    

