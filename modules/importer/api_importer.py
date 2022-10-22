import requests
from retrying import retry
import os
from modules.config import LOGGER


SEARCH_URL = "https://api.planet.com/data/v1/quick-search"
ITEM_TYPES = 'https://api.planet.com/data/v1/item-types'


def handle_exception(response):
    if response.status_code == 200:
        return
    while response.status_code == 429:
        LOGGER.debug("We got 429 error, retrying!")
        raise RateLimitException("Rate limit error")

    if response.status_code > 299:
        LOGGER.error("Error getting results")
        raise Exception("HTTP code {}: {}\n".format(response.status_code, response.reason))
    else:
        raise Exception("Search failed with error {}: {} -> {}".format(response.status_code, response.reason,
                                                                       response.text))

class RateLimitException(Exception):
    pass

def _retry_if_rate_limit_error(exception):
    return isinstance(exception, RateLimitException)

def get_item_types():
    """gets all available item types from Planets Data API"""
    response = requests.get(ITEM_TYPES, auth=(os.environ['PL_API_KEY'],''))
    
    if response.status_code == 200:
        items = response.json()
        item_types = items['item_types']
        return [item['id'] for item in item_types]
    else:
        handle_exception(response)

@retry(
    wait_exponential_multiplier=1000,
    wait_exponential_max=10000,
    retry_on_exception=_retry_if_rate_limit_error,
    stop_max_attempt_number=5)
def _paginate(url):
    """Navigates through the pages of an API response"""
    response = requests.get(url, auth=(os.environ['PL_API_KEY'],''))
    if response.status_code == 200:
        return response.json()
    else:
        handle_exception(response)

@retry(
    wait_exponential_multiplier=1000,
    wait_exponential_max=10000,
    retry_on_exception=_retry_if_rate_limit_error,
    stop_max_attempt_number=5)
def get_features(response):
    if response.status_code == 200:
        page = response.json()
        features = page["features"]
        while page['_links'].get('_next'):
            LOGGER.info("...Paging results...")
            page_url = page['_links'].get('_next')
            page = _paginate(page_url)
            features += page["features"]
    else:
        handle_exception(response)
    return features

@retry(
    wait_exponential_multiplier=1000,
    wait_exponential_max=10000,
    retry_on_exception=_retry_if_rate_limit_error,
    stop_max_attempt_number=5)
def get_response(search_request):
    """
    Makes calls to the Data API quick-search endpoints returning the response
    """
    response = requests.post(SEARCH_URL, 
                            json=search_request, 
                            auth=(os.environ['PL_API_KEY'],''))
    if response.status_code == 200:
        return response
    else:
        handle_exception(response)

def create_payload(item_types, start_date, end_date, cc, geometry):
    """
    Create search payload with geometry, cloud filter and TOI
    """
    date_range_filter = {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {
            "gte": start_date + "T00:00:00.000Z",
            "lte": end_date + "T00:00:00.000Z"
        }
    }

    cloud_filter = {
        "type": "RangeFilter",
        "field_name": "cloud_cover",
        "config": {
            "lte": cc
        }
    }

    geometry_filter = {
        "type": "GeometryFilter",
        "field_name": "geometry",
        "config":geometry}

    and_filter = {
        "type": "AndFilter",
        "config": [date_range_filter, cloud_filter, geometry_filter]
    }

    search_request = {
        "item_types": item_types,
        "filter": and_filter
    }
    return search_request


def api_importer(api_key=None, item_types=None, start_date=None, end_date=None, cc=None, geometry=None):
    """
    Imports items from Planets Data API for all items in AOI,TOI, below provided cloud cover threshold
    If item types are provided only searches for those, otherwise searches all item_types
    """

    # get all item_types if none provided
    item_types = get_item_types() if not item_types else item_types

    LOGGER.info(f'Searching for item types:{item_types}')

    # create search request payload with filters
    search_request = create_payload(item_types, start_date, end_date, cc, geometry)

    # Search for items
    response = get_response(search_request)
    items = get_features(response)

    LOGGER.info("Total items found: {}".format(len(items)))

    return items




