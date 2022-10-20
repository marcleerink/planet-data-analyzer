

from urllib import response
from requests_mock import adapter
import os
import json
import mock
from tests.importer.fixtures import fake_response, geometry, cc, item_types, start_date, end_date,\
    payload, planet_session, payload, mock_session, mock_response_429, mock_response_200, mock_response_300
from modules.importer.api_importer import get_item_types, handle_exception,  create_payload,\
     get_features, get_planet_api_session, get_response, SEARCH_URL, api_importer, ITEM_TYPES, _paginate, RateLimitException

from modules.config import LOGGER



"""UNIT"""
def test_create_payload(payload, 
                        item_types, 
                        start_date, 
                        end_date, 
                        cc, 
                        geometry):
    #act
    response = create_payload(item_types=item_types,
                        start_date=start_date,
                        end_date=end_date,
                        cc=cc,
                        geometry=geometry) 
    #assert
    assert response == payload

def test_handle_exceptions(mock_response_429, mock_response_200, mock_response_300):
    """ Test if exceptions are caught appropriately"""
    try:
        handle_exception(mock_response_429)
        assert False
    except RateLimitException:
        assert True
    try:
        handle_exception(mock_response_300)
        assert False
    except Exception:
        assert True
    
    assert handle_exception(mock_response_200) == None

# def test_get_response(payload, fake_response):
#     with requests_mock.Mocker() as mock_session:
#         #arrange
#         mock_session.register_uri('POST', SEARCH_URL, json=fake_response, status_code=200)

#         #act
#         response = get_response(mock_session,payload)

#         #assert
#         assert response.json() == fake_response

# def test_get_features(fake_response, mock_session, mock_response):
#     features = get_features(mock_session, mock_response)
#     assert features.status_code == fake_response

# def test_get_response(mock_session, payload, fake_response):
#     LOGGER.info(mock_session.status_code)
#     response = get_response(mock_session,payload)
#     assert response.json() == fake_response


"""INTEGRATION"""
def test_handle_exceptions_integration(planet_session, payload):
    #act
    result = handle_exception(get_response(planet_session, payload))
    #assert
    assert result == None

def test_get_response_integration(planet_session, payload):
    #act 
    result = get_response(planet_session, payload)
    #assert
    assert result.status_code == 200


def test_get_item_types_integration(planet_session):
    #act
    result = get_item_types(planet_session)

    #assert
    assert isinstance(result, list)
    assert len(result) > 1
    assert any('PS' in item for item in result)

def test_get_features_integration(planet_session, payload):
    #act
    result = get_features(planet_session, get_response(planet_session, payload))
    
    #assert
    assert isinstance(result, list)
    assert len(result) > 1
    assert all('https://api.planet.com/data/v1' in item['_links']['_self'] for item in result)

def test_api_importer_integration(item_types, start_date, end_date, cc, geometry):
    #act
    result = api_importer(api_key= os.environ['PL_API_KEY'],
                        item_types=item_types,
                        start_date=start_date, 
                        end_date=end_date,
                        cc=cc,
                        geometry=geometry)

    #assert
    assert isinstance(result, list)
    assert len(result) > 1
    assert all('https://api.planet.com/data/v1' in item['_links']['_self'] for item in result)
    assert all(item['properties']['cloud_cover'] < cc for item in result)


    
    
    