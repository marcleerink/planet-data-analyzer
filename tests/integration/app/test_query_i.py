import pytest
from datetime import datetime, timedelta

from modules.database import db
from modules.app import query

from tests.integration.database.test_db_i import db_session, setup_test_db, \
    setup_models, sat_image, geom_shape, satellite, item_type, asset_type, country

def test_query_distinc_satellite_names(db_session, setup_test_db):
    #arrange
    fake_satellite = [{'id':'fake_id', 'name':'fake', 'pixel_res': 9.99},
            {'id':'fake_id2', 'name':'fake2', 'pixel_res': 9.99}, 
             {'id':'fake_id', 'name':'fake', 'pixel_res': 2.99},
             {'id':'fake_id', 'name':'fake3', 'pixel_res': 1.99}]
    for i in fake_satellite:
        db_session.add(db.Satellite(id=i['id'],
                                    name=i['name'],
                                    pixel_res=i['pixel_res']))
        db_session.commit()

    #act
    sat_names = query.query_distinct_satellite_names(db_session)
    
    #assert
    assert sat_names == ['fake2', 'fake']

def test_query_lat_lon_sat_images(db_session, setup_models):
    #arrange
    sat_images = db_session.query(db.SatImage).all()

    #act
    lat_lon = query.query_lat_lon_sat_images(sat_images)

    #assert
    assert lat_lon == [[55.474220203855445, 8.804454520157185]]

sat_names_input_output = [
    ('Planetscope', 1),
    ('Skysat', 0),
    ('Esa', 0),
    ('Usgs', 0),
    ]

@pytest.mark.parametrize('sat_names, expected_output', sat_names_input_output)
def test_query_sat_images_with_filter(db_session, setup_models, sat_names, expected_output):
    #arrange
    cloud_cover = 0.7
    start_date = datetime.utcnow() - timedelta(days=7)
    end_date = datetime.utcnow()
    
    #act
    sat_images = query.query_sat_images_with_filter(db_session, sat_names, cloud_cover, start_date, end_date)
    
    #assert
    assert len(sat_images) == expected_output


def test_query_countries_with_filter(db_session, setup_models):
    cloud_cover = 0.7
    start_date = datetime.utcnow() - timedelta(days=7)
    end_date = datetime.utcnow()
    sat_names = 'Planetscope'

    countries_list = query.query_countries_with_filters(db_session, sat_names, cloud_cover, start_date, end_date)

    assert [i.iso for i in countries_list] == ['DE']
    assert [i.name for i in countries_list] == ['Germany']
    assert [i.total_images for i in countries_list] == [1]

def test_query_cities_with_filter(db_session, setup_models):
    cloud_cover = 0.7
    start_date = datetime.utcnow() - timedelta(days=7)
    end_date = datetime.utcnow()
    sat_names = 'Planetscope'

    cities_list = query.query_cities_with_filters(db_session, sat_names, cloud_cover, start_date, end_date)

    assert [i.name for i in cities_list] == ['Berlin']
