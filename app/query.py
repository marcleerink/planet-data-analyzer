from sqlalchemy import func, select
from sqlalchemy.orm import session
import datetime
import geopandas as gpd
import streamlit as st
import time
from database.db import SatImage, Satellite, City, Country, LandCoverClass
from shapely import wkb

from config import LOGGER


@st.experimental_memo
def query_all_countries(_session: session.Session) -> list[str]:
    query = _session.query(Country)
    return [i for i in query]


@st.experimental_memo
def query_distinct_satellite_names(_session: session.Session) -> list[str]:
    query = _session.query(Satellite.name).distinct()
    return sorted([sat.name for sat in query])


def get_lat_lon_from_images(gdf_images: gpd.GeoDataFrame) -> list[tuple[float]]:
    """gets lon and lat for each row in gdf_images"""
    return [(x, y) for x, y in zip(gdf_images['lat'],
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

    query = _session.query(SatImage)\
        .join(SatImage.satellites)\
        .filter(SatImage.geom.ST_Intersects(subquery),
                Satellite.name.in_(sat_names),
                SatImage.time_acquired >= start_date,
                SatImage.time_acquired <= end_date,
                SatImage.cloud_cover <= cloud_cover).group_by(SatImage.id)

    gdf = gpd.read_postgis(sql=query.statement,
                           con=query.session.bind, crs=4326)

    # TODO get list of land cover classes directly in query (then all other extra queries here can be in one)
    gdf['land_cover_class'] = [query_land_cover_class_from_image(
        image) for image in query if image]
    gdf['lat'] = [i.lat for i in query]
    gdf['lon'] = [i.lon for i in query]
    gdf['area_sqkm'] = [i.area_sqkm for i in query]
    gdf['sat_name'] = [i.satellites.name for i in query]
    gdf['pixel_res'] = [i.satellites.pixel_res for i in query]
    gdf['area_sqkm'] = gdf['area_sqkm'].round(3)
    gdf = gdf.drop('centroid', axis=1)

    t2 = time.time()
    LOGGER.info(f'query sat images took {t2-t1} seconds')

    assert gdf.id.is_unique
    return gdf


def query_land_cover_class_from_image(_image: SatImage) -> list[str]:
    return list(set([i.featureclass for i in _image.land_cover_class]))

@st.experimental_memo
def query_cities_with_filters(_session: session.Session,
                              sat_names: list,
                              cloud_cover: float,
                              start_date: datetime.date,
                              end_date: datetime.date,
                              country_name: str) -> gpd.GeoDataFrame:
    '''
    gets all cities with total images per city from postgis with applied filters.
    '''
    t1 = time.time()
    sq_country_geom, sq_country_iso = _session.query(Country.geom, Country.iso).filter(
        Country.name == country_name).one()

    subquery_sat = _session.query(Satellite.id).filter(
        Satellite.name.in_(sat_names)).subquery()

    query = _session.query(City.id,
                           City.name,
                           City.buffer.label('geom'),
                           func.count(SatImage.id).label('total_images'))\
        .join(City.sat_images)\
        .filter(City.country_iso == sq_country_iso)\
        .filter(SatImage.geom.ST_Intersects(sq_country_geom))\
        .filter(SatImage.sat_id.in_(select(subquery_sat)))\
        .filter(SatImage.time_acquired >= start_date,
                SatImage.time_acquired <= end_date,
                SatImage.cloud_cover <= cloud_cover)\
        .group_by(City.id)

    gdf = gpd.read_postgis(sql=query.statement,
                           con=query.session.bind, crs=4326)
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
    
    gdf = gpd.read_postgis(sql=query.statement,
                           con=query.session.bind, crs=4326)
    print(gdf)
    t2 = time.time()
    LOGGER.info(f'query land cover classes took {t2-t1} seconds')
    return gdf

@st.experimental_memo
def query_land_cover_classes_with_filters_image_coverage(_session: session.Session,
                                          sat_names: list,
                                          cloud_cover: float,
                                          start_date: datetime.date,
                                          end_date: datetime.date,
                                          country_name: str) -> gpd.GeoDataFrame:
    t1 = time.time()
        
    query = f"""
    
    SELECT foo.featureclass as featureclass,
            ST_INTERSECTION(foo.geom, bar.geom) as geom, 
            ST_AREA(ST_INTERSECTION(foo.geom, bar.geom)) / ST_AREA(foo.geom) AS coverage_percentage
    FROM (
        SELECT featureclass, ST_TRANSFORM(ST_UNION(ST_BUFFER(ST_TRANSFORM(geom, 3035), 1)), 4326) as geom
        FROM land_cover_classes
        WHERE ST_INTERSECTS(geom, ((SELECT countries.geom AS geom 
                                FROM countries 
                                WHERE countries.name = '{country_name}')))
        GROUP BY featureclass
    ) AS foo, (
        SELECT ST_UNION(geom) as geom
        FROM sat_images
        WHERE ST_INTERSECTS(geom,((SELECT countries.geom AS geom 
                                FROM countries 
                                WHERE countries.name = '{country_name}')))
        AND sat_images.sat_id IN 
                (SELECT satellites.id
                FROM satellites
                WHERE satellites.name IN {tuple(sat_names)})
        AND sat_images.time_acquired >= '{start_date.strftime('%Y-%m-%d')}'
        AND sat_images.time_acquired <= '{end_date.strftime('%Y-%m-%d')}'
        AND sat_images.cloud_cover <= {cloud_cover}
        
    ) AS bar
    WHERE ST_INTERSECTS(foo.geom, bar.geom)
    
    
    ;"""

    gdf = gpd.read_postgis(sql=query,
                           con=_session.bind, crs=4326)

    gdf['coverage_percentage'] = gdf['coverage_percentage'] * 100
    gdf['coverage_percentage'] = gdf['coverage_percentage'].round(3)
    
    t2 = time.time()
    LOGGER.info(f'query land cover image coverage took {t2-t1} seconds')
    return gdf


@st.experimental_memo
def query_land_cover_geom_dissolved(_session: session.Session,
                                    country_name: str) -> gpd.GeoDataFrame:
    t1 = time.time()
        
    query = f"""
    SELECT featureclass, ST_UNION(geom) as geom
    FROM land_cover_classes
    WHERE ST_INTERSECTS(geom, ((SELECT countries.geom AS geom 
                            FROM countries 
                            WHERE countries.name = '{country_name}')))
    GROUP BY featureclass
    ;"""

    gdf = gpd.read_postgis(sql=query,
                           con=_session.bind, crs=4326)

    t2 = time.time()
    LOGGER.info(f'query land cover dissolved took {t2-t1} seconds')
    return gdf