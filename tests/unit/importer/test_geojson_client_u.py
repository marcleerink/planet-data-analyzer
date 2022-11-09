import pytest
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
import vcr

from api_importer.clients.geojson_xyz import \
    GeojsonXYZClient, CityFeature, CountryFeature, LandCoverClassFeature

@pytest.fixture
def fake_countries():
        return gpd.read_file('tests/resources/fake_countries.geojson').reset_index(names='id')\
                                                               .to_dict(orient='records')

@pytest.fixture
def fake_cities():
    return gpd.read_file('tests/resources/fake_cities.geojson').reset_index(names='id')\
                                                    .to_dict(orient='records')

@pytest.fixture
def fake_rivers_lakes():
    return gpd.read_file('tests/resources/fake_rivers_lakes.geojson')

@pytest.fixture
def fake_urban_areas():
    return gpd.read_file('tests/resources/fake_urban_areas.geojson')

@pytest.fixture
def fake_land_cover(fake_rivers_lakes, fake_urban_areas):
    gdf_list = [fake_rivers_lakes, fake_urban_areas]
    return pd.concat(gdf_list, axis=0, ignore_index=True).reset_index(names='id')\
                                                        .to_dict(orient='records')

@vcr.use_cassette('tests/resources/fixtures/test_get_countries_vcr.yaml')
def test_get_countries_vcr(fake_countries):
    """
    test if all countries are retrieved from geojsonxyz and 
    CountryFeature instances returned with correct data.
    """
    client = GeojsonXYZClient()

    country_list = list(client.get_countries())
    country = country_list[0]
    
    assert len(country_list) == 241
    assert country.iso == str(fake_countries[0]['adm0_a3'])
    assert country.name == str(fake_countries[0]['name'])
    assert country.geom == shape(fake_countries[0]['geometry'])

@vcr.use_cassette('tests/resources/fixtures/test_get_cities_vcr.yaml')
def test_get_cities_vcr(fake_cities):
    """
    test if all cities are retrieved from geojsonxyz and
    CityFeature instances returned with correct data
    """
    client = GeojsonXYZClient()
    
    # get first 8 instances
    cities_list = list(client.get_cities())
    city = cities_list[0]
    
    assert len(cities_list) == 1249
    assert city.id == int(fake_cities[0]["id"]) 
    assert city.name == str(fake_cities[0]["name"])
    assert city.geom == shape(fake_cities[0]["geometry"])


@vcr.use_cassette('tests/resources/fixtures/test_get_rivers_lakes_vcr.yaml')
def test_get_rivers_lakes_vcr(fake_rivers_lakes):
    """
    test if all rivers/lakes are retrieved from geojsonxyz and 
    GeoDataFrame returned with correct data.
    """
    client = GeojsonXYZClient()

    river_lake_gdf = client.get_rivers_lakes()

    assert len(river_lake_gdf.index) > 400
    assert river_lake_gdf.loc[0, 'featureclass'] == fake_rivers_lakes.loc[0,'featureclass']
    assert river_lake_gdf.loc[0 , 'geometry'] == fake_rivers_lakes.loc[0, 'geometry']

@vcr.use_cassette('tests/resources/fixtures/test_get_urban_areas_vcr.yaml')
def test_get_urban_areas_vcr(fake_urban_areas):
    """
    test if all urban areas are retrieved from geojsonxyz and 
    GeoDataFrame returned with correct data.
    """
    client = GeojsonXYZClient()

    urban_areas_gdf = client.get_urban_areas()

    assert len(urban_areas_gdf.index) > 2000
    assert urban_areas_gdf.loc[0, 'featureclass'] == fake_urban_areas.loc[0, 'featureclass']
    assert urban_areas_gdf.loc[0, 'geometry'] == fake_urban_areas.loc[0, 'geometry']

def test_CountryFeature(fake_countries):
    """test if all metadata from multiple features is converted correctly"""
    
    fake_feature_list = [CountryFeature(i) for i in fake_countries]
    
    fake_iso_list = [i.iso for i in fake_feature_list]
    fake_name_list = [i.name for i in fake_feature_list]
    fake_geom_list = [i.geom for i in fake_feature_list]

    assert len(fake_countries) == len(fake_feature_list)
    assert fake_iso_list == [str(i["adm0_a3"]) for i in fake_countries]
    assert fake_name_list == [str(i["name"]) for i in fake_countries]
    assert fake_geom_list == [shape(i["geometry"]) for i in fake_countries]


def test_CityFeature(fake_cities):
    """test if all metadata from multiple features is converted correctly"""
    
    fake_feature_list = [CityFeature(i) for i in fake_cities]

    fake_id_list = [i.id for i in fake_feature_list]
    fake_name_list = [i.name for i in fake_feature_list]
    fake_geom_list = [i.geom for i in fake_feature_list]

    assert len(fake_cities) == len(fake_feature_list)
    assert fake_id_list == [int(i["id"]) for i in fake_cities]
    assert fake_name_list == [str(i["name"]) for i in fake_cities]
    assert fake_geom_list == [shape(i["geometry"]) for i in fake_cities]
    

def test_LandCoverClassFeature(fake_land_cover):
    """test if all metadata from multiple features is converted correctly"""
    fake_feature_list = [LandCoverClassFeature(i) for i in fake_land_cover]

    fake_id_list = [i.id for i in fake_feature_list]
    fake_feat_list = [i.featureclass for i in fake_feature_list]
    fake_geom_list = [i.geom for i in fake_feature_list]

    assert len(fake_land_cover) == len(fake_feature_list)
    assert fake_id_list == [int(i["id"]) for i in fake_land_cover]
    assert fake_feat_list == [str(i["featureclass"]) for i in fake_land_cover]
    assert fake_geom_list == [shape(i["geometry"]) for i in fake_land_cover]

