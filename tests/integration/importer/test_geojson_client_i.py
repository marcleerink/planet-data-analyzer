import pytest
import httplib2
from concurrent.futures import ThreadPoolExecutor
import geopandas as gpd
import pandas as pd

from database import db
from api_importer.clients.geojson_xyz import GeojsonXYZClient, CityFeature,\
                                             CountryFeature, LandCoverClassFeature
from tests.integration.database.test_db_i import db_session, setup_test_db

@pytest.fixture
def fake_cities():
    return gpd.read_file('tests/resources/fake_cities.geojson').reset_index(names='id')\
                                                    .to_dict(orient='records')

@pytest.fixture
def fake_countries():
        return gpd.read_file('tests/resources/fake_countries.geojson').reset_index(names='id')\
                                                    .to_dict(orient='records')
        
@pytest.fixture
def fake_land_cover():
        rivers_lakes = gpd.read_file('tests/resources/fake_rivers_lakes.geojson')
        urban_areas = gpd.read_file('tests/resources/fake_urban_areas.geojson')
        gdf_list = [rivers_lakes, urban_areas]

        return pd.concat(gdf_list, axis=0, ignore_index=True).reset_index(names='id')\
                                                            .to_dict(orient='records')


def test_conn():
    """test if connection can be made to necessary geojson xyz urls"""
    client = GeojsonXYZClient()
    http = httplib2.Http()
    base_url = client.base_url
    country_url = '{}/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson'.format(base_url)
    city_url = '{}/naturalearth-3.3.0/ne_50m_populated_places_simple.geojson'.format(base_url)
    river_lake_url = '{}/naturalearth-3.3.0/ne_50m_rivers_lake_centerlines.geojson'.format(base_url)
    urban_area_url = '{}/naturalearth-3.3.0/ne_50m_urban_areas.geojson'.format(base_url)
    
    response_base = http.request(client.base_url, 'HEAD')
    response_country = http.request(country_url, 'HEAD')
    response_city = http.request(city_url, 'HEAD')
    response_river_lake = http.request(river_lake_url, 'HEAD')
    response_urban_area = http.request(urban_area_url, 'HEAD')

    assert int(response_base[0]['status']) == 200
    assert int(response_country[0]['status']) == 200
    assert int(response_city[0]['status']) == 200
    assert int(response_river_lake[0]['status']) == 200
    assert int(response_urban_area[0]['status']) == 200

def test_to_postgis_in_parallel_i(fake_countries, fake_cities, fake_land_cover, db_session, setup_test_db):
    """
    Test if all data from geojson xyz is imported to tables in db correctly when done in parallel.
    """
    
    # get ImageDataFeatures list
    fake_country_list = [CountryFeature(f) for f in fake_countries]
    fake_city_list = [CityFeature(f) for f in fake_cities]
    fake_land_cover_list = [LandCoverClassFeature(f) for f in fake_land_cover]

    def to_country(f):
        f.to_country_model()

    def to_city(f):
        f.to_city_model()

    def to_land_cover(f):
        f.to_land_cover_model()

    with ThreadPoolExecutor() as executor:
        executor.map(to_country, fake_country_list)
        executor.map(to_city, fake_city_list)
        executor.map(to_land_cover, fake_land_cover_list)
        
    countries_in_db = db_session.query(db.Country)
    cities_in_db = db_session.query(db.City)
    land_cover_in_db = db_session.query(db.LandCoverClass)
   
    # assert that tables in db have same data as fakes
    assert sorted(i.iso for i in fake_country_list) == sorted([i.iso for i in countries_in_db])
    assert sorted(i.name for i in fake_city_list) == sorted([i.name for i in cities_in_db])
    assert sorted(i.featureclass for i in fake_land_cover_list) == sorted([i.featureclass for i in land_cover_in_db])
   