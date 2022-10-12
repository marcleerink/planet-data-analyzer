import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from datetime import datetime
from geojson.utils import generate_random
from shapely.geometry import shape
from geoalchemy2.shape import from_shape
import geopandas as gpd
from modules.database.db import SatImage, Satellite, ItemType, AssetType, Country


engine = create_engine(os.environ['POSTGIS_URL'], echo=True)
Session = sessionmaker()

@pytest.fixture(scope='module')
def connection():
    connection = engine.connect()
    yield connection
    connection.close()

@pytest.fixture(scope='function')
def session(connection):
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    
def delete_instance(session, model_id, model, model_primary):
    session.query(model).filter(model_primary == model_id).delete()
    result = session.query(model).one_or_none()
    assert result is None

def satellite_create(session):
    satellite = Satellite(id='s145', 
                        name='planetscope', 
                        pixel_res=3.15)
    session.add(satellite)
    session.commit()
    assert session.query(Satellite).one()
    return satellite

def item_type_create(session):
    item_type = ItemType(id = 'PSScene',
                        sat_id = 's145')
    session.add(item_type)
    session.commit()
    assert session.query(ItemType).one()
    return item_type

def sat_image_create(session):
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

def asset_type_create(session):
    asset_type = AssetType(id='analytic')
    session.add(asset_type)
    session.commit()
    assert session.query(AssetType).one()
    return asset_type

def test_planet_models(session):
    satellite = satellite_create(session)
    item_type = item_type_create(session)
    sat_image = sat_image_create(session)
    asset_type = asset_type_create(session)
    
    delete_instance(session, asset_type.id, AssetType, AssetType.id)
    delete_instance(session, sat_image.id, SatImage, SatImage.id)
    delete_instance(session, item_type.id, ItemType, ItemType.id)
    delete_instance(session, satellite.id, Satellite, Satellite.id)
    

def country_create(session):
    gdf = gpd.read_file('data/germany.geojson')
    country = Country(iso = gdf['ISO2'][0],
                    name = gdf['NAME_ENGLI'][0],
                    geom = from_shape(gdf['geometry'][0], srid=4326))
                    
    session.add(country)
    session.commit()
    assert session.query(Country).one()
    return country

def test_land_cover_models(session):
    country = country_create(session)

    delete_instance(session, country.iso, Country, Country.iso)


    

    

