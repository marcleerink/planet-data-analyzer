from datetime import datetime
import pytest
import json
from shapely.geometry import shape
import pandas as pd
import requests
import requests_mock

from modules.importer.clients.data import ImageDataFeature
from tests.resources import fake_feature

TEST_URL = 'http://www.MockNotRealURL.com/api/path'
TEST_SEARCHES_URL = f'{TEST_URL}/searches'
TEST_STATS_URL = f'{TEST_URL}/stats'



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

@pytest.fixture
def fake_response_list():
    with open('tests/resources/fake_response.json') as f:
        return json.load(f)


# def test_data_client_basic(item_descriptions,
#                             geometry,
#                             item_types,
#                             mock_session):
#     quick_search_url = f'{TEST_URL}/quick-search'
#     next_page_url = f'{TEST_URL}/blob/?page_marker=IAmATest'

#     start_date = '2022-10-01'
#     end_date = '2022-10-02'
#     cc = 0.1

#     item1, item2, item3 = item_descriptions
#     page1_response = {
#         "_links": {
#             "_next": next_page_url
#         }, "features": [item1, item2]
#     }
    
#     client = DataAPIClient(session=mock_session)
#     client.base_url = TEST_URL

#     feature_generator = client.get_features(start_date=start_date,
#                                         end_date=end_date,
#                                         cc=cc,
#                                         geometry=geometry,
#                                         item_types=item_types)
                            
    
#     for i in feature_generator:
#         assert i.id == '20220125_075509_67_1061'

#     assert feature_generator == item_descriptions

def test_ImageDataFeature():
    """test if all metadata from a feature is converted correctly"""
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

def test_ImageDataFeature_list(fake_response_list):
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



    


