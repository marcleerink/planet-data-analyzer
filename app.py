from re import S
import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium
import folium
from modules.database.db import ENGINE, SESSION, SatImage, Satellite, City, Country
from folium.plugins import HeatMap, HeatMapWithTime
from sqlalchemy import select, func
import json
import pandas as pd
from datetime import datetime, timedelta
from geoalchemy2.shape import from_shape, to_shape
from shapely import wkt
from shapely.wkb import loads
from itertools import chain
from sqlalchemy import cast, String
from geojson import Feature, FeatureCollection, dumps

APP_TITLE = "Satellite Image Joins"
APP_SUB_TITLE = 'Source: Planet'
session = SESSION()

def get_images_with_filter(session, sat_names,cloud_cover, start_date, end_date):
    '''
    gets all sat images objects from postgis with applied filters, 
    '''
    return session.query(SatImage).join(Satellite).filter(Satellite.name == sat_names)\
                                .filter(SatImage.cloud_cover <= cloud_cover)\
                                .filter(SatImage.time_acquired >= start_date)\
                                .filter(SatImage.time_acquired <= end_date).all()

def get_countries_with_filters(session, sat_names, cloud_cover, start_date, end_date):
    subquery = session.query(Satellite.id).filter(Satellite.name == sat_names).subquery()
    return session.query(Country.iso, Country.name, Country.geom, func.count(SatImage.geom).label('total_images'))\
                                                            .join(Country.sat_images)\
                                                            .filter(SatImage.time_acquired >= start_date,
                                                                    SatImage.time_acquired <= end_date,
                                                                    SatImage.cloud_cover <= cloud_cover,
                                                                    SatImage.sat_id.in_(select(subquery)))\
                                                            .group_by(Country.iso).all()

def get_lat_lon_lst(all_images):
    lon_list = [image.lon for image in all_images]
    lat_list = [image.lat for image in all_images]
    return list(map(list,zip(lat_list,lon_list)))

def get_min_max_list(list):
    min_v = min(list)
    max_v = max(list)
    return min_v, max_v

def create_basemap(zoom=None, lat_lon_list=None):
    if zoom:
        map = folium.Map(location=[52.5200, 13.4050], zoom_start=zoom)
    else:
        map = folium.Map(location=[52.5200, 13.4050])

    folium.TileLayer('CartoDB positron',name="Light Map",control=False).add_to(map)

    if lat_lon_list:
        map.fit_bounds(lat_lon_list, max_zoom=7)
    return map

def heatmap(all_images, sat_names):
    all_images_lat_lon_lst = get_lat_lon_lst(all_images)
    map = create_basemap(lat_lon_list=all_images_lat_lon_lst)


    heat_data_list = [
        [all_images_lat_lon_lst, sat_names]
    ]

    for heat_data, title in heat_data_list:
        HeatMap(data=heat_data, name=title).add_to(map)

    folium.LayerControl().add_to(map)
    st_folium(map, height= 500, width=700)

def style_highlight_func():
    style_function = lambda x: {'fillColor': '#ffffff', 
                        'color':'#000000', 
                        'fillOpacity': 0.1, 
                        'weight': 0.1}
    highlight_function = lambda x: {'fillColor': '#000000', 
                            'color':'#000000', 
                            'fillOpacity': 0.50, 
                            'weight': 0.1}
    return style_function, highlight_function

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

def images_per_country_map(countries):
    map = create_basemap(zoom=4)
    
    countries_geojson = create_country_geojson(countries)
    df_countries = create_countries_df(countries)
    
    folium.Choropleth(geo_data=countries_geojson,
                    name='Choropleth: Total Satellite Imagery per Country',
                    data=df_countries,
                    columns=['iso', 'total_images'],
                    key_on ='feature.id',
                    fill_color='YlGnBu',
                    legend_name='Satellite Image per Country',
                    smooth_factor=0).add_to(map)
    
    style_func, highlight_func = style_highlight_func()
                    
    folium.GeoJson(
        countries_geojson,
        control=False,
        style_function=style_func,
        highlight_function = highlight_func,
        tooltip=folium.GeoJsonTooltip(
            fields=['name', 'total_images'],
            aliases=['Country:  ','Total Images: '],
            
            )).add_to(map)

    folium.LayerControl().add_to(map)
    st_folium(map, height= 500, width=700)

def create_images_df(images):
    return pd.DataFrame({
        'id': [image.id for image in images],
        'cloud_cover' : [image.cloud_cover for image in images],
        'pixel_res' : [image.pixel_res for image in images],
        'time_acquired': [image.time_acquired.strftime("%Y-%m-%d") for image in images],
        'sat_name' : [image.satellites.name for image in images]})
    
def create_images_geojson(images):
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

def image_info_map(images):
    map = create_basemap(lat_lon_list = get_lat_lon_lst(images))
    
    images_geojson = create_images_geojson(images)
    df_images = create_images_df(images)

    folium.Choropleth(geo_data=images_geojson,
                name='Choropleth: Satellite Imagery Cloud Cover',
                data=df_images,
                columns=['id', 'cloud_cover'],
                key_on ='feature.id',
                fill_color='YlGnBu',
                legend_name='Cloud Cover',
                smooth_factor=0).add_to(map)

    style_func, highlight_func = style_highlight_func()

    folium.GeoJson(
    images_geojson,
    control=False,
    style_function=style_func,
    highlight_function = highlight_func,
    tooltip=folium.GeoJsonTooltip(
        fields=['id', 'sat_name', 'cloud_cover' ,'area_sqkm', 'pixel_res', 'time_acquired'],
        aliases=['ID:  ','Satellite: ', 'Cloud Cover: ','Area Sqkm', 'Pixel Resolution: ', 'Time Acquired: '],
        
        )).add_to(map)
    
    folium.LayerControl().add_to(map)
    st_folium(map, height= 500, width=700)

def display_sat_name_filter(session):
    satellites = session.query(Satellite.name).distinct()
    sat_name_list = [sat.name for sat in satellites]
    return st.sidebar.radio('Satellite Providers',sat_name_list)

def display_time_filter():
    start_date = st.sidebar.date_input('Start Date', datetime.utcnow() - timedelta(days=7))
    end_date = st.sidebar.date_input('End_date', datetime.utcnow())

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    return start_date, end_date

def display_cloud_cover_filter():
    return st.sidebar.slider('Cloud Cover Threshold', 0.0, 1.0, step=0.1)
    
def main():
    #config
    st.set_page_config(page_title=APP_TITLE, layout='wide')
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)
    
    # add sidebar with filters
    sat_names = display_sat_name_filter(session)
    start_date, end_date = display_time_filter()
    cloud_cover = display_cloud_cover_filter()
    
    # get data
    images = get_images_with_filter(session, 
                                    sat_names, 
                                    cloud_cover, 
                                    start_date, 
                                    end_date)

    countries = get_countries_with_filters(session,sat_names,cloud_cover, start_date, end_date)
    
    if len(images) == 0:
        st.write('No Images available for selected filters')
    else:
        st.write('Total Satellite Images: {}'.format(len(images)))
        heatmap(images, sat_names)
        image_info_map(images)
        images_per_country_map(countries)

if __name__=='__main__':
    main()

