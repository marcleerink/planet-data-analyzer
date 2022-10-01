import argparse
import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def arguments():
    parser = argparse.ArgumentParser(description="Creates a usage report for all SkySat Tasks and Orders.")
    parser.add_argument(
        '--api_key', 
        type=str, 
        required=False,
        help="Planet's API key")

    yesterday= datetime.utcnow() - timedelta(days=1)
    parser.add_argument(
        "--start_date",
        type=str,
        required=False,
        default = yesterday.strftime("%Y-%m-%d"),
        help="Required.Start date of the time interval to create a report for, in ISO (YYYY-MM-DD) format.(gte)")

    parser.add_argument(
        "--end_date",
        type=str,
        required=False,
        default=datetime.utcnow().strftime("%Y-%m-%d"),
        help="Optional. End date of the time interval to create a report for, in ISO (YYYY-MM-DD) format.(lte)" 
        "\nDefaults to the current date.")

    parser.add_argument(
        '--out_dir', 
        type=str, 
        required=False,
        default='reports',
        help="Destination path where reports should be exported."
            "\nDefaults to 'reports' in current directory")

    parser.add_argument(
        '--aoi_file', 
        type=str, 
        required=True,
        help="Path to geojson file containing AOIs")

    parser.add_argument(
        '--item_types', 
        type=str, 
        required=False,
        help="Item Type(s) to run the search for, comma-delimited. "
            "Defaults to all item types available", )
            
    parser.add_argument(
        "--cc", 
        type=float, 
        required=False,
        default=1.0,
        help="Cloud cover value to be used for filtering. Defaults to 1.0")
    
    return parser.parse_args()

def args_validate(args):
    if pd.to_datetime(args.end_date) <= pd.to_datetime(args.start_date):
        raise ValueError('The end date can not be before the start date')

    if not args.api_key:
        try:
            args.api_key = os.environ["PL_API_KEY"]
        except Exception as e:
            raise ValueError("No API was provided, please provide a valid API key or use an environment variable")
    
    if args.item_types:
        if "," in args.item_types:
            args.item_types = args.item_types.split(",")
        else:
            args.item_types = [args.item_types]

    return args


def args_bundler(args):
    args_bundle = []
    bundle = vars(args).copy()
    args_bundle.append(bundle)
    return args_bundle
       

def parser():
    args = arguments()
    args = args_validate(args)
    args_bundle = args_bundler(args)

    return args_bundle