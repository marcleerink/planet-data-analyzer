
import pytest
from urllib import response
from requests_mock import adapter
import os
import json
import mock
import vcr
import requests
import requests_mock
from tests.importer.fixtures import fake_response, geometry, cc, item_types, start_date, end_date,\
    payload, fake_api_key, payload, mock_response_429, mock_response_200, mock_response_300
from modules.importer.clients import get_item_types, handle_exception,  create_payload,\
     get_features, get_response, SEARCH_URL, api_importer, ITEM_TYPES, _paginate, RateLimitException

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

def test_get_features_success(fake_response):
    #arrange
    with mock.patch('modules.importer.api_importer.requests.post') as m:
        m.post.return_value.status_code.return_value = 200
        m.post.return_value.json.return_value = fake_response

        result = get_features(m)
        assert m.post.called
   


# def test_get_features_exception(mock_response_429):
    
#     #act
#     try:
#         result = get_features(mock_response_429)
#         assert False
#     except RateLimitException:
#         assert True
    

def test_api_importer_succes(item_types, start_date, end_date, cc, geometry, fake_api_key, mock_response_200):
    #arrange
    with mock_response_200:
        #act
        result = api_importer(api_key=fake_api_key,
                        item_types=item_types,
                        start_date=start_date, 
                        end_date=end_date,
                        cc=cc,
                        geometry=geometry)
    #assert
    assert isinstance(result, list)
    assert len(result) > 1
    assert all('https://api.planet.com/data/v1' in item['_links']['_self'] for item in result)

def test_api_importer_exception(item_types, start_date, end_date, cc, geometry, fake_api_key, mock_response_429):
    #arrange
    with mock_response_429:
        #act
        result = api_importer(api_key= fake_api_key,
                        item_types=item_types,
                        start_date=start_date, 
                        end_date=end_date,
                        cc=cc,
                        geometry=geometry)
    #assert
    assert isinstance(result, list)
    assert len(result) > 1
    assert all('https://api.planet.com/data/v1' in item['_links']['_self'] for item in result)

"""INTEGRATION"""
# def test_handle_exceptions_integration(payload):
#     #act
#     result = handle_exception(get_response(payload))
#     #assert
#     assert result == None

# def test_get_response_integration(payload):
#     #act 
#     result = get_response(payload)
#     #assert
#     assert result.status_code == 200


# def test_get_item_types_integration():
#     #act
#     result = get_item_types()

#     #assert
#     assert isinstance(result, list)
#     assert len(result) > 1
#     assert any('PS' in item for item in result)

# def test_get_features_integration(payload):
#     #act
#     result = get_features(get_response(payload))
    
#     #assert
#     assert isinstance(result, list)
#     assert len(result) > 1
#     assert all('https://api.planet.com/data/v1' in item['_links']['_self'] for item in result)

# def test_api_importer_integration(item_types, start_date, end_date, cc, geometry):
#     #act
#     result = api_importer(api_key= os.environ['PL_API_KEY'],
#                         item_types=item_types,
#                         start_date=start_date, 
#                         end_date=end_date,
#                         cc=cc,
#                         geometry=geometry)

#     #assert
#     assert isinstance(result, list)
#     assert len(result) > 1
#     assert all('https://api.planet.com/data/v1' in item['_links']['_self'] for item in result)
#     assert all(item['properties']['cloud_cover'] < cc for item in result)


    
    
    