from sqlalchemy import func, select
from sqlalchemy.orm import session
from sqlalchemy.ext import baked
import pandas as pd
from geoalchemy2.shape import to_shape
from geojson import Feature, FeatureCollection, dumps
import json
import datetime
import geopandas as gpd
import streamlit as st
import time
from database.db import SatImage, Satellite, City, Country, LandCoverClass

from config import LOGGER
def query_all_countries_name(_session: session.Session) -> list[str]:
    query = _session.query(Country)
    return [i.name for i in query]


def query_asset_types_from_image(_image: SatImage) -> list[str]:
    return [i.id for i in _image.item_types.assets]


def query_land_cover_class_from_image(_image: SatImage) -> list[str]:
    return list(set([i.featureclass for i in _image.land_cover_class]))

@st.experimental_memo
def query_distinct_satellite_names(_session: session.Session) -> list[str]:
    query = _session.query(Satellite.name).distinct()
    return sorted([sat.name for sat in query])


def get_lat_lon_from_images(gdf_images: gpd.GeoDataFrame) -> list[tuple[float]]:
    """gets lon and lat for each row in gdf_images"""   
    return [(x,y) for x,y in zip(gdf_images['lat'],
                                        gdf_images['lon'])]
    

@st.experimental_memo
def query_sat_images_with_filter(_session: session.Session,
                                 sat_names: list,
                                 cloud_cover: float,
                                 start_date: datetime.date,
                                 end_date: datetime.date,
                                 country_name: str) -> gpd.GeoDataFrame:
    '''
    gets all sat images objects from postgis with applied filters. 
    '''
    t1 = time.time()
    subquery = _session.query(Country.geom).filter(
        Country.name == country_name).scalar_subquery()
    query = _session.query(SatImage.id, 
                            SatImage.clear_confidence_percent, 
                            SatImage.cloud_cover,
                            SatImage.time_acquired,
                            SatImage.sat_id,
                            Satellite.name.label('sat_name'),
                            Satellite.pixel_res.label('pixel_res'),
                            SatImage.item_type_id,
                            SatImage.lon.label('lon'),
                            SatImage.lat.label('lat'),
                            SatImage.area_sqkm,
                            LandCoverClass.featureclass.label('land_cover_class'),
                            SatImage.geom).join(SatImage.satellites).join(SatImage.land_cover_class, isouter=True)\
                                                .filter(Satellite.name.in_(sat_names))\
                                                .filter(SatImage.geom.ST_Intersects(subquery))\
                                                .filter(SatImage.time_acquired >= start_date)\
                                                .filter(SatImage.time_acquired <= end_date)\
                                                .filter(SatImage.cloud_cover <= cloud_cover)
    
    gdf=gpd.read_postgis(sql=query.statement, con=query.session.bind, crs=4326)
    gdf['area_sqkm'] = gdf['area_sqkm'].round(3)
    t2 = time.time()
    LOGGER.info(f'query sat images took {t2-t1} seconds')
    return gdf

@st.experimental_memo
def query_cities_with_filters(_session: session.Session,
                              sat_names: list,
                              cloud_cover: float,
                              start_date: datetime.date,
                              end_date: datetime.date,
                              country_name: str) -> list[Country]:
    '''
    gets all cities with total images per city from postgis with applied filters.
    '''
    t1 = time.time()
    subquery_country = _session.query(Country.geom).filter(
        Country.name == country_name).scalar_subquery()

    subquery_sat = _session.query(Satellite.id).filter(
        Satellite.name.in_(sat_names)).subquery()

    query = _session.query(City.id, 
                            City.name, 
                            City.buffer.label('geom'), 
                            func.count(SatImage.id).label('total_images'))\
                            .join(City.sat_images)\
                            .filter(SatImage.geom.ST_Intersects(subquery_country))\
                            .filter(SatImage.sat_id.in_(select(subquery_sat)))\
                            .filter(SatImage.time_acquired >= start_date,
                                    SatImage.time_acquired <= end_date,
                                    SatImage.cloud_cover <= cloud_cover)\
                            .group_by(City.id)

    gdf = gpd.read_postgis(sql=query.statement, con=query.session.bind, crs=4326)
    t2 = time.time()
    LOGGER.info(f'query cities took {t2-t1} seconds')
    return gdf

@st.experimental_memo
def query_land_cover_classes_with_filters(_session: session.Session,
                                          sat_names: list,
                                          cloud_cover: float,
                                          start_date: datetime.date,
                                          end_date: datetime.date,
                                          country_name: str) -> list[LandCoverClass]:
    t1 = time.time()
    subquery_country = _session.query(Country.geom).filter(
        Country.name == country_name).scalar_subquery()
    subquery_sat = _session.query(Satellite.id).filter(
        Satellite.name.in_(sat_names)).subquery()
    query = _session.query(LandCoverClass, 
                            func.count(SatImage.id).label('total_images'))\
                                .join(LandCoverClass.sat_image)\
                                .filter(SatImage.geom.ST_Intersects(subquery_country))\
                                .filter(SatImage.sat_id.in_(select(subquery_sat)))\
                                .filter(SatImage.time_acquired >= start_date,
                                        SatImage.time_acquired <= end_date,
                                        SatImage.cloud_cover <= cloud_cover)\
                                .group_by(LandCoverClass.id)

    gdf = gpd.read_postgis(sql=query.statement, con=query.session.bind, crs=4326)
    t2 = time.time()
    LOGGER.info(f'query land cover classes took {t2-t1} seconds')
    return gdf