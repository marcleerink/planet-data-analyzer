from sqlalchemy import func, select

from modules.database.db import SatImage, Satellite, City, Country


def get_images_with_filter(session, sat_names,cloud_cover, start_date, end_date):
    '''
    gets all sat images objects from postgis with applied filters.
    '''
    return session.query(SatImage).join(Satellite).filter(Satellite.name == sat_names)\
                                .filter(SatImage.cloud_cover <= cloud_cover)\
                                .filter(SatImage.time_acquired >= start_date)\
                                .filter(SatImage.time_acquired <= end_date).all()

def get_countries_with_filters(session, sat_names, cloud_cover, start_date, end_date):
    '''
    gets all country objects with total images per country from postgis with applied filters.
    '''
    subquery = session.query(Satellite.id).filter(Satellite.name == sat_names).subquery()
    return session.query(Country.iso, Country.name, Country.geom, func.count(SatImage.geom).label('total_images'))\
                                                            .join(Country.sat_images)\
                                                            .filter(SatImage.time_acquired >= start_date,
                                                                    SatImage.time_acquired <= end_date,
                                                                    SatImage.cloud_cover <= cloud_cover,
                                                                    SatImage.sat_id.in_(select(subquery)))\
                                                            .group_by(Country.iso).all()

