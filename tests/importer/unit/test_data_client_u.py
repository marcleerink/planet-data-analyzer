from datetime import datetime
import pytest
import json
from shapely.geometry import shape
import pandas as pd
import vcr
from unittest import TestCase
import logging

from modules.importer.clients.data import ImageDataFeature, DataAPIClient


@pytest.fixture
def fake_response_list():
    with open('tests/resources/fake_response.json') as f:
        return json.load(f)

@pytest.fixture
def fake_item_types():
    return ['Landsat8L1G', 
            'MOD09GA', 
            'MOD09GQ', 
            'MYD09GA', 
            'MYD09GQ', 
            'PSOrthoTile', 
            'PSScene',
            'REOrthoTile', 
            'REScene', 
            'Sentinel1', 
            'Sentinel2L1C', 
            'SkySatCollect', 
            'SkySatScene', 
            'SkySatVideo']

@pytest.fixture
def fake_item_types_with_deprecated(fake_item_types):
    return sorted(fake_item_types.append(['PSScene3Band',
                                    'PSScene4Band']))

@pytest.fixture()
def fake_response_small_aoi():
    with open('tests/resources/fake_response_small_aoi.json') as f:
        return json.load(f)

@pytest.fixture
def geometry():
    with open('tests/resources/small_aoi.geojson') as f:
        geometry = json.load(f)
    return geometry['features'][0]['geometry']

@pytest.fixture
def fake_payload(geometry, fake_item_types):
    item_types = fake_item_types.append(['PSScene3Band',
                                        'PSScene4Band'])
        

    date_range_filter = {
            "type": "DateRangeFilter",
            "field_name": "acquired",
            "config": {
                "gte": "2022-10-01T00:00:00.000Z",
                "lte": "2022-10-02T00:00:00.000Z"
            }
        }

    cloud_filter = {
            "type": "RangeFilter",
            "field_name": "cloud_cover",
            "config": {
                "lte": 0.1
            }
        }

    geometry_filter = {
            "type": "GeometryFilter",
            "field_name": "geometry",
            "config":geometry}

    and_filter = {
            "type": "AndFilter",
            "config": [date_range_filter, cloud_filter, geometry_filter]
        }

    search_request = {
            "item_types": item_types,
            "filter": and_filter
        }
    return search_request


def test__get():
    
    client = DataAPIClient()

@vcr.use_cassette()
def test__query_vcr(fake_payload, fake_response_small_aoi):
    endpoint = 'quick-search'
    key = 'features'
    client = DataAPIClient(api_key='dummy')

    response = client._query(endpoint=endpoint, 
                            key=key, 
                            json_query=fake_payload)

    assert response == fake_response_small_aoi

@vcr.use_cassette()
def test__query_vcr_paginate(fake_payload, fake_response_small_aoi, caplog):
    endpoint = 'quick-search'
    key = 'features'
    client = DataAPIClient(api_key='dummy')

    with caplog.at_level(logging.DEBUG):
        response = client._query(endpoint=endpoint, 
                            key=key, 
                            json_query=fake_payload)
        assert 'Paging results...' in caplog.text


@vcr.use_cassette()
def test_get_items_vcr_u(fake_item_types):
    """test if all item types are retrieved from data_api"""

    fake_item_type_with_depracated = fake_item_types + ['PSScene3Band', 'PSScene4Band']

    print(fake_item_types)
    client = DataAPIClient(api_key='dummy')
    item_types = client.get_item_types(key='id')

    assert item_types == sorted(fake_item_type_with_depracated)

@vcr.use_cassette()
def test_get_features_vcr_u(geometry, fake_response_small_aoi):
    """test if image_features are retrieved from data client correctly"""
    start_date = '2022-10-01'
    end_date = '2022-10-02'
    cc = 0.1

    client = DataAPIClient(api_key='dummy')
    features = list(client.get_features(start_date=start_date,
                                    end_date=end_date,
                                    cc=cc,
                                    geometry=geometry))
    
    assert len(features) == len(fake_response_small_aoi)
    assert [i.id for i in features] == [str(i["id"]) for i in fake_response_small_aoi]
    



def test_ImageDataFeature(fake_response_list):
    """test if all metadata from multiple features is converted correctly"""
    
    # get ImageDataFeatures list
    fake_features_list = [ImageDataFeature(f) for f in fake_response_list]

    fake_id_list = [i.id for i in fake_features_list]
    fake_sat_id_list = [i.sat_id for i in fake_features_list]
    fake_time_list = [i.time_acquired for i in fake_features_list]
    fake_sat_list = [i.satellite for i in fake_features_list]
    fake_pixel_list = [i.pixel_res for i in fake_features_list]
    fake_item_type_list = [i.item_type_id for i in fake_features_list]
    fake_asset_list = [i.asset_types for i in fake_features_list]
    fake_cloud_list = [i.cloud_cover for i in fake_features_list]
    fake_geom_list = [i.geom for i in fake_features_list]
    
    
    # assert fake_feature_list has same data as fake_response_list
    assert len(fake_response_list) == len(fake_features_list)
    assert fake_id_list == [str(i["id"]) for i in fake_response_list]
    assert fake_sat_id_list == [str(i["properties"]["satellite_id"]) for i in fake_response_list]
    assert fake_time_list == [pd.to_datetime(i["properties"]["acquired"]) for i in fake_response_list]
    assert fake_sat_list == [str(i["properties"]["provider"].title()) for i in fake_response_list]
    assert fake_pixel_list == [float(i["properties"]["pixel_resolution"]) for i in fake_response_list]
    assert fake_item_type_list == [str(i["properties"]["item_type"]) for i in fake_response_list]
    assert fake_asset_list == [list(i["assets"]) for i in fake_response_list]
    assert fake_cloud_list == [float(i["properties"]["cloud_cover"]) for i in fake_response_list]
    assert fake_geom_list == [shape(i["geometry"]) for i in fake_response_list]



    


