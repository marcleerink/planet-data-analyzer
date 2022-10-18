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


@pytest.fixture(scope='session')
def session(setup_test_db):
    session = get_db_session()
    yield session
    session.close()
    session.rollback()

@pytest.mark.run(order=1)
def test_satellite_create(session):
    satellite = Satellite(id='s145', 
                        name='Planetscope', 
                        pixel_res=3.15)
    session.add(satellite)
    session.commit()
    assert session.query(Satellite).one()
    return satellite

@pytest.mark.run(order=2)
def test_item_type_create(session):
    item_type = ItemType(id = 'PSScene',
                        sat_id = 's145')
    session.add(item_type)
    session.commit()
    assert session.query(ItemType).one()
    return item_type

@pytest.mark.run(order=3)
def test_sat_image_create(session):
    sat_image = SatImage(id = 'ss20221002', 
                        clear_confidence_percent = 95,
                        cloud_cover = 0.65,
                        pixel_res = 3.15,
                        time_acquired = datetime.utcnow(),
                        centroid = 'POLYGON ((19 -25, 0 0, -27 0, 19 -25))',
                        geom = 'POLYGON ((19 -25, 0 0, -27 0, 19 -25))',
                        sat_id = 's145',
                        item_type_id = 'PSScene')
    session.add(sat_image)
    session.commit()
    assert session.query(SatImage).one()
    return sat_image

    
@pytest.mark.run(order=4)
def test_asset_type_create(session):
    asset_type = AssetType(id='analytic')
    session.add(asset_type)
    session.commit()
    assert session.query(AssetType).one()
    return asset_type
    

def test_country_create(session):
    gdf = gpd.read_file('data/germany.geojson')
    country = Country(iso = gdf['ISO2'][0],
                    name = gdf['NAME_ENGLI'][0],
                    geom = from_shape(gdf['geometry'][0], srid=4326))
                    
    session.add(country)
    session.commit()
    assert session.query(Country).one()
    return country

def delete_instance(session, instance_id, model, model_primary):
    session.query(model).filter(model_primary == instance_id).delete()
    result = session.query(model).one_or_none()
    assert result is None


def test_query_distinc_satellite_names(session):
    assert query_distinct_satellite_names(session) == ['Planetscope']


def test_query_lat_lon_sat_images(session):
    sat_images = [test_sat_image_create(session)]
    lat_lon = query_lat_lon_sat_images(sat_images)
    assert lat_lon == [[-8.333333333333334, -2.6666666666666665]]

sat_names_input_output = [
    ('Planetscope', 1),
    ('Skysat', 0),
    ('Esa', 0),
    ('Usgs', 0),
]

@pytest.mark.parametrize('sat_names, expected_output', sat_names_input_output)
def test_query_sat_images_with_filter(session, sat_names, expected_output):
    cloud_cover = 0.7
    start_date = datetime.utcnow() - timedelta(days=7)
    end_date = datetime.utcnow()
    sat_images = query_sat_images_with_filter(session, sat_names, cloud_cover, start_date, end_date)
    
    assert len(sat_images) == expected_output



    

