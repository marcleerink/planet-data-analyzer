from unittest.mock import MagicMock
import pytest
import geopandas as gpd
import json
from factory.alchemy import SQLAlchemyModelFactory
import factory
from modules.importer.postgis_importer import get_data_countries, import_countries_table
from modules.database.db import Country, get_db_session
from shapely.geometry import shape
from geojson.utils import generate_random

class CountryFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Country
        sqlalchemy_session = get_db_session()
    
    iso = factory.Faker
    name = factory.Faker('name')
    geom = shape(generate_random('Polygon')).wkt

    


@pytest.fixture()
def fake_countries_data():
    gdf = gpd.read_file('tests/resources/fake_countries.geojson')
    gdf.columns = gdf.columns.str.lower()
    gdf = gdf.rename_geometry('geom')
    gdf = gdf.rename(columns={'iso_a2' : 'iso'})
    return gdf[['iso', 'name', 'geom']]
    

"""UNIT"""
def test_get_data_countries(fake_countries_data):
    result = fake_countries_data
    correct_columns = ['iso', 'name', 'geom']
    assert isinstance(result, gpd.GeoDataFrame)
    assert all(i in result.columns for i in correct_columns)
    assert not result['geom'].isnull().values.any()

@pytest.mark.parametrize("val,expected", [(1, 3), (5, 5)])
def test_import_countries_table(fake_countries_data, val, expected):
    session = MagicMock()
    session.configure_mock(
        **{
            'modules.importer.postgis_importer.import_countries_table.return_value': val
    })
    result = import_countries_table(session=session, gdf_countries=fake_countries_data)

    assert result.session is session
# """INTEGRATION"""
# def test_get_data_countries_integration():
#     result = get_data_countries()
#     correct_columns = ['iso', 'name', 'geom']
#     assert isinstance(result, gpd.GeoDataFrame)
#     assert all(i in result.columns for i in correct_columns)
#     assert not result['geom'].isnull().values.any()

