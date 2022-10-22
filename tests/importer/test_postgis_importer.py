import pytest
import geopandas as gpd
from modules.importer.postgis_importer import get_data_countries




"""INTEGRATION"""
def test_get_data_countries_integration():
    result = get_data_countries()
    correct_columns = ['iso', 'name', 'geom']
    assert isinstance(result, gpd.GeoDataFrame)
    assert all(i in result.columns for i in correct_columns)
    assert not result['geom'].isnull().values.any()

