from re import S
import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium
import folium
from modules.database.db import ENGINE, SESSION, SatImage, Satellite, City, Country
from folium.plugins import HeatMap, HeatMapWithTime
from sqlalchemy import select
import json
import pandas as pd
from datetime import datetime, timedelta
from geoalchemy2.shape import from_shape
from shapely import wkt
from itertools import chain
from sqlalchemy import cast, String



APP_TITLE = "Satellite Image Joins"
APP_SUB_TITLE = 'Source: Planet'

# @st.cache(allow_output_mutation=True)
def get_db_conn():
    return ENGINE


st.cache(hash_funcs={ENGINE: id})
def get_all_images(engine):
    sql = """
        SELECT DISTINCT sat_images.id,
                        sat_images.cloud_cover,
                        sat_images.pixel_res,
                        sat_images.clear_confidence_percent,
                        sat_images.time_acquired,
                        ST_X(sat_images.centroid) AS lon,
                        ST_Y(sat_images.centroid) AS lat,
                        sat_images.geom AS geom,
                        satellites.name AS sat_name
        FROM sat_images, satellites 
        """
    return gpd.read_postgis(sql=sql, con=engine, crs=4326)

st.cache(hash_funcs={ENGINE: id})
def get_total_images_countries(engine):
    sql = """
        SELECT DISTINCT countries.iso AS iso, 
                countries.name AS name, 
                countries.geom, 
                sat_images.time_acquired AS time_acquired, 
                count(sat_images.geom) AS total_images
        FROM countries
        LEFT JOIN sat_images ON ST_DWithin(countries.geom, sat_images.geom, 0)
        GROUP BY countries.iso, sat_images.time_acquired
        """
    return gpd.read_postgis(sql=sql, con=engine, crs=4326)

# def get_images_from_satellite(sat_name):
#     sql = """
#         SELECT DISTINCT sat_images.id,
#                         sat_images.cloud_cover,
#                         sat_images.pixel_res,
#                         sat_images.clear_confidence_percent,
#                         sat_images.time_acquired,
#                         ST_X(sat_images.centroid) AS lon,
#                         ST_Y(sat_images.centroid) AS lat,
#                         sat_images.geom AS geom,
#                         satellites.name AS sat_name
#         FROM sat_images, satellites 
#         WHERE satellites.name = '{}'
#         """.format(sat_name)

#     return gpd.read_postgis(sql=sql, con=ENGINE, crs=4326)

def get_lat_lon_lst(lat,lon):
    return list(map(list,zip(lat,lon)))



def create_basemap():
    map = folium.Map(location=[52.5200, 13.4050], 
                        zoom_start=6)
    folium.TileLayer('CartoDB positron',name="Light Map",control=False).add_to(map)
    return map

def heatmap(all_images):
    map = create_basemap()

    all_images_lat_lon_lst = get_lat_lon_lst((all_images['lat']), 
                                all_images['lon'])
    
    heat_data_list = [
        [all_images_lat_lon_lst, 'PlanetScope Images']
    ]

    for heat_data, title in heat_data_list:
        HeatMap(data=heat_data, name=title).add_to(map)

    folium.LayerControl().add_to(map)
    st_folium(map, height= 500, width=700)

def images_per_country_map(countries):
    map = create_basemap()
    
    countries_geojson = gpd.GeoSeries(countries.set_index('iso')['geom']).to_json()
    
    # cast to string for geojson input
    countries['time_acquired'] = countries['time_acquired'].dt.strftime('%Y-%m-%d')
    
    folium.Choropleth(geo_data=countries_geojson,
                    name='Choropleth: Total Satellite Imagery per Country',
                    data=countries,
                    columns=['iso', 'total_images'],
                    key_on ='feature.id',
                    fill_color='YlGnBu',
                    legend_name='Satellite Image per Country',
                    smooth_factor=0).add_to(map)
    
    style_function = lambda x: {'fillColor': '#ffffff', 
                            'color':'#000000', 
                            'fillOpacity': 0.1, 
                            'weight': 0.1}
    highlight_function = lambda x: {'fillColor': '#000000', 
                                'color':'#000000', 
                                'fillOpacity': 0.50, 
                                'weight': 0.1}
                    
    folium.GeoJson(
        countries,
        control=False,
        style_function=style_function,
        highlight_function = highlight_function,
        tooltip=folium.GeoJsonTooltip(
            fields=['name', 'total_images'],
            aliases=['Country:  ','Total Images: '],
            
            )).add_to(map)
    folium.LayerControl().add_to(map)
    st_folium(map, height= 500, width=700)

def image_info_map(all_images):
    map = create_basemap()

    # cast to string for geojson input
    all_images['time_acquired'] = all_images['time_acquired'].dt.strftime('%Y-%m-%d')

    image_geojson = all_images.to_json(drop_id=True)
    
    folium.Choropleth(geo_data=image_geojson,
                name='Choropleth: Satellite Imagery Clear Confidence Percent',
                data=all_images,
                columns=['id', 'clear_confidence_percent'],
                key_on ='feature.properties.id',
                fill_color='YlGnBu',
                legend_name='Clear Confidence Percent',
                smooth_factor=0).add_to(map)

    style_function = lambda x: {'fillColor': '#ffffff', 
                        'color':'#000000', 
                        'fillOpacity': 0.1, 
                        'weight': 0.1}
    highlight_function = lambda x: {'fillColor': '#000000', 
                            'color':'#000000', 
                            'fillOpacity': 0.50, 
                            'weight': 0.1}
                
    folium.GeoJson(
    all_images,
    control=False,
    style_function=style_function,
    highlight_function = highlight_function,
    tooltip=folium.GeoJsonTooltip(
        fields=['id', 'sat_name', 'cloud_cover', 'clear_confidence_percent' ,'pixel_res', 'time_acquired'],
        aliases=['ID:  ','Satellite: ', 'Cloud Cover: ', 'Clear Confidence Percent: ', 'Pixel Resolution: ', 'Time Acquired: '],
        
        )).add_to(map)
    

    folium.LayerControl().add_to(map)
    st_folium(map, height= 500, width=700)

def apply_filters(df, sat_names, start_date, end_date):
    df = df.loc[(df['time_acquired'] > start_date) & (df['time_acquired'] <= end_date)]
    return df[df['sat_name'] == sat_names]


def display_sat_name_filter(all_images):
    sat_name_list = list(all_images['sat_name'].unique())
    return st.sidebar.radio('Satellite Providers',sat_name_list, len(sat_name_list)-1)

def display_time_filter():
    start_date = st.sidebar.date_input('Start Date', datetime.utcnow() - timedelta(days=1))
    end_date = st.sidebar.date_input('End_date', datetime.utcnow())

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    return start_date, end_date

def main():
    #config
    st.set_page_config(page_title=APP_TITLE, layout='wide')
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)
    
    engine = get_db_conn()
    countries = get_total_images_countries(engine)
    all_images = get_all_images(engine)

    # add sidebar with filters
    sat_names = display_sat_name_filter(all_images)
    start_date, end_date = display_time_filter()


    all_images = apply_filters(all_images, sat_names, start_date, end_date)
    
    
    # countries = apply_filters(countries, sat_names, start_date, end_date)
    
    if len(all_images.index) ==0:
        st.write('No Images available for selected filters')
    else:
        heatmap(all_images)
        image_info_map(all_images)
        # images_per_country_map(countries)

if __name__=='__main__':
    main()