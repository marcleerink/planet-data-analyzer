from sqlalchemy import func, select
import streamlit as st
from modules.database.db import SESSION, SatImage, Satellite, City, Country
from sqlalchemy.orm.query import Query
from sqlalchemy.sql.compiler import StrSQLCompiler
from modules.config import LOGGER

@st.experimental_memo
def get_images_with_filter(_session, sat_names,cloud_cover, start_date, end_date):
    '''
    gets all sat images objects from postgis with applied filters.
    '''
    LOGGER.info('Getting Images from DB')
    
    return _session.query(SatImage).join(Satellite).filter(Satellite.name == sat_names)\
                                .filter(SatImage.cloud_cover <= cloud_cover)\
                                .filter(SatImage.time_acquired >= start_date)\
                                .filter(SatImage.time_acquired <= end_date).all()

@st.experimental_memo
def get_countries_with_filters(_session, sat_names, cloud_cover, start_date, end_date):
    '''
    gets all country objects with total images per country from postgis with applied filters.
    '''
    LOGGER.info('Getting Country from DB')
    
    subquery = _session.query(Satellite.id).filter(Satellite.name == sat_names).subquery()
    return _session.query(Country.iso, Country.name, Country.geom, func.count(SatImage.geom).label('total_images'))\
                                                            .join(Country.sat_images)\
                                                            .filter(SatImage.time_acquired >= start_date,
                                                                    SatImage.time_acquired <= end_date,
                                                                    SatImage.cloud_cover <= cloud_cover,
                                                                    SatImage.sat_id.in_(select(subquery)))\
                                                            .group_by(Country.iso).all()

