import pytest
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from shapely import geometry
import geopandas as gpd
from shapely.geometry import shape
from geoalchemy2.shape import from_shape

from app import query
from tests.resources import fake_feature

@dataclass
class FakeSatellite:
    id: str
    name: str
    pixel_res : str

@dataclass
class FakeAssetType:
    id: list

@dataclass
class FakeItemType:
    id: str
    sat_id: FakeSatellite
    assets: FakeAssetType
    
@dataclass
class FakeSatImage:
    id: str
    cloud_cover: float
    time_acquired: datetime
    geom: geometry
    area_sqkm: float
    satellites: FakeSatellite
    sat_id: FakeSatellite
    item_type_id: FakeItemType
    item_types: FakeItemType   

@dataclass
class FakeCountry:
    iso: str
    name: str
    total_images: int
    geom: geometry

@pytest.fixture()
def geom_shape():
    return shape(fake_feature.feature['geometry'])


@pytest.fixture
def fake_satellite():
    return FakeSatellite(id='fake_sat', name='planetscope', pixel_res=3.0)

@pytest.fixture
def fake_item_type(fake_satellite, fake_asset_type, fake_asset_type2):
    return FakeItemType(id='fake_item', sat_id=fake_satellite, assets=[fake_asset_type, fake_asset_type2])

@pytest.fixture
def fake_asset_type():
    return FakeAssetType(id='asset1')

@pytest.fixture
def fake_asset_type2():
    return FakeAssetType(id='asset2')

@pytest.fixture
def fake_image(fake_satellite, fake_item_type, geom_shape):
    return FakeSatImage(
                    id='fake_id', 
                    cloud_cover=0.1, 
                    time_acquired = datetime.utcnow(), 
                    sat_id='fake_sat_id',
                    satellites= fake_satellite,
                    item_type_id = 'fake_item_type_id',
                    item_types = fake_item_type,
                    geom=from_shape(geom_shape),
                    area_sqkm = 25.0)

@pytest.fixture
def fake_country(geom_shape):
    return FakeCountry(iso='NL', name='Netherlands', total_images=50, geom=from_shape(geom_shape))

def test_create_images_df(fake_image):
    images_df = query.create_images_df([fake_image])
    
    assert isinstance(images_df, pd.DataFrame)
    assert images_df['id'][0] == fake_image.id
    assert images_df['cloud_cover'][0] == fake_image.cloud_cover
    assert images_df['pixel_res'][0] == fake_image.satellites.pixel_res
    assert images_df['time_acquired'][0] == fake_image.time_acquired.strftime("%Y-%m-%d %H:%M:%S")
    assert images_df['sat_name'][0] == fake_image.satellites.name



def test_create_images_geojson(fake_image):
    
    images_geojson = query.create_images_geojson([fake_image])
    
    assert images_geojson['features'][0]['properties']['id'] == fake_image.id
    assert images_geojson['features'][0]['properties']['cloud_cover'] == fake_image.cloud_cover
    assert images_geojson['features'][0]['properties']['pixel_res'] == fake_image.satellites.pixel_res
    assert images_geojson['features'][0]['properties']['time_acquired'] == fake_image.time_acquired.strftime("%Y-%m-%d %H:%M:%S")
    assert images_geojson['features'][0]['properties']['sat_name'] == fake_image.satellites.name
    assert images_geojson['features'][0]['properties']['asset_types'] ==[i.id for i in fake_image.item_types.assets]

def test_create_countries_geojson(fake_country):

    country_geojson = query.create_country_geojson([fake_country])
    
    assert country_geojson['features'][0]['properties']['iso'] == fake_country.iso
    assert country_geojson['features'][0]['properties']['name'] == fake_country.name
    assert country_geojson['features'][0]['properties']['total_images'] == fake_country.total_images
    

def test_create_countries_df(fake_country):

    country_df = query.create_countries_df([fake_country])
    
    assert isinstance(country_df, pd.DataFrame)
    assert country_df['iso'][0] == fake_country.iso
    assert country_df['name'][0] == fake_country.name
    assert country_df['total_images'][0] == fake_country.total_images
    
