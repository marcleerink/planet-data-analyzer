import requests
import logging
from retrying import retry
import pandas as pd


# Logger
logger = logging.getLogger(__name__)

SEARCH_URL = "https://api.planet.com/data/v1/quick-search"
ITEM_TYPES = 'https://api.planet.com/data/v1/item-types'


class RateLimitException(Exception):
    pass


def _retry_if_rate_limit_error(exception):
    return isinstance(exception, RateLimitException)

@retry(
    wait_exponential_multiplier=1000,
    wait_exponential_max=10000,
    retry_on_exception=_retry_if_rate_limit_error,
    stop_max_attempt_number=5)
def _paginate(session, url):
    """Navigates through the pages of an API response"""
    response = session.get(url)

    while response.status_code == 429:
        logger.debug("We got 429 error, retrying!")
        raise RateLimitException("Rate limit error")

    if response.status_code > 299:
        logger.error("Error when paginating through results")
        logger.error("HTTP code {}: {}\n".format(response.status_code, response.reason))
        page = {"_links": {"_next": url}, "features": []}
    else:
        page = response.json()

    return page

@retry(
    wait_exponential_multiplier=1000,
    wait_exponential_max=10000,
    retry_on_exception=_retry_if_rate_limit_error,
    stop_max_attempt_number=5)
def search(session, search_request):
    """Created a search filter using the input payload and makes calls to the Data API quick-search endpoints returning
    all features in API response"""


    # Search API request
    logger.info("Searching {} - {}".format(SEARCH_URL, search_request))
    response = session.post(SEARCH_URL, json=search_request, params={"strict": "true"})
    
    # Exponential back-off, uo to 5 times retry
    while response.status_code == 429:
        logger.debug("We got 429, retrying!")
        raise RateLimitException("Rate limit error")

    if response.status_code == 200:
        page = response.json()
        features = page["features"]
        while page['_links'].get('_next'):
            logger.debug("...Paging results...")
            page_url = page['_links'].get('_next')
            page = _paginate(session, page_url)
            features += page["features"]
        return features
    else:
        raise Exception("Search failed with error {}: {} -> {}".format(response.status_code, response.reason,
                                                                       response.text))

def search_requester(item_types, start_date, end_date, cc, geometry):
    # Create search payload with full geometry and full TOI
    payload = {
        "item_types": item_types,  # Default item type to search for
        "gte": start_date,
        "lt": end_date,
        "cc": cc
    }

    date_range_filter = {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {
            "gte": payload["gte"] + "T00:00:00.000Z",
            "lte": payload["lt"] + "T00:00:00.000Z"
        }
    }

    cloud_filter = {
        "type": "RangeFilter",
        "field_name": "cloud_cover",
        "config": {
            "lte": payload["cc"]
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
        "item_types": payload["item_types"],
        "filter": and_filter
    }
    return search_request

def do_search(api_key=None, item_types=None, start_date=None, end_date=None, cc=None, geometry=None):
    # Start Planet Session
    session = requests.Session()
    session.auth = requests.auth.HTTPBasicAuth(api_key, '')

    item_types = [item_types] if not isinstance(item_types, list) else item_types
    
    
    # create search request with filters
    search_request = search_requester(item_types, start_date, end_date, cc, geometry)

    # Search for items
    items = search(session, search_request)
    
    logger.info("Total items found: {}".format(len(items)))

    items_df = pd.DataFrame(items)
    print(items_df)
    return items_df.to_dict('index')




