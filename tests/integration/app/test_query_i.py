import pytest
from datetime import datetime
from shapely.geometry import Polygon
from geoalchemy2.shape import from_shape
from database import db
from app import query

from tests.integration.database.test_db_i import db_session, setup_test_db, \
    setup_models, sat_image, geom_shape, satellite, item_type, asset_type, country, land_cover_class, city, city_berlin


def test_query_distinc_satellite_names(db_session, setup_test_db):
    # arrange
    fake_satellite = [{'id': 'fake_id', 'name': 'fake', 'pixel_res': 9.99},
                      {'id': 'fake_id2', 'name': 'fake2', 'pixel_res': 9.99},
                      {'id': 'fake_id', 'name': 'fake', 'pixel_res': 2.99},
                      {'id': 'fake_id', 'name': 'fake3', 'pixel_res': 1.99}]
    for i in fake_satellite:
        db_session.add(db.Satellite(id=i['id'],
                                    name=i['name'],
                                    pixel_res=i['pixel_res']))
        db_session.commit()

    # act
    sat_names = query.query_distinct_satellite_names(db_session)

    # assert
    assert sat_names == ['fake', 'fake2']


sat_names_input_output = [
    (['Planetscope'], 1),
    (['Skysat'], 0),
    (['Esa'], 0),
    (['Usgs'], 0),
]


@pytest.mark.parametrize('sat_names, expected_output', sat_names_input_output)
def test_query_sat_images_with_filter(db_session, setup_models, sat_names, expected_output):
    # setup filters
    cloud_cover = 0.7
    start_date = datetime(2022, 9, 1, 23, 55, 59)
    end_date = datetime.utcnow()
    country_name = 'Germany'

    # act
    sat_images = query.query_sat_images_with_filter(
        db_session, sat_names, cloud_cover, start_date, end_date, country_name)

    # assert
    assert len(sat_images) == expected_output


def test_query_cities_with_filter(db_session, setup_models, city_berlin):
    # add Berlin to cities table in db
    db_session.add(city_berlin)
    db_session.commit()

    # setup filters
    cloud_cover = 1.0
    start_date = datetime(2022, 9, 1, 23, 55, 59)
    end_date = datetime.utcnow()
    sat_names = ['Planetscope']
    country_name = 'Germany'

    gdf_cities = query.query_cities_with_filters(
        db_session, sat_names, cloud_cover, start_date, end_date, country_name)

    # assert only city in bounds is returned
    assert len(gdf_cities.index) == 1
    assert gdf_cities['name'][0] == 'Berlin'


def test_query_sat_images_with_filter(db_session, setup_models):

    # setup filters
    cloud_cover = 1.0
    start_date = datetime(2022, 9, 1, 23, 55, 59)
    end_date = datetime.utcnow()
    sat_names = ['Planetscope']
    country_name = 'Germany'

    gdf_images = query.query_sat_images_with_filter(
        db_session, sat_names, cloud_cover, start_date, end_date, country_name)

    assert len(gdf_images) == 1
    assert gdf_images['id'][0] == 'ss20221002'
    assert gdf_images['sat_id'][0] == 's145'
    assert gdf_images['clear_confidence_percent'][0] == 95
    assert gdf_images['cloud_cover'][0] == 0.65
    assert gdf_images['time_acquired'][0] == datetime(2022, 10, 1, 23, 55, 59)
    assert gdf_images['pixel_res'][0] == 3.15
    assert gdf_images['item_type_id'][0] == 'PSScene'
    assert gdf_images['lon'][0] == 8.804454520157185
    assert gdf_images['lat'][0] == 55.474220203855445
    assert gdf_images['area_sqkm'][0] == 1244037.118
    assert gdf_images['land_cover_class'][0] == ['fake_area']
    assert gdf_images['geom'].any()

def test_query_images_with_filters_queries_unique_image_ids(db_session, setup_models):
    
    # setup filters
    cloud_cover = 1.0
    start_date = datetime(2022, 9, 1, 23, 55, 59)
    end_date = datetime.utcnow()
    sat_names = ['Planetscope']
    country_name = 'Germany'

    gdf_images = query.query_sat_images_with_filter(
        db_session, sat_names, cloud_cover, start_date, end_date, country_name)

    assert gdf_images['id'].is_unique

def test_query_land_cover_classes_with_filters(db_session, setup_models):

    # setup filters
    cloud_cover = 1.0
    start_date = datetime(2022, 9, 1, 23, 55, 59)
    end_date = datetime.utcnow()
    sat_names = ['Planetscope']
    country_name = 'Germany'

    gdf_land_cover = query.query_land_cover_classes_with_filters(
        db_session, sat_names, cloud_cover, start_date, end_date, country_name)

    assert gdf_land_cover['id'].any()
    assert gdf_land_cover['total_images'][0] == 1
    assert gdf_land_cover['featureclass'][0] == 'fake_area'
    assert gdf_land_cover['geom'].any()