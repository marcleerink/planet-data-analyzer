import pytest
import json
from shapely.geometry import shape
import pandas as pd
import vcr

import logging
import requests

from api_importer.clients.data import ImageDataFeature, DataAPIClient

TEST_URL = "https://api.planet.com/data/v1"
SEARCH_ENDPOINT = "quick-search"
ITEM_ENDPOINT = "item-types"
SEARCH_URL = "{}/{}".format(TEST_URL, SEARCH_ENDPOINT)
ITEM_URL = "{}/{}".format(TEST_URL, ITEM_ENDPOINT)
API_KEY = None


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
    return sorted(fake_item_types + ['PSScene3Band', 'PSScene4Band'])


@pytest.fixture()
def fake_response_small_aoi():
    with open('tests/resources/fake_response_small_aoi.json') as f:
        return json.load(f)


@pytest.fixture()
def fake_page_small_aoi():
    with open('tests/resources/fake_response_page.json') as f:
        return json.load(f)


@pytest.fixture
def geometry():
    with open('tests/resources/small_aoi.geojson') as f:
        geometry = json.load(f)
    return geometry['features'][0]['geometry']


@pytest.fixture
def fake_payload(geometry, fake_item_types):
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
        "config": geometry}

    and_filter = {
        "type": "AndFilter",
        "config": [date_range_filter, cloud_filter, geometry_filter]
    }

    search_request = {
        "item_types": fake_item_types,
        "filter": and_filter
    }
    return search_request


@vcr.use_cassette('tests/resources/fixtures/tests__get_vcr.yaml')
def test__get_vcr(fake_page_small_aoi):
    url = fake_page_small_aoi['_links'].get('_self')

    client = DataAPIClient(api_key=API_KEY)

    response = client._get(url)

    assert response == fake_page_small_aoi


@vcr.use_cassette('tests/resources/fixtures/tests__get_exception_vcr.yaml')
def test__get_exception_vrc(fake_page_small_aoi):
    url = 'https://api.planet.com/data/v1/searches/bad-url12345'

    client = DataAPIClient(api_key=API_KEY)
    try:
        response = client._get(url=url)
        assert False

    except requests.exceptions.HTTPError:
        assert True


@vcr.use_cassette('tests/resources/fixtures/test__get_auth_exception_vcr.yaml')
def test__get_auth_exception_vcr(fake_page_small_aoi):
    url = fake_page_small_aoi['_links'].get('_self')
    client = DataAPIClient(api_key='auth_exception')

    try:
        client._get(url)
        assert False
    except requests.exceptions.HTTPError:
        assert True


@vcr.use_cassette('tests/resources/fixtures/test__post_vcr.yaml')
def test__post_vcr(fake_page_small_aoi, fake_payload):
    url = SEARCH_URL
    client = DataAPIClient(api_key=API_KEY)
    response = client._post(url, json_data=fake_payload)

    assert response['features'] == fake_page_small_aoi['features']


@vcr.use_cassette('tests/resources/fixtures/test__query_vcr.yaml')
def test__query_vcr(fake_payload, fake_response_small_aoi):
    endpoint = SEARCH_ENDPOINT
    key = 'features'
    client = DataAPIClient(api_key=API_KEY)

    response = client._query(endpoint=endpoint,
                             key=key,
                             json_query=fake_payload)

    assert response == fake_response_small_aoi


@vcr.use_cassette('tests/resources/fixtures/test__query_paginate_vcr.yaml')
def test__query_paginate_vcr(fake_payload, fake_response_small_aoi, caplog):
    endpoint = SEARCH_ENDPOINT
    key = 'features'
    client = DataAPIClient(api_key=API_KEY)

    with caplog.at_level(logging.DEBUG):
        response = client._query(endpoint=endpoint,
                                 key=key,
                                 json_query=fake_payload)
        assert 'Paging results...' in caplog.text


@vcr.use_cassette('tests/resources/fixtures/test_get_items_vcr.yaml')
def test_get_items_vcr(fake_item_types_with_deprecated):
    """test if all item types are retrieved from data_api"""
    client = DataAPIClient(api_key=API_KEY)
    item_types = client.get_item_types(key='id')

    assert item_types == fake_item_types_with_deprecated


@vcr.use_cassette('tests/resources/fixtures/test_get_features_vcr.yaml')
def test_get_features_vcr(geometry, fake_response_small_aoi):
    """test if image_features are retrieved from data client correctly"""
    start_date = '2022-10-01'
    end_date = '2022-10-02'
    cc = 0.1

    client = DataAPIClient(api_key=API_KEY)
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
