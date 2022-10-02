from pathlib import Path
from modules import utils, arg_parser
from database.db import SESSION, SatImage, City, Country
from sqlalchemy import func
from geoalchemy2.shape import from_shape, to_shape

def main():
    session = SESSION()    
    amsterdam = session.query(City).filter_by(name = 'amsterdam')
    

    query = session.query(City.name, func.ST_Area(func.ST_Buffer(City.geom, 2)).label('bufferarea'))

    nl = session.query(Country).filter_by(iso = 'FR ')
    nl_geom = nl[0].geom
    
    sat_image_berlin = session.query(SatImage.id).filter(SatImage.geom.ST_Intersects(nl_geom)).all()
    print(sat_image_berlin)
   
   



if __name__ == "__main__":
    # args_bundle = arg_parser.parser()
    # Path(args_bundle[0].get('out_dir')).mkdir(parents=True, exist_ok=True)
    # pool = utils.ReportPool(4)
    # results = pool.map(main)
    # pool.close()
    # pool.join()
    main()