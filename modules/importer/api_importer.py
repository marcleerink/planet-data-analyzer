from re import S
import requests
import os
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from modules.importer import utils
from modules.config import LOGGER

def _get_client(client):
    if client is None:
        client = DataAPIClient()
    return client

class DataAPIClient(object):
    """Base client for working with the Planet Data API"""

    base_url = "https://api.planet.com/data/v1"
    
    def __init__(self, api_key=None):
        """
        :param str api_key:
            Your Planet API key. If not specified, this will be read from the
            PL_API_KEY environment variable.
        """
        if api_key is None:
            api_key = os.getenv('PL_API_KEY')
        self.api_key = api_key

        if self.api_key is None and 'internal' not in self.base_url:
            msg = 'You are not logged in! Please set the PL_API_KEY env var.'
            raise ValueError(msg)

        self.session = requests.Session()
        self.session.auth = (api_key, '')

        retries = Retry(total=5, backoff_factor=0.2, status_forcelist=[429, 503])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def _url(self, endpoint):
        return '{}/{}'.format(self.base_url, endpoint)

    def _get(self, url, **params):
        rv = self.session.get(url, params=params)
        rv.raise_for_status()
        return rv.json()

    def _post(self, url, json_data):
        rv = self.session.post(url, json=json_data)
        rv.raise_for_status()
        return rv.json()

    def _item(self, endpoint, **params):
        return self._get(self._url(endpoint), **params)

    def _paginate(self, url):
        """Navigates through the pages of an API response"""
        return self._get(url)

    def _query(self, endpoint, key, json_query):
        """Post and then get for pagination."""

        url = self._url(endpoint)
        page = self._post(url, json_query)
        features = page[key]

        while page['_links'].get('_next'):
            LOGGER.info("...Paging results...")
            page_url = page['_links'].get('_next')
            page = self._get(page_url)
            features += page["features"]
            
        return features
    
    def _payload(self, item_types, start_date, end_date, cc, geometry):
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

    def get_item_types(self, key='id'):
        """
        gets all available item type ids from Planets Data API

        :param str key
            Key to return results for. Defaults to 'id'.
        """
        
        endpoint = 'item-types'
        items = self._item(endpoint=endpoint)
        item_types = items['item_types']
        return [item[key] for item in item_types]

    def get_features(self, start_date=None, end_date=None, 
                    cc=None, geometry=None, item_types=None):
        """
        Gets all features from quick search end-point with specified filters.

        :param str start_date
            Start date of the time interval to filter search results by, 
            in ISO (YYYY-MM-DD)(gte)
        :param str end_date
            End date of the time interval to filter search results by,
            in ISO (YYYY-MM-DD)(lte)
        :param float cc
            Max cloud cover value to filter results by (0.0 - 1.0).
        :param dict geometry
            A GeoJSON polygon to filter results by.
        :param list item_types
            Item types to filter results by. Gets all available item_types if none provided.
        
        :returns list features
            A list containing all the features from the api response.
        """

        endpoint = 'quick-search'
        key = 'features'
        if not item_types:
            item_types= self.get_item_types()

        payload = self._payload(start_date=start_date,
                                end_date=end_date,
                                cc=cc,
                                geometry=geometry,
                                item_types=item_types)
        
        return self._query(endpoint=endpoint, 
                        json_query=payload,
                        key=key)

def api_importer(args):
    """
    Imports features from Planets Data API for all features in AOI,TOI, below provided cloud cover threshold
    If item types are provided only searches for those, otherwise searches all available item_types
    """
    client = DataAPIClient()
    geometry = utils.geojson_import(args.get('aoi_file'))
    
    features = client.get_features(start_date=args.get('start_date'),
                                end_date=args.get('end_date'), 
                                cc=args.get('cc'),
                                geometry=geometry)

    LOGGER.info("Total items found: {}".format(len(features)))
    
    return features



