import pytest
import argparse
import os
import json
from importer import importer, data_api_importer
from database import db
from tests.integration.database.test_db_i import db_session, setup_test_db



@pytest.fixture()
def arg_input():
    return ['--aoi_file', 'tests/resources/small_aoi.geojson']

@pytest.fixture()
def fake_args(arg_input):
    parser = argparse.ArgumentParser(description="Search all satellite imagery in AOI and TOI")
    parser.add_argument(
        '--api_key', 
        type=str, 
        required=False,
        help="Optional. Planet's API key")

    parser.add_argument(
        "--start_date",
        type=str,
        required=False)

    parser.add_argument(
        "--end_date",
        type=str,
        required=False)

    parser.add_argument(
        '--aoi_file', 
        type=str, 
        required=True)

    parser.add_argument(
        "--cc", 
        type=float, 
        required=False,
        default=1.0)

    return parser.parse_args(arg_input)

@pytest.fixture()
def fake_response_small_aoi():
    with open('tests/resources/fake_response_small_aoi.json') as f:
        return json.load(f)

def test_data_importer_i(fake_args, fake_response_small_aoi, db_session, setup_test_db):
    """
    Verifying that correct features are retrieved from data api and correctly stored in db.
    """

    #setup argparser
    fake_args.api_key = os.environ['PL_API_KEY']
    fake_args.start_date = '2022-10-01'
    fake_args.end_date = '2022-10-02'
    fake_args.cc = 0.1

    #setup fake response
    fake_response_sat_id = set(i['properties']['satellite_id'] for i in fake_response_small_aoi)
    fake_response_item_id = set(i['properties']['item_type'] for i in fake_response_small_aoi)
    fake_response_id = set(i['id'] for i in fake_response_small_aoi)
    fake_response_assets = [i['assets'] for i in fake_response_small_aoi]
    fake_response_asset_types = set([i for sublist in fake_response_assets for i in sublist])
    
    
    # call api
    data_api_importer(fake_args)

    # query db
    satellite_in_db = db_session.query(db.Satellite)
    item_types_in_db = db_session.query(db.ItemType)
    sat_images_in_db = db_session.query(db.SatImage)
    asset_types_in_db = db_session.query(db.AssetType)
    

    #assert that all unique sat_images are imported into db
    assert sorted(fake_response_sat_id) == sorted([i.id for i in satellite_in_db])
    assert sorted(fake_response_item_id) == sorted([i.id for i in item_types_in_db])
    assert sorted(fake_response_id) == sorted([i.id for i in sat_images_in_db])
    assert sorted(fake_response_asset_types) == sorted([i.id for i in asset_types_in_db])
    
