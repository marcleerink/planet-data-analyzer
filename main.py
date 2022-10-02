from pathlib import Path
from modules import utils, arg_parser
from database import db


def main(args):
    



if __name__ == "__main__":
    args_bundle = arg_parser.parser()
    Path(args_bundle[0].get('out_dir')).mkdir(parents=True, exist_ok=True)
    pool = utils.ReportPool(4)
    results = pool.map(main, args_bundle)
    pool.close()
    pool.join()