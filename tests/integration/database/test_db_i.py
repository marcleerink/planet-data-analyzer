
import pytest
from sqlalchemy import create_engine
import os
from datetime import datetime, timedelta
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import shape
import geopandas as gpd
from sqlalchemy_utils import database_exists, create_database
import psycopg2
import json

from config import POSTGIS_URL
from database import db
from app.query import query_distinct_satellite_names, query_countries_with_filters,\
    query_distinct_satellite_names, query_sat_images_with_filter, query_lat_lon_sat_images, query_sat_images_with_filter

from tests.resources import fake_feature

 #TODO: seperate test for centroid insert
 # test on conflict do nothing

@pytest.fixture()
def setup_test_db():
    engine = create_engine(POSTGIS_URL, echo=False)
    if not database_exists(engine.url):
        create_database(url=engine.url)
        conn = psycopg2.connect(dbname='planet_test', 
                                user=os.environ['DB_USER'], 
                                password=os.environ['DB_PW'], 
                                host=os.environ['DB_HOST'], 
                                port=os.environ['DB_PORT'])
        cursor = conn.cursor()
        cursor.execute('CREATE EXTENSION postgis')
        conn.commit()
        cursor.close()
        conn.close()

    db.Base.metadata.create_all(bind=engine)
    yield db.Base
    db.Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(setup_test_db):
    db_session = db.get_db_session()
    yield db_session
    db_session.close()
    db_session.rollback()

@pytest.fixture()
def satellite():
    return db.Satellite(id='s145', 
                    name='Planetscope', 
                    pixel_res=3.15)
@pytest.fixture()
def item_type():
    return db.ItemType(id = 'PSScene',
                    sat_id = 's145')

@pytest.fixture
def geom_shape():
    return shape(fake_feature.feature['geometry'])

@pytest.fixture
def geom_shape_nl_germany_border():
    gdf = gpd.read_file('tests/resources/polygon_border_germany.geojson')
    return gdf['geometry'][0]
    
    
@pytest.fixture
def sat_image(geom_shape):
    return db.SatImage(id = 'ss20221002', 
                        clear_confidence_percent = 95,
                        cloud_cover = 0.65,
                        time_acquired = datetime(2022, 10, 1, 23, 55, 59),
                        centroid = from_shape(geom_shape, srid=4326),
                        geom = from_shape(geom_shape, srid=4326),
                        sat_id = 's145',
                        item_type_id = 'PSScene')
@pytest.fixture
def sat_image_nl_germany_border(geom_shape_nl_germany_border):
    return db.SatImage(id = 'fake_not_in_bounds', 
                    clear_confidence_percent = 95,
                    cloud_cover = 0.65,
                    time_acquired = datetime(2022, 10, 1, 23, 55, 59),
                    centroid = from_shape(geom_shape_nl_germany_border, srid=4326),
                    geom = from_shape(geom_shape_nl_germany_border, srid=4326),
                    sat_id = 's145',
                    item_type_id = 'PSScene')
@pytest.fixture()
def asset_type():
    return db.AssetType(id='analytic')

@pytest.fixture()
def country():
    gdf = gpd.read_file('tests/resources/germany.geojson')
    return db.Country(iso = gdf['ISO2'][0],
                    name = gdf['NAME_ENGLI'][0],
                    geom = from_shape(gdf['geometry'][0], srid=4326))
@pytest.fixture()
def city():
    gdf = gpd.read_file('tests/resources/fake_cities.geojson')
    return db.City(id = 1,
                   name = gdf['name'][0],
                   geom = from_shape(gdf['geometry'][0], srid=4326))
@pytest.fixture
def city_berlin():
    gdf = gpd.read_file('tests/resources/fake_city_berlin.geojson')
    return db.City(id = 2,
                   name = gdf['name'][0],
                   geom = from_shape(gdf['geometry'][0], srid=4326))
@pytest.fixture()
def land_cover_class(geom_shape):
    return db.LandCoverClass(id = 1, 
                    featureclass='fake_area', 
                    geom=from_shape(geom_shape))

@pytest.fixture()
def setup_models(db_session,
                satellite, 
                item_type, 
                sat_image, 
                asset_type, 
                country, 
                city,
                land_cover_class):

    db_session.add(satellite)
    item_type.assets.append(asset_type)
    db_session.add(item_type)
    db_session.add(sat_image)
    db_session.add(country)
    db_session.add(city)
    db_session.add(land_cover_class)
    db_session.commit()
    return db_session

def test_Satellite(db_session, setup_models):
    
    query = db_session.query(db.Satellite).one()

    #columns
    assert query.id == 's145'
    assert query.name == 'Planetscope'
    assert query.pixel_res == 3.15
    
    #relationships
    assert [i.id for i in query.sat_images] == ['ss20221002']
    assert [i.id for i in query.items] == ['PSScene']

    
def test_ItemType(db_session, setup_models):
    query=db_session.query(db.ItemType).one()

    #columns
    assert query.id == 'PSScene'
    assert query.sat_id == 's145'

    #relationships
    assert [i.id for i in query.sat_image] == ['ss20221002']
    assert [i.id for i in query.assets] == ['analytic']
    assert query.satellites.id == 's145'


def test_AssetType(db_session, setup_models):
    #act
    query = db_session.query(db.AssetType).one()

    #assert
    assert query.id == 'analytic'
    
    #relationships
    assert [i.id for i in query.item_types] == ['PSScene']


def test_SatImage(db_session, setup_models, geom_shape):
    '''data correctly stored and (spatial) relations set up correct'''
    query = db_session.query(db.SatImage).one()

    #columns
    assert query.id == 'ss20221002'
    assert query.clear_confidence_percent == 95
    assert query.cloud_cover == 0.65
    assert query.time_acquired == datetime(2022, 10, 1, 23, 55, 59)
    assert to_shape(query.geom) == geom_shape
    
    #foreign
    assert query.sat_id == 's145'
    assert query.item_type_id == 'PSScene'
    
    # relationships
    assert query.satellites.pixel_res == 3.15
    assert [i.featureclass for i in query.land_cover_class] == ['fake_area']
    assert [i.iso for i in query.countries] == ['DE']

    #properties
    assert query.lon == 8.804454520157185
    assert query.lat == 55.474220203855445
    assert query.area_sqkm == 1244037.118

def test_CentroidFromPolygon(db_session, setup_models):

    query = db_session.query(db.SatImage).one()

    assert to_shape(query.centroid).wkt == 'POINT (8.804454520157185 55.474220203855445)'

def test_Country_success(db_session, setup_models, city_berlin):
    #add city within germany to test cities relationship
    db_session.add(city_berlin)
    db_session.commit()

    query = db_session.query(db.Country).one()

    #columns
    assert query.iso == 'DE'
    assert query.name == 'Germany'
    assert to_shape(query.geom).geom_type == 'MultiPolygon'
    
    #relationships
    assert query.sat_images.id == 'ss20221002'
    assert [i.name for i in query.cities]== ['Berlin']

def test_Country_rel_none_found(db_session, setup_models, sat_image_nl_germany_border):
    """Test that spatial relationships with City and SatImage are not returning objects when out of bounds"""
    
    #add sat_image out of geometry bounds
    db_session.add(sat_image_nl_germany_border)
    db_session.commit()

    query = db_session.query(db.Country).one()
    
    #relationships
    assert query.sat_images.id == 'ss20221002'
    assert query.sat_images.id != 'fake_not_in_bounds'
    assert [i.name for i in query.cities]== []

def test_City_success(db_session, setup_models, city_berlin):
    #add city within germany to test sat_images spatial relationship
    db_session.add(city_berlin)
    db_session.commit()

    query_with_berlin = db_session.query(db.City).filter_by(name='Berlin').one()

    #columns
    assert query_with_berlin.id == 2
    assert query_with_berlin.name == 'Berlin'
    assert to_shape(query_with_berlin.geom).geom_type == 'Point'
    
    #spatial relationship
    assert [i.id for i in query_with_berlin.sat_images] == ['ss20221002']

def test_City_relationship_none_found(db_session, setup_models):

    query = db_session.query(db.City).first()

    assert [i.id for i in query.sat_images] == []

def test_LandCoverClass(db_session, setup_models, geom_shape):
    query = db_session.query(db.LandCoverClass).one()

    #columns
    assert query.id == 1
    assert query.featureclass == 'fake_area'
    assert to_shape(query.geom) == geom_shape

    #relationships
    assert [i.id for i in query.sat_image] == ['ss20221002']

def test_prefix_insert(db_session, setup_models, sat_image):
    """
    test that double unique constraint items are not added to database ('ON CONFLICT DO NOTHING'), 
    without throwing an error.
    """
    db_session.add(sat_image)
    db_session.commit()

    query = db_session.query(db.SatImage).one()

    #assert query only returns one item
    assert query

