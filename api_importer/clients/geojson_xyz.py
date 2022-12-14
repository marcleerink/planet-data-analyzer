from database import db
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
from geoalchemy2.shape import from_shape

from config import LOGGER
from database import db


def _get_client(client):
    if client is None:
        client = GeojsonXYZClient()
    return client


class GeojsonXYZClient(object):
    """
    Base client for working with the geojson-xyz API
    http://geojson.xyz/
    """
    base_url = "https://d2ad6b4ur7yvpq.cloudfront.net"

    def _url(self, endpoint):
        return '{}/{}'.format(self.base_url, endpoint)

    def _get(self, url, **params):
        rv = self.session.get(url, params=params)
        rv.raise_for_status()
        return rv.json()

    def _item(self, endpoint, **params):
        return self._get(self._url(endpoint), **params)

    def get_countries(self):
        endpoint = "naturalearth-3.3.0/ne_50m_admin_0_countries.geojson"
        features = gpd.read_file(self._url(endpoint)).to_dict(orient='records')

        LOGGER.info('{} countries found'.format(len(features)))
        for f in features:
            yield CountryFeature(f)

    def get_cities(self):
        endpoint = "naturalearth-3.3.0/ne_50m_populated_places.geojson"
        features = gpd.read_file(self._url(endpoint)).reset_index(names='id')\
            .to_dict(orient='records')
        LOGGER.info('{} cities found'.format(len(features)))
        for f in features:
            yield CityFeature(f)

    def get_rivers_lakes(self):
        endpoint = "naturalearth-3.3.0/ne_50m_rivers_lake_centerlines.geojson"
        return gpd.read_file(self._url(endpoint))

    def get_urban_areas(self):
        endpoint = "naturalearth-3.3.0/ne_50m_urban_areas.geojson"
        return gpd.read_file(self._url(endpoint))

    def get_land_cover_classes(self):
        gdf_urban = self.get_urban_areas()
        gdf_river = self.get_rivers_lakes()

        gdf_list = [gdf_urban,
                    gdf_river]

        features = pd.concat(gdf_list, axis=0, ignore_index=True).reset_index(names='id')\
            .to_dict(orient='records')
        LOGGER.info('{} land cover class features found'.format(len(features)))
        for f in features:
            yield LandCoverClassFeature(f)


class CountryFeature:
    """
    Represents a country feature its metadata.
    Imported from GeojsonXYZ API
    """

    def __init__(self, country_feature, client=None):
        """
        :param dict land_cover_feature:
            A dictionary containing metadata of a country feature.
        :param GeometryXYZClient client:
            A specific client instance to use. Will be created if not specified.
        """
        self.client = _get_client(client)

        for key, value in country_feature.items():
            setattr(self, key, value)

        self.iso = str(self.adm0_a3)
        self.name = str(self.name)
        self.geom = shape(self.geometry)

    def to_country_model(self):
        city = db.Country(
            iso=self.iso,
            name=self.name,
            geom=from_shape(self.geom, srid=4326),
        )
        db.sql_alch_commit(city)


class CityFeature:
    """
    Represents a city feature its metadata.
    Imported from GeojsonXYZ API
    """

    def __init__(self, city_feature, client=None):
        """
        :param dict land_cover_feature:
            A dictionary containing metadata of a city feature.
        :param GeometryXYZClient client:
            A specific client instance to use. Will be created if not specified.
        """
        self.client = _get_client(client)

        for key, value in city_feature.items():
            setattr(self, key, value)

        self.id = int(self.id)
        self.name = str(self.NAME).title()
        self.country_iso = str(self.ADM0_A3)
        self.geom = shape(self.geometry)

    def to_city_model(self):
        city = db.City(
            id=self.id,
            name=self.name,
            country_iso=self.country_iso,
            geom=from_shape(self.geom, srid=4326),
        )
        db.sql_alch_commit(city)


class LandCoverClassFeature:
    """
    Represents a landcoverclass feature its metadata.
    Imported from GeojsonXYZ API    
    """

    def __init__(self, land_cover_feature):
        """
        :param dict land_cover_feature:
            A dictionary containing metadata of a land cover class feature.

        """
        for key, value in land_cover_feature.items():
            setattr(self, key, value)

        self.id = int(self.id)
        self.featureclass = str(self.featureclass)
        self.geom = shape(self.geometry)

    def to_land_cover_model(self):
        land_cover_class = db.LandCoverClass(
            id=self.id,
            featureclass=self.featureclass,
            geom=from_shape(self.geom, srid=4326),
        )
        db.sql_alch_commit(land_cover_class)
