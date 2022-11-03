import pytest
from datetime import datetime, timedelta

from modules.database import db
from modules.app.query import query_distinct_satellite_names,\
    query_lat_lon_sat_images, query_sat_images_with_filter
from tests.integration.database.test_db_i import db_session, setup_test_db, setup_models, geom_shape

def test_query_distinc_satellite_names(db_session):
    #act
    query = query_distinct_satellite_names(db_session)
    
    #assert
    assert query == ['Planetscope']

def test_query_lat_lon_sat_images(db_session):
    #arrange
    sat_images = db_session.query(db.SatImage).all()

    #act
    lat_lon = query_lat_lon_sat_images(sat_images)

    #assert
    assert lat_lon == [[55.474220203855445, 8.804454520157185]]

sat_names_input_output = [
    ('Planetscope', 1),
    ('Skysat', 0),
    ('Esa', 0),
    ('Usgs', 0),
]

@pytest.mark.parametrize('sat_names, expected_output', sat_names_input_output)
def test_query_sat_images_with_filter(db_session, sat_names, expected_output):
    #arrange
    cloud_cover = 0.7
    start_date = datetime.utcnow() - timedelta(days=7)
    end_date = datetime.utcnow()
    
    #act
    sat_images = query_sat_images_with_filter(db_session, sat_names, cloud_cover, start_date, end_date)
    
    #assert
    assert len(sat_images) == expected_output