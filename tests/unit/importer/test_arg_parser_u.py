import pytest
from api_importer.arg_parser import arguments, args_validate
import argparse
from datetime import datetime, timedelta


@pytest.fixture()
def arg_input():
    return ['--aoi_file', 'data/berlin.geojson']


@pytest.fixture()
def fake_args(arg_input):
    parser = argparse.ArgumentParser(description="Search all satellite imagery in AOI and TOI")
    parser.add_argument(
        '--api_key',
        type=str,
        required=False,
        help="Optional. Planet's API key")

    yesterday = datetime.utcnow() - timedelta(days=1)
    parser.add_argument(
        "--start_date",
        type=str,
        required=False,
        default=yesterday.strftime("%Y-%m-%d"))

    parser.add_argument(
        "--end_date",
        type=str,
        required=False,
        default=datetime.utcnow().strftime("%Y-%m-%d"))

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


def test_arguments(arg_input):
    # arrange
    yesterday = datetime.utcnow() - timedelta(days=1)

    # act
    result = arguments(arg_input)

    try:
        arguments()
        assert False
    except SystemExit:
        assert True

    assert result.aoi_file == 'data/berlin.geojson'
    assert result.start_date == yesterday.strftime("%Y-%m-%d")
    assert result.end_date == datetime.utcnow().strftime("%Y-%m-%d")
    assert result.cc == 1.0


def test_args_validate_wrong_date(fake_args):
    # arrange
    fake_args.start_date = '2022-10-02'
    fake_args.end_date = '2022-10-01'

    try:
        args_validate(fake_args)
        assert False
    except ValueError:
        assert True


def test_args_validate_success(fake_args):
    """
    Check if args_validate lets through valid dates and aoi.
    Check if args_validate gets API key from environment if none provided in args
    """
    # arrange
    fake_args.start_date = '2022-10-01'
    fake_args.end_date = '2022-10-02'

    # act
    result = args_validate(fake_args)

    # assert
    assert result.start_date == '2022-10-01'
    assert result.end_date == '2022-10-02'
    assert result.api_key is not None
