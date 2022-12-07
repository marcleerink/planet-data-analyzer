import pandas as pd
import pytest
import json
import httplib2
from concurrent.futures import ThreadPoolExecutor

from database import db
from api_importer.clients.data import DataAPIClient, ImageDataFeature

from tests.integration.database.test_db_i import asset_type, db_session, setup_test_db
# TODO test rate limit
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
        feature.to_item_asset_model()
        feature.to_sat_image_model()

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
