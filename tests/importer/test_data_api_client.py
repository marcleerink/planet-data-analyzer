from datetime import datetime
from email.mime import image
import pytest
from unittest import mock
import json
from shapely.geometry import shape
import pandas as pd
from modules.importer.clients.data import DataAPIClient, ImageDataFeature
from tests.resources import fake_feature
import respx
import httpx
from http import HTTPStatus
import requests
import requests_mock

TEST_URL = 'http://www.MockNotRealURL.com/api/path'
TEST_SEARCHES_URL = f'{TEST_URL}/searches'
TEST_STATS_URL = f'{TEST_URL}/stats'

@pytest.fixture
def item_types():
    return ['Landsat8L1G', 
            'MOD09GA', 
            'MOD09GQ', 
            'MYD09GA', 
            'MYD09GQ', 
            'PSOrthoTile', 
            'PSScene', 
            'PSScene3Band', 
            'PSScene4Band', 
            'REOrthoTile', 
            'REScene', 
            'Sentinel1', 
            'Sentinel2L1C', 
            'SkySatCollect', 
            'SkySatScene', 
            'SkySatVideo']

@pytest.fixture
def geometry():
    with open('tests/resources/small_aoi.geojson') as f:
        geometry = json.load(f)
    return geometry['features'][0]['geometry']

@pytest.fixture()
def mock_session():
    adapter = requests_mock.Adapter()
    session = requests.Session()
    session.auth = requests.auth.HTTPBasicAuth('dummy', '')
    
    session.mount('https://', adapter)
    return session
    # adapter.register_uri('POST', TEST_URL, json=fake_response, status_code=200)
    # return session.post(TEST_URL)

@pytest.fixture
def item_descriptions():
    item_ids = [
        '20220125_075509_67_1061',
        '20220125_075511_17_1061',
        '20220125_075650_17_1061'
    ]
    items = []
    for id in item_ids:
        with open(f'tests/resources/data_item_{id}.json') as f:
            items.append(json.load(f))

    return items


"""
UNIT
"""


def test_data_client_basic(item_descriptions,
                            geometry,
                            item_types,
                            mock_session):
    quick_search_url = f'{TEST_URL}/quick-search'
    next_page_url = f'{TEST_URL}/blob/?page_marker=IAmATest'

    start_date = '2022-10-01'
    end_date = '2022-10-02'
    cc = 0.1

    item1, item2, item3 = item_descriptions
    page1_response = {
        "_links": {
            "_next": next_page_url
        }, "features": [item1, item2]
    }
    
    client = DataAPIClient(session=mock_session)
    client.base_url = TEST_URL

    feature_generator = client.get_features(start_date=start_date,
                                        end_date=end_date,
                                        cc=cc,
                                        geometry=geometry,
                                        item_types=item_types)
                            
    
    for i in feature_generator:
        assert i.id == '20220125_075509_67_1061'

    assert feature_generator == item_descriptions


"""
INTEGRATION
"""
def test_get_item_types_i():
    """test if filled list with item types is returned"""
    client = DataAPIClient()
    
    response = client.get_item_types(key='id')
    assert isinstance(response, list)
    assert len(response) > 1
    assert any('PS' in item for item in response)

def test_get_features(geometry, item_types):
    """
    test if image_feature generator is returned with correct data.
    """ 
    start_date = '2022-10-01'
    end_date = '2022-10-02'
    cc = 0.1

    client = DataAPIClient()
    image_features = client.get_features(start_date=start_date,
                                end_date=end_date,
                                cc=cc,
                                geometry=geometry,
                                item_types=item_types)
                                
    image_feature = image_features[0]
    assert isinstance(image_feature.id, str)
    assert isinstance(image_feature.sat_id, str)
    assert isinstance(image_feature.item_type_id, str)
    assert isinstance(image_feature.time_acquired, datetime)
    assert isinstance(image_feature.pixel_res, float)
    assert isinstance(image_feature.asset_types, list)
    assert isinstance(image_feature.cloud_cover, float)
    assert isinstance(image_feature.clear_confidence_percent, int)
    assert image_feature.geom.geom_type == 'Polygon' or image_feature.geom.geom_type == 'MultiPolygon'


def test_get_features_filter(geometry, item_types):
    """test if api response is filtered"""
    start_date = '2022-10-03'
    end_date = '2022-10-05'
    cc = 0.1
    item_types = ['PSScene', 'PSScene3Band', 'PSScene4Band', 'PSOrthoTile']

    dt_end_date = pd.to_datetime(end_date)
    dt_start_date = pd.to_datetime(start_date)
    
    client = DataAPIClient()
    image_features_list = client.get_features(start_date=start_date,
                                end_date=end_date,
                                cc=cc,
                                geometry=geometry,
                                item_types=item_types)
    
    assert len(image_features_list) >= 1
    assert all(feature.cloud_cover <= cc for feature in image_features_list)
    assert all(pd.to_datetime(feature.time_acquired).tz_localize(None) <= dt_end_date for feature in image_features_list)
    assert all(pd.to_datetime(feature.time_acquired).tz_localize(None) >= dt_start_date for feature in image_features_list)
    assert all('PS' in feature.item_type_id for feature in image_features_list)

def test_ImageDataFeature():
    """test if all metadata from a feature is stored correctly"""
    feature = fake_feature.feature

    image_feature = ImageDataFeature(feature)
    
    assert image_feature.id == str(feature["id"])
    assert image_feature.sat_id == str(feature["properties"]["satellite_id"])
    assert image_feature.time_acquired == pd.to_datetime(feature["properties"]["acquired"])
    assert image_feature.satellite == str(feature["properties"]["provider"].title())
    assert image_feature.pixel_res == float(feature["properties"]["pixel_resolution"])
    assert image_feature.item_type_id == str(feature["properties"]["item_type"])
    assert image_feature.asset_types == list(feature["assets"])
    assert image_feature.cloud_cover == float(feature["properties"]["cloud_cover"])
    assert image_feature.geom == shape(feature["geometry"])
    
# def test_to_sattellite_model(setup_test_db, db_session):
#     """test if metadata from a feature is imported to db correctly"""
#     feature = fake_feature.feature
#     image_feature = ImageDataFeature(feature)

#     image_feature.to_satellite_model()

#     satellites = db_session.query(Satellite).all()
#     for sat in satellites:
#         assert sat.id == str(feature["properties"]["satellite_id"])

# def test_to_item_type_model(setup_test_db, db_session):
#     feature = fake_feature.feature
#     image_feature = ImageDataFeature(feature)

#     image_feature.to_item_type_model()

#     item_types = db_session.query(ItemType).all()
#     for item in item_types:
#         assert item.id == str(feature["properties"]["item_type"])
