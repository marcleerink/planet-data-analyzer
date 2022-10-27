from urllib.parse import quote_from_bytes
import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from datetime import datetime, timedelta
from geoalchemy2.shape import from_shape
import geopandas as gpd
from sqlalchemy_utils import database_exists, create_database
import psycopg2


from modules.config import POSTGIS_URL, LOGGER
from modules.database.db import Satellite, SatImage, AssetType, ItemType, Country, City, get_db_session, Base
from modules.app.query import query_distinct_satellite_names, query_countries_with_filters,\
    query_distinct_satellite_names, query_sat_images_with_filter, query_lat_lon_sat_images, query_sat_images_with_filter

@pytest.fixture()
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
def session(setup_test_db):
    session = get_db_session()
    yield session
    session.close()
    session.rollback()

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
def sat_image():
    return SatImage(id = 'ss20221002', 
                        clear_confidence_percent = 95,
                        cloud_cover = 0.65,
                        time_acquired = datetime.utcnow(),
                        centroid = 'POLYGON ((19 -25, 0 0, -27 0, 19 -25))',
                        geom = 'POLYGON ((19 -25, 0 0, -27 0, 19 -25))',
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
def setup_models(session,satellite, item_type, sat_image, asset_type, country):
    session.add(satellite)
    session.add(item_type)
    session.add(sat_image)
    session.add(asset_type)
    session.add(country)
    session.commit()
    return session

def test_satellite_create(session, setup_models):
    #act
    query = session.query(Satellite).one()

    #assert
    assert query
    
def test_item_type_create(session, setup_models):
    #act
    query=session.query(ItemType).one()

    #assert
    assert query

def test_sat_image_create(session, setup_models):
    #act
    query = session.query(SatImage).one()

    #assert
    assert query

def test_asset_type_create(session, setup_models):
    #act
    query = session.query(AssetType).one()

    #assert
    assert query
    
def test_country_create(session, setup_models):
    #act
    query = session.query(Country).one()

    #assert
    assert query

def test_query_distinc_satellite_names(session, setup_models):
    #act
    query = query_distinct_satellite_names(session)
    
    #assert
    assert query == ['Planetscope']

def test_query_lat_lon_sat_images(session, setup_models):
    #arrange
    sat_images = session.query(SatImage).all()

    #act
    lat_lon = query_lat_lon_sat_images(sat_images)

    #assert
    assert lat_lon == [[-8.333333333333334, -2.6666666666666665]]

sat_names_input_output = [
    ('Planetscope', 1),
    ('Skysat', 0),
    ('Esa', 0),
    ('Usgs', 0),
]

@pytest.mark.parametrize('sat_names, expected_output', sat_names_input_output)
def test_query_sat_images_with_filter(session, sat_names, setup_models, expected_output):
    #arrange
    cloud_cover = 0.7
    start_date = datetime.utcnow() - timedelta(days=7)
    end_date = datetime.utcnow()
    
    #act
    sat_images = query_sat_images_with_filter(session, sat_names, cloud_cover, start_date, end_date)
    
    #assert
    assert len(sat_images) == expected_output