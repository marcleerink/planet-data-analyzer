from sqlalchemy import func, select
import streamlit as st
from modules.database.db import SatImage, Satellite, City, Country
from sqlalchemy.orm.query import Query
from sqlalchemy.sql.compiler import StrSQLCompiler
from modules.config import LOGGER
import geopandas as gpd
import pandas as pd
from geoalchemy2.shape import to_shape
from geojson import Feature, FeatureCollection, dumps

def create_images_df(images):
    return pd.DataFrame({
        'id': [image.id for image in images],
        'cloud_cover' : [image.cloud_cover for image in images],
        'pixel_res' : [image.pixel_res for image in images],
        'time_acquired': [image.time_acquired.strftime("%Y-%m-%d") for image in images],
        'sat_name' : [image.satellites.name for image in images]})


def create_images_geojson(session, images):
    json_lst=[]
    
    for i in images:
        geometry = to_shape(i.geom)
        feature = Feature(
                id=i.id,
                geometry=geometry,
                properties={
                    "id" : i.id,
                    "cloud_cover" : i.cloud_cover,
                    "pixel_res" : i.pixel_res,
                    "time_acquired" : i.time_acquired.strftime("%Y-%m-%d"),
                    "sat_id" : i.sat_id,
                    "sat_name" : i.satellites.name,
                    "item_type_id" : i.item_type_id,
                    "srid" :i.srid,
                    "area_sqkm": i.area_sqkm,
                })
        json_lst.append(feature)
    return dumps(FeatureCollection(json_lst))

def create_country_geojson(countries):
    json_lst=[]
    for i in countries:
        geometry = to_shape(i.geom)
        feature = Feature(
                id=i.iso,
                geometry=geometry,
                properties={
                    "iso" : i.iso,
                    "name" : i.name,
                    "total_images" : i.total_images
                })
        json_lst.append(feature)
    return dumps(FeatureCollection(json_lst))

def create_countries_df(countries):
    return pd.DataFrame({
        'iso': [c.iso for c in countries],
        'name' : [c.name for c in countries],
        'total_images' : [c.total_images for c in countries],})


def get_distinct_satellite_names(_session):
    return _session.query(Satellite.name).distinct()

@st.experimental_memo
def get_images_with_filter(_session, sat_names,cloud_cover, start_date, end_date):
    '''
    gets all sat images objects from postgis with applied filters. 
    Creates geojson and df. Does that in this function to make single caching possible
    '''
    LOGGER.info('Getting images from DB')
    
    images =_session.query(SatImage).join(Satellite).filter(Satellite.name == sat_names)\
                                .filter(SatImage.cloud_cover <= cloud_cover)\
                                .filter(SatImage.time_acquired >= start_date)\
                                .filter(SatImage.time_acquired <= end_date).all()
    images_geojson = create_images_geojson(_session,images)
    df_images = create_images_df(images)

    return images, images_geojson, df_images


@st.experimental_memo
def get_countries_with_filters(_session, sat_names, cloud_cover, start_date, end_date):
    '''
    gets all country objects with total images per country from postgis with applied filters.
    Creates geojson and df. Does that in this function to make single caching possible
    '''
    LOGGER.info('Getting countries from DB')
    
    subquery = _session.query(Satellite.id).filter(Satellite.name == sat_names).subquery()
    countries = _session.query(Country.iso, Country.name, Country.geom, func.count(SatImage.geom).label('total_images'))\
                                                            .join(Country.sat_images)\
                                                            .filter(SatImage.time_acquired >= start_date,
                                                                    SatImage.time_acquired <= end_date,
                                                                    SatImage.cloud_cover <= cloud_cover,
                                                                    SatImage.sat_id.in_(select(subquery)))\
                                                            .group_by(Country.iso).all()
    countries_geojson = create_country_geojson(countries)
    df_countries = create_countries_df(countries)
    return countries, countries_geojson, df_countries