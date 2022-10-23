import pytest
import geopandas as gpd
import json
from modules.importer.postgis_importer import get_data_countries

@pytest.fixture()
def fake_countries():
    gdf = gpd.read_file('tests/resources/fake_countries.geojson')
    gdf.columns = gdf.columns.str.lower()
    gdf = gdf.rename_geometry('geom')
    gdf = gdf.rename(columns={'iso_a2' : 'iso'})
    return gdf[['iso', 'name', 'geom']]
    


"""UNIT"""
def test_get_data_countries(fake_countries):
    result = fake_countries
    correct_columns = ['iso', 'name', 'geom']
    assert isinstance(result, gpd.GeoDataFrame)
    assert all(i in result.columns for i in correct_columns)
    assert not result['geom'].isnull().values.any()

# """INTEGRATION"""
# def test_get_data_countries_integration():
#     result = get_data_countries()
#     correct_columns = ['iso', 'name', 'geom']
#     assert isinstance(result, gpd.GeoDataFrame)
#     assert all(i in result.columns for i in correct_columns)
#     assert not result['geom'].isnull().values.any()

