import pytest
import pandas as pd

from modules.importer.utils import geojson_import
from tests.importer.test_api_importer import geometry
from tests.importer.fixtures import fake_response


def test_geojson_import(geometry):
    #act
    geometry = geojson_import(aoi_file='tests/resources/berlin.geojson')
    #assert
    assert geometry == geometry
