import pytest
import json
import httplib2
from importer import river_lake_import
from modules.importer.clients.geojson_xyz import GeojsonXYZClient, CityFeature, CountryFeature
from tests.database.test_db_i import country

@pytest.fixture
def fake_cities():
    with open('tests/resources/fake_cities.geojson') as f:
        return json.load(f)

@pytest.fixture
def fake_countries():
    with open('tests/resources/fake_countries.geojson') as f:
        return json.load(f)

def test_conn():
    """test connection can be made to necessary geojson xyz urls"""
    client = GeojsonXYZClient()
    http = httplib2.Http()
    base_url = client.base_url
    country_url = '{}/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson'.format(base_url)
    city_url = '{}/naturalearth-3.3.0/ne_50m_populated_places_simple.geojson'.format(base_url)
    river_lake_url = '{}/naturalearth-3.3.0/ne_50m_rivers_lake_centerlines.geojson'.format(base_url)
    
    response_base = http.request(client.base_url, 'HEAD')
    response_country = http.request(country_url, 'HEAD')
    response_city = http.request(city_url, 'HEAD')
    response_river_lake = http.request(river_lake_url, 'HEAD')

    assert int(response_base[0]['status']) < 400
    assert int(response_country[0]['status']) < 400
    assert int(response_city[0]['status']) < 400
    assert int(response_river_lake[0]['status']) < 400

def test_get_countries_i():
    """
    test if all country features are retrieved from geojsonxyz 
    """
    client = GeojsonXYZClient()

    countries_list = list(client.get_countries())

    assert len(countries_list) > 200

def test_get_cities_i():
    """
    test if all city features are retrieved from geojsonxyz 
    """
    client = GeojsonXYZClient()

    cities_list = list(client.get_cities())

    assert len(cities_list) > 1000
    
def test_get_rivers_lakes():
    """
    test if all river/lake features are retrieved from geojsonxyz 
    """

    client = GeojsonXYZClient()

    river_lake_list = list(client.get_rivers_lakes())

    assert len(river_lake_list) > 400

def test_get_urban_areas():
    """
    test if all urban area features are retrieved from geojsonxyz 
    """
    client = GeojsonXYZClient()
    
    urban_area_list = list(client.get_urban_areas())

    assert len(urban_area_list) > 2000

