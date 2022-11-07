
import pytest
from sqlalchemy import create_engine
import os
from datetime import datetime, timedelta
from geoalchemy2.shape import from_shape
from shapely.geometry import shape
import geopandas as gpd
from sqlalchemy_utils import database_exists, create_database
import psycopg2

from modules.config import POSTGIS_URL, LOGGER
from modules.database.db import Satellite, SatImage, AssetType, ItemType, Country, City, get_db_session, Base
from modules.app.query import query_distinct_satellite_names, query_countries_with_filters,\
    query_distinct_satellite_names, query_sat_images_with_filter, query_lat_lon_sat_images, query_sat_images_with_filter

from tests.resources import fake_feature

@pytest.fixture(scope='session')
def setup_test_db():
    engine = create_engine(POSTGIS_URL, echo=False)
    if not database_exists(engine.url):
        create_database(url=engine.url)
        conn = psycopg2.connect(dbname=os.environ['DB_NAME'], 
                                user=os.environ['DB_USER'], 
                                password=os.environ['DB_PW'], 
                                host=os.environ['DB_HOST'], 
                                port=os.environ['DB_PORT'])
        cursor = conn.cursor()
        cursor.execute('CREATE EXTENSION postgis')
        conn.commit()
        cursor.close()
        conn.close()

    Base.metadata.create_all(bind=engine)
    yield Base
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(setup_test_db):
    db_session = get_db_session()
    yield db_session
    db_session.close()
    db_session.rollback()

@pytest.fixture()
def satellite():
    return Satellite(id='s145', 
                    name='Planetscope', 
                    pixel_res=3.15)
@pytest.fixture()
def item_type():
    return ItemType(id = 'PSScene',
                    sat_id = 's145')

@pytest.fixture()
def geom_shape():
    return shape(fake_feature.feature['geometry'])

@pytest.fixture()
def sat_image(geom_shape):
    return SatImage(id = 'ss20221002', 
                        clear_confidence_percent = 95,
                        cloud_cover = 0.65,
                        time_acquired = datetime.utcnow(),
                        centroid = from_shape(geom_shape, srid=4326),
                        geom = from_shape(geom_shape, srid=4326),
                        sat_id = 's145',
                        item_type_id = 'PSScene')

@pytest.fixture()
def asset_type():
    return AssetType(id='analytic')

@pytest.fixture()
def country():
    gdf = gpd.read_file('tests/resources/germany.geojson')
    return Country(iso = gdf['ISO2'][0],
                    name = gdf['NAME_ENGLI'][0],
                    geom = from_shape(gdf['geometry'][0], srid=4326))

@pytest.fixture()
def setup_models(db_session,satellite, item_type, sat_image, asset_type, country):
    db_session.add(satellite)
    db_session.add(item_type)
    db_session.add(sat_image)
    db_session.add(asset_type)
    db_session.add(country)
    db_session.commit()
    return db_session

def test_satellite_create(db_session, setup_models):
    #act
    query = db_session.query(Satellite).one()

    #assert
    assert query
    
def test_item_type_create(db_session, setup_models):
    #act
    query=db_session.query(ItemType).one()

    #assert
    assert query

def test_sat_image_create(db_session, setup_models):
    #act
    query = db_session.query(SatImage).one()

    #assert
    assert query

def test_asset_type_create(db_session, setup_models):
    #act
    query = db_session.query(AssetType).one()

    #assert
    assert query
    
def test_country_create(db_session, setup_models):
    #act
    query = db_session.query(Country).one()

    #assert
    assert query
