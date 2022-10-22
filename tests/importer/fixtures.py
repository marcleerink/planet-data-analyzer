import pytest
import json
import requests
import requests_mock
import mock
import os

from modules.config import LOGGER
from modules.importer.api_importer import SEARCH_URL

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
    return 0.3

@pytest.fixture()
def geometry():
    return {'type': 'Polygon', 'coordinates': [[[12.463552, 52.169746], [12.463552, 52.862511], [14.305487, 52.862511], [14.305487, 52.169746], [12.463552, 52.169746]]]}

@pytest.fixture()
def payload():
    return {'item_types': ['Landsat8L1G', 'MOD09GA', 'MOD09GQ', 'MYD09GA', 'MYD09GQ', 'PSOrthoTile', 'PSScene', 'PSScene3Band', 'PSScene4Band', 'REOrthoTile', 'REScene', 'Sentinel1', 'Sentinel2L1C', 'SkySatCollect', 'SkySatScene', 'SkySatVideo'],
        'filter': {'type': 'AndFilter', 
        'config': [{'type': 'DateRangeFilter', 'field_name': 'acquired', 
        'config': {'gte': '2022-10-01T00:00:00.000Z', 'lte': '2022-10-02T00:00:00.000Z'}}, 
        {'type': 'RangeFilter', 'field_name': 'cloud_cover', 'config': {'lte': 0.3}}, 
        {'type': 'GeometryFilter', 'field_name': 'geometry', 
        'config': {'type': 'Polygon', 'coordinates': 
        [[[12.463552, 52.169746], [12.463552, 52.862511], [14.305487, 52.862511], [14.305487, 52.169746], [12.463552, 52.169746]]]}}]}}

@pytest.fixture()
def fake_api_key():
    return "PLAKfef2608cfa784a2baae1ed95ce314nn1"
    
@pytest.fixture()
def fake_response():
    with open('tests/resources/data_api_response.json', 'r') as f:
        return json.loads(f.read())
   

@pytest.fixture()
def mock_response_200(fake_response):
    adapter = requests_mock.Adapter()
    session = requests.Session()
    session.mount('https://', adapter)
    adapter.register_uri('POST', SEARCH_URL, json=fake_response, status_code=200)
    return session.post(SEARCH_URL)

@pytest.fixture()
def mock_response_300(fake_response):
    adapter = requests_mock.Adapter()
    session = requests.Session()
    session.mount('https://', adapter)
    adapter.register_uri('POST', SEARCH_URL, json=fake_response, status_code=300)
    return session.post(SEARCH_URL)

@pytest.fixture()
def mock_response_429(fake_response):
    adapter = requests_mock.Adapter()
    session = requests.Session()
    session.mount('https://', adapter)
    adapter.register_uri('POST', SEARCH_URL, json=fake_response, status_code=429)
    return session.post(SEARCH_URL)