from email.mime import image
import pytest
from unittest import mock
import json
from shapely.geometry import shape
import pandas as pd
from modules.importer.clients.data import DataAPIClient

@pytest.fixture()
def item_types():
    return ['Landsat8L1G', 'MOD09GA', 'MOD09GQ', 'MYD09GA', 'MYD09GQ', 'PSOrthoTile', 'PSScene', 'PSScene3Band', 'PSScene4Band', 'REOrthoTile', 'REScene', 'Sentinel1', 'Sentinel2L1C', 'SkySatCollect', 'SkySatScene', 'SkySatVideo']

@pytest.fixture()
def start_date():
    return '2022-10-01'

@pytest.fixture()
def end_date():
    return '2022-10-02'

@pytest.fixture()
def cc():
    return 0.1

@pytest.fixture()
def geometry():
    with open('tests/resources/small_aoi.geojson') as f:
        geometry = json.load(f)
    return geometry['features'][0]['geometry']

def test_get_item_types():
    """test if filled list with item types is returned"""
    client = DataAPIClient()
    
    response = client.get_item_types(key='id')
    assert isinstance(response, list)
    assert len(response) > 1
    assert any('PS' in item for item in response)

def test_get_features(start_date, end_date, cc, geometry, item_types):
    """
    test if image_feature generator is returned with all necessary fields.
    """ 
    client = DataAPIClient()

    image_feature = next(client.get_features(start_date=start_date,
                                end_date=end_date,
                                cc=cc,
                                geometry=geometry,
                                item_types=item_types))
    
    assert image_feature.id is not None
    assert image_feature.sat_id is not None
    assert image_feature.item_type_id is not None
    assert image_feature.time_acquired is not None
    assert image_feature.pixel_res is not None
    assert image_feature.asset_types is not None
    assert image_feature.cloud_cover is not None
    assert image_feature.clear_confidence_percent is not None
    assert image_feature.geom is not None

def test_get_features_filter(start_date, end_date, cc, geometry, item_types):
    """test if api response is filtered"""
    client = DataAPIClient()
    end_date = '2022-10-05'
    item_types = ['PSScene', 'PSScene3Band', 'PSScene4Band', 'PSOrthoTile']
    
    dt_end_date = pd.to_datetime(end_date)
    dt_start_date = pd.to_datetime(start_date)
    
    

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

                                