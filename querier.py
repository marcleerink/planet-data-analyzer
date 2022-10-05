from os import stat_result
from modules.database.db import SESSION, SatImage, City, Country, Satellite
from sqlalchemy import func


def get_sat_image_country(session, iso_code):
    '''gets a list of sat_images objects in a country'''
    query = session.query(Country).filter_by(iso=iso_code).join(Country.sat_images)
    return [image for row in query for image in row.sat_images]

def get_sat_image_satellite(session, satellite_name):
    query = session.query(SatImage, Satellite).filter(Satellite.name == satellite_name)
    print(query)
    return [image for image in query]
