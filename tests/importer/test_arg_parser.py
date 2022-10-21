import pytest
import sys
from modules.importer.arg_parser import arguments, args_validate, args_bundler
import argparse
from datetime import datetime, timedelta


@pytest.fixture()
def arg_input():
    return ['--aoi_file', 'data/berlin.geojson']

def test_arguments(arg_input):
    #act
    result = arguments(arg_input)
    try:
        arguments()
        assert False
    except SystemExit:
        assert True
     
    #assert
    assert result.aoi_file == 'data/berlin.geojson'
    assert isinstance(result.start_date , str)
    assert isinstance(result.end_date, str)
    assert isinstance(result.cc, float)
    

# def test_args_validate(arg_input):
#     #arrange
#     wrong_date_input = [['--aoi_file', 'data/berlin.geojson'], ['--start_date', '2022-10-01'],['--end_date', '2022-10-02']]
#     result =  args_validate(arguments(arg_input))
#     assert result

#     try:
#         args_validate(arguments(wrong_date_input))
#         assert False
#     except ValueError:
#         assert True

    