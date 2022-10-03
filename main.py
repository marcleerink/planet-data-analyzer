from os import stat_result
from modules.database.db import SESSION, SatImage, City, Country
from sqlalchemy import func
from geoalchemy2.shape import from_shape, to_shape
from 

def get_sat_image_country(session, iso_code):
    '''gets a list of sat_images objects in a country'''
    query = session.query(Country).filter_by(iso=iso_code).join(Country.sat_images)
    return [image for row in query for image in row.sat_images]


def main():
    session = SESSION()



    

    # print(sat_images_germany.id)
    # sat_image_berlin = session.query(Country.sat_images).filter_by(name='Germany').all()
    
    
    # amsterdam = session.query(City).filter_by(name = 'amsterdam')

    # nl = session.query(Country).filter_by(iso = 'ES')
    # nl_geom = nl[0].geom
    # polygon_spain = to_shape(nl_geom)
    # print(polygon_spain)
    
    # sat_image_berlin = session.query(SatImage).filter(SatImage.geom.ST_Intersects(nl_geom)).all()
    # print(sat_image_berlin)
   
   



if __name__ == "__main__":
    # args_bundle = arg_parser.parser()
    # Path(args_bundle[0].get('out_dir')).mkdir(parents=True, exist_ok=True)
    # pool = utils.ReportPool(4)
    # results = pool.map(main)
    # pool.close()
    # pool.join()
    main()