
import pytest
import requests
import requests_mock
from requests_mock import adapter
import os, json
import mock
from modules.importer.api_importer import handle_exception,  create_payload,\
     get_features, get_planet_api_session, get_response, SEARCH_URL, searcher

from modules.config import LOGGER, POSTGIS_URL

@pytest.fixture()
def item_types():
    return ['PSScene', 'SkySatScene']

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
    return {'item_types': ['PSScene','SkySatScene'],
        'filter': {'type': 'AndFilter', 
        'config': [{'type': 'DateRangeFilter', 'field_name': 'acquired', 
        'config': {'gte': '2022-10-01T00:00:00.000Z', 'lte': '2022-10-02T00:00:00.000Z'}}, 
        {'type': 'RangeFilter', 'field_name': 'cloud_cover', 'config': {'lte': 0.3}}, 
        {'type': 'GeometryFilter', 'field_name': 'geometry', 
        'config': {'type': 'Polygon', 'coordinates': 
        [[[12.463552, 52.169746], [12.463552, 52.862511], [14.305487, 52.862511], [14.305487, 52.169746], [12.463552, 52.169746]]]}}]}}


def test_create_payload(payload, 
                        item_types, 
                        start_date, 
                        end_date, 
                        cc, 
                        geometry):
    assert create_payload(item_types=item_types,
                                    start_date=start_date,
                                    end_date=end_date,
                                    cc = cc,
                                    geometry=geometry) == payload
@pytest.fixture()
def fake_response():
    with open('tests/resources/data_api_response.json', 'r') as f:
        return json.loads(f.read())

@pytest.fixture()
def mock_session():
     with mock.patch('modules.importer.api_importer.requests.Session') as mock_session:
        mock_session.return_value.status_code = 200
        return mock_session
   

@pytest.fixture()
def mock_response(fake_response):
    adapter = requests_mock.Adapter()
    session = requests.Session()
    session.mount('https://', adapter)
    adapter.register_uri('POST', SEARCH_URL, json=fake_response, status_code=200)
    return session.post(SEARCH_URL)

def test_get_response(payload, fake_response):
    with requests_mock.Mocker() as mock_session:
        #arrange
        mock_session.register_uri('POST', SEARCH_URL, json=fake_response, status_code=200)

        #act
        response = get_response(mock_session,payload)

        #assert
        assert response.json() == fake_response

def test_get_features(fake_response, mock_session, mock_response):
    features = get_features(mock_session, mock_response)
    assert features.status_code == fake_response


# def test_get_response(mock_session, payload, fake_response):
#     LOGGER.info(mock_session.status_code)
#     response = get_response(mock_session,payload)
#     assert response.json() == fake_response