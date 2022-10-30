import requests
import os
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from shapely.geometry import shape
from geoalchemy2.shape import from_shape
from concurrent.futures import ThreadPoolExecutor
from modules.config import LOGGER

from modules.database import db

def _get_client(client):
    if client is None:
        client = DataAPIClient()
    return client

class DataAPIClient:
    """
    Base client for working with the Planet Data API.
    https://developers.planet.com/docs/apis/data/
    """
    
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

    def _payload(self, item_types, start_date, end_date, cc, geometry):
        """Create search payload with geometry, cloud filter and TOI """

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

    def get_item_types(self, key=None):
        """
        Gall available item types from Planets Data API

        :param str key
            Key to return results for.

        returns list of item type
        """
        
        endpoint = 'item-types'
        items = self._item(endpoint=endpoint)
        item_types = items['item_types']
        return [item[key] for item in item_types]
        
    def get_features(self, start_date=None, end_date=None, 
                    cc=None, geometry=None, item_types=None):
        """
        Gets all features from quick search end-point with specified filters.
        Yields ``ImageDataFeature`` instances.

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
      
        """
        
        endpoint = 'quick-search'
        key = 'features'
        if not item_types:
            item_types = self.get_item_types(key='id')
            

        payload = self._payload(start_date=start_date,
                                end_date=end_date,
                                cc=cc,
                                geometry=geometry,
                                item_types=item_types)
        
        features = self._query(endpoint=endpoint, 
                                json_query=payload,
                                key=key)
        LOGGER.info('Found {} features'.format(len(features)))
        for feature in features:
            yield ImageDataFeature(feature)


class ImageDataFeature:
    """
    Represents a image feature its metadata. 
    Imported from Planets Data API.
    """
    def __init__(self, image_feature, client=None):
        """
        :param dict image_feature:
            A dictionary containing metadata of a image from the Data API.
        :param DataAPIClient client:
            A specific client instance to use. Will be created if not specified.
        """
        self.client = _get_client(client)

        for key, value in image_feature.items():
            setattr(self, key, value)
        self.sat_id = self.properties["satellite_id"]
        self.time_acquired = self.properties["acquired"]
        self.published = self.properties["published"]
        self.satellite = self.properties["provider"].title()
        self.pixel_res = self.properties["pixel_resolution"]
        self.item_type_id = self.properties["item_type"]
        self.asset_types = self.assets
        self.cloud_cover = self.properties["cloud_cover"] \
            if "cloud_cover" in self.properties else 0
        self.clear_confidence_percent = self.properties["clear_confidence_percent"] \
            if "clear_confidence_percent" in self.properties else 0
        self.geom = shape(self.geometry)
        
        
    def to_dict(self):
        return vars(self)

    def to_satellite_model(self):
        satellite = db.Satellite(
            id = self.sat_id,
            name = self.satellite,
            pixel_res = self.pixel_res)
        db.sql_alch_commit(satellite)

    def to_item_type_model(self):
        item_type = db.ItemType(
            id = self.item_type_id,
            sat_id = self.sat_id)
        db.sql_alch_commit(item_type)
    
    def to_sat_image_model(self):
        sat_image = db.SatImage(
                id = self.id, 
                clear_confidence_percent = self.clear_confidence_percent,
                cloud_cover = self.cloud_cover,
                time_acquired = self.time_acquired,
                centroid = from_shape(self.geom, srid=4326),
                geom = from_shape(self.geom, srid=4326),
                sat_id = self.sat_id,
                item_type_id = self.item_type_id
                )
        db.sql_alch_commit(sat_image)
    
    def to_asset_type_model(self):
        for id in self.asset_types:
            asset_type = db.AssetType(
                id = id)
            db.sql_alch_commit(asset_type)
    
   
class LandCoverClassFeature:
    """
    Represents a landcoverclass feature its metadata.
    Imported from Planets Data API.
    """
    def __init__(self, land_cover_feature):
        """
        :param dict land_cover_feature:
            A dictionary containing metadata of a land cover class feature.
        
        """
        for key, value in land_cover_feature.items():
            setattr(self, key, value)
        self.id = self.id
        self.featureclass = self.featureclass
        self.geom = shape(self.geom)

    def to_dict(self):
        return vars(self)

    def _sql_alch_commit(self,model):
        session = db.get_db_session()
        session.add(model)
        session.commit()

    def to_land_cover_model(self):
        land_cover_class = db.LandCoverClass(
                id = self.id, 
                featureclass = self.featureclass,
                geom = from_shape(self.geom, srid=4326),
                )
        self._sql_alch_commit(land_cover_class)


    