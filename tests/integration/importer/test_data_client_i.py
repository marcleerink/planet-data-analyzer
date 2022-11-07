import pandas as pd
import pytest
import json
import httplib2
from concurrent.futures import ThreadPoolExecutor

from modules.database import db
from modules.importer.clients.data import DataAPIClient, ImageDataFeature

from tests.integration.database.test_db_i import asset_type, db_session, setup_test_db

TEST_URL = "https://api.planet.com/data/v1"
SEARCH_ENDPOINT = "quick-search"
ITEM_ENDPOINT = "item-types"
SEARCH_URL = "{}/{}".format(TEST_URL, SEARCH_ENDPOINT)
ITEM_URL = "{}/{}".format(TEST_URL, ITEM_ENDPOINT)

@pytest.fixture
def fake_response_list():
    with open('tests/resources/fake_response.json') as f:
        return json.load(f)

@pytest.fixture()
def fake_response_small_aoi():
    with open('tests/resources/fake_response_small_aoi.json') as f:
        return json.load(f)

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

def test_conn():
    client = DataAPIClient()
    http = httplib2.Http()
    response_base = http.request(client.base_url, 'HEAD')
    assert int(response_base[0]['status']) == 200

def test_get_item_types_i(item_types):
    """test if filled list with item types is returned"""
    client = DataAPIClient()
    
    response = client.get_item_types(key='id')
    assert response == item_types

def test_get_features_i(geometry, fake_response_small_aoi):
    """
    test if image_features are retrieved from data client and ImageDataFeature 
    generator is returned with correct data.
    """ 
    start_date = '2022-10-01'
    end_date = '2022-10-02'
    cc = 0.1

    client = DataAPIClient()
    features = list(client.get_features(start_date=start_date,
                                end_date=end_date,
                                cc=cc,
                                geometry=geometry))
                                
    
    assert len(features) == len(fake_response_small_aoi)
    assert [i.id for i in features] == [str(i["id"]) for i in fake_response_small_aoi]


def test_get_features_filter_i(geometry):
    """test if api response is filtered"""
    start_date = '2022-10-03'
    end_date = '2022-10-05'
    cc = 0.1
    item_types = ['PSScene', 'PSOrthoTile']

    dt_end_date = pd.to_datetime(end_date)
    dt_start_date = pd.to_datetime(start_date)
    
    client = DataAPIClient()
    image_features_list = list(client.get_features(start_date=start_date,
                                end_date=end_date,
                                cc=cc,
                                geometry=geometry,
                                item_types=item_types))

    assert len(image_features_list) >= 1
    assert all(feature.cloud_cover <= cc for feature in image_features_list)
    assert all(pd.to_datetime(feature.time_acquired).tz_localize(None) <= dt_end_date for feature in image_features_list)
    assert all(pd.to_datetime(feature.time_acquired).tz_localize(None) >= dt_start_date for feature in image_features_list)
    assert all('PS' in feature.item_type_id for feature in image_features_list)
    
def test_to_postgis_in_parallel_i(fake_response_list, setup_test_db, db_session):
    """
    Test if all metadata from a feature is imported to tables in db correctly when done in parallel.
    """

    # get ImageDataFeatures list
    fake_features_list = [ImageDataFeature(f) for f in fake_response_list]
    
    # get unique values based on pkeys for each table/model.
    fake_sat_list = set([f.sat_id for f in fake_features_list])
    fake_item_type_list = set([f.item_type_id for f in fake_features_list])
    fake_image_list = set([f.id for f in fake_features_list])
    fake_asset_type_list = [sublist.asset_types for sublist in fake_features_list]
    fake_asset_type_list = set([i for sublist in fake_asset_type_list for i in sublist])
    
    
    def to_postgis(feature):
        feature.to_satellite_model()
        feature.to_item_type_model()
        feature.to_sat_image_model()
        feature.to_asset_type_model()

    with ThreadPoolExecutor(4) as executor:
        executor.map(to_postgis, fake_features_list)

    satellites_in_db = db_session.query(db.Satellite)
    item_types_in_db = db_session.query(db.ItemType)
    sat_images_in_db = db_session.query(db.SatImage)
    asset_types_in_db = db_session.query(db.AssetType)

    # assert that tables in db have same data as fake_features_list
    assert sorted(fake_sat_list) == sorted([i.id for i in satellites_in_db])
    assert sorted(fake_item_type_list) == sorted([i.id for i in item_types_in_db])
    assert sorted(fake_image_list) == sorted([i.id for i in sat_images_in_db])
    assert sorted(fake_asset_type_list) == sorted(i.id for i in asset_types_in_db)
    
