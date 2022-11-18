from sqlalchemy import func, select
from sqlalchemy.orm import session
import pandas as pd
from geoalchemy2.shape import to_shape
from geojson import Feature, FeatureCollection, dumps
import json
import datetime


from database.db import SatImage, Satellite, City, Country

def query_all_countries_name(_session: session.Session) -> list[str]:
    query=_session.query(Country)
    return [i.name for i in query]

def query_asset_types_from_image(_image: SatImage) -> list[str]:
    return [i.id for i in _image.item_types.assets]
    

def query_land_cover_class_from_image(_image: SatImage) -> list[str]:
    return list(set([i.featureclass for i in _image.land_cover_class]))
       

def create_images_df(_images: list[SatImage]):
    
    return pd.DataFrame({
        'id': [image.id for image in _images],
        'cloud_cover' : [image.cloud_cover for image in _images],
        'pixel_res' : [image.satellites.pixel_res for image in _images],
        'time_acquired': [image.time_acquired.strftime("%Y-%m-%d %H:%M:%S") for image in _images],
        'sat_name' : [image.satellites.name for image in _images]})


def create_images_geojson(_images: list[SatImage]) -> dict:
    json_lst=[]
    for i in _images:
        geometry = to_shape(i.geom)
        asset_type = query_asset_types_from_image(i)
        land_cover_class = query_land_cover_class_from_image(i)
        feature = Feature(
                id=i.id,
                geometry=geometry,
                properties={
                    "id" : i.id,
                    "cloud_cover" : i.cloud_cover,
                    "pixel_res" : i.satellites.pixel_res,
                    "time_acquired" : i.time_acquired.strftime("%Y-%m-%d %H:%M:%S"),
                    "sat_id" : i.sat_id,
                    "sat_name" : i.satellites.name,
                    "item_type_id" : i.item_type_id,
                    "asset_types" : asset_type,
                    "area_sqkm": i.area_sqkm,
                    "land_cover_class": land_cover_class
                })
        json_lst.append(feature)
    geojson_str = dumps(FeatureCollection(json_lst))
    return json.loads(geojson_str)


def create_country_geojson(_countries: list[Country]) -> dict:
    json_lst=[]
    
    for i in _countries:
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
    geojson_str = dumps(FeatureCollection(json_lst))
    return json.loads(geojson_str)


def create_countries_df(_countries: list[Country]) -> pd.DataFrame:
    return pd.DataFrame({
        'iso': [c.iso for c in _countries],
        'name' : [c.name for c in _countries],
        'total_images' : [c.total_images for c in _countries]})


def create_cities_geojson(_cities: list[City]) -> dict:
    json_lst=[]
    for i in _cities:
        geometry = to_shape(i.buffer)
        feature = Feature(
                id=i.id,
                geometry=geometry,
                properties={
                    "id" : i.id,
                    "name" : i.name,
                    "total_images" : i.total_images
                })
        json_lst.append(feature)
    geojson_str = dumps(FeatureCollection(json_lst))
    return json.loads(geojson_str)


def create_cities_df(_cities: list[Country]) -> pd.DataFrame:
    return pd.DataFrame({
        'id': [i.id for i in _cities],
        'name' : [i.name for i in _cities],
        'total_images' : [i.total_images for i in _cities]})

def query_distinct_satellite_names(_session: session.Session) -> list[str]:
    query = _session.query(Satellite.name).distinct()
    return [sat.name for sat in query]


def query_lat_lon_from_images(_images: list[SatImage]) -> list[tuple[float]]:
    """gets lon and lat for each SatImage model instance"""
    lon_list = [image.lon for image in _images]
    lat_list = [image.lat for image in _images]
    return list(map(list,zip(lat_list,lon_list)))


def query_sat_images_with_filter(_session: session.Session, 
                                sat_names: list, 
                                cloud_cover: float, 
                                start_date: datetime.date, 
                                end_date: datetime.date,
                                country_iso: str) -> list[SatImage]:
    '''
    gets all sat images objects from postgis with applied filters. 
    '''
    subquery = _session.query(Country.geom).filter(Country.iso == country_iso).subquery()
    return _session.query(SatImage).join(Satellite).filter(Satellite.name.in_(sat_names))\
                                .filter(SatImage.geom.ST_Intersects(subquery))\
                                .filter(SatImage.time_acquired >= start_date)\
                                .filter(SatImage.time_acquired <= end_date)\
                                .filter(SatImage.cloud_cover <= cloud_cover).all()
    

def query_countries_with_filters(_session: session.Session,
                                sat_names: list, 
                                cloud_cover: float, 
                                start_date: datetime.date, 
                                end_date: datetime.date) -> list[Country]:
    '''
    gets all country objects with total images per country from postgis with applied filters.
    '''

    subquery = _session.query(Satellite.id).filter(Satellite.name.in_(sat_names)).subquery()
    countries = _session.query(Country.iso, Country.name, Country.geom, func.count(SatImage.id).label('total_images'))\
                                                            .join(Country.sat_images)\
                                                            .filter(SatImage.time_acquired >= start_date,
                                                                    SatImage.time_acquired <= end_date,
                                                                    SatImage.cloud_cover <= cloud_cover,
                                                                    SatImage.sat_id.in_(select(subquery)))\
                                                            .group_by(Country.iso).all()
    
    return countries


def query_cities_with_filters(_session: session.Session,
                                sat_names: list, 
                                cloud_cover: float, 
                                start_date: datetime.date, 
                                end_date: datetime.date) -> list[Country]:
    '''
    gets all country objects with total images per country from postgis with applied filters.
    '''
    
    subquery = _session.query(Satellite.id).filter(Satellite.name.in_(sat_names)).subquery()
    countries = _session.query(City.id, City.name, City.buffer, func.count(SatImage.geom).label('total_images'))\
                                                            .join(City.sat_images)\
                                                            .filter(SatImage.time_acquired >= start_date,
                                                                    SatImage.time_acquired <= end_date,
                                                                    SatImage.cloud_cover <= cloud_cover,
                                                                    SatImage.sat_id.in_(select(subquery)))\
                                                            .group_by(City.id).all()
    
    return countries

