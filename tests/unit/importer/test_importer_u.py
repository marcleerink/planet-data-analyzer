import pytest
import json

from importer import geojson_import


@pytest.fixture
def geometry():
    with open('tests/resources/berlin.geojson') as f:
        geometry = json.load(f)
    return geometry['features'][0]['geometry']


def test_geojson_import(geometry):
    # act
    geometry = geojson_import(aoi_file='tests/resources/berlin.geojson')
    # assert
    assert geometry == geometry
