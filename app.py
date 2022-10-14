import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium
import folium
from modules.database.db import ENGINE, SESSION, SatImage, Satellite, City, Country
from folium.plugins import HeatMap, HeatMapWithTime
from sqlalchemy import select
import json
import pandas as pd
from datetime import datetime
from geoalchemy2.shape import from_shape
from shapely import wkt
from itertools import chain
from sqlalchemy import cast, String


APP_TITLE = "Satellite Image Joins"
APP_SUB_TITLE = 'Source: Planet'
time_interval = 'Day'
start_date = '2022-10-01'
end_date = datetime.utcnow().strftime("%Y-%m-%d")

session = SESSION()

def get_all_images():
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
    return gpd.read_postgis(sql=sql, con=ENGINE, crs=4326)

def get_images_from_satellite(sat_name):
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
        WHERE satellites.name = '{}'
        """.format(sat_name)

    return gpd.read_postgis(sql=sql, con=ENGINE, crs=4326)

def get_lat_lon_lst(lat,lon):
    return list(map(list,zip(lat,lon)))


def get_total_images_countries():
    sql = """
        SELECT iso, name, countries.geom, count(sat_images.geom) AS total_images
        FROM countries
        LEFT JOIN sat_images ON ST_DWithin(countries.geom, sat_images.geom, 0)
        GROUP BY countries.iso
        """
    return gpd.read_postgis(sql=sql, con=ENGINE, crs=4326)

def footprints(map, gdf, name):
    # geojson_str = gdf.to_json()
    # geojson = json.loads(geojson_str)
    
    for _, r in gdf.iterrows():
        folium.GeoJson(data=r['geom'],
            control=False,
            tooltip=folium.GeoJsonTooltip(
                    fields=['id', 'sat_name', 'pixel_res', 'cloud_cover'],
                    aliases=['ID:  ','Satellite Type: ', 'Pixel Resolution(meter per pixel): ', 'cloud_cover: ']
            )).add_to(map)
    return map


def choropleth_map(countries):
    map = folium.Map(location=[52.5200, 13.4050], 
                        zoom_start=3)

    countries_geojson = gpd.GeoSeries(countries.set_index('iso')['geom']).to_json()
    
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

def heatmap(planetscope_images, skysat_images):
    map = folium.Map(location=[52.5200, 13.4050], 
                        zoom_start=7)
    folium.TileLayer('CartoDB positron',name="Light Map",control=False).add_to(map)

    
    planetscope_lat_lon_lst = get_lat_lon_lst((planetscope_images['lat']), 
                                                planetscope_images['lon'])
    
    skysat_lat_lon_lst = get_lat_lon_lst(skysat_images['lat'],
                                        skysat_images['lon'])
    heat_data_list = [
        [planetscope_lat_lon_lst, 'PlanetScope Images'],
        [skysat_lat_lon_lst, 'SkySat Images']
    ]
    
    for heat_data, title in heat_data_list:
        HeatMap(data=heat_data, name=title).add_to(map)

    folium.LayerControl().add_to(map)
    st_folium(map, height= 500, width=700)

def toolbar_map(all_images):
    map = folium.Map(location=[52.5200, 13.4050], 
                        zoom_start=7)
    folium.TileLayer('CartoDB positron',name="Light Map",control=False).add_to(map)
    
    all_images['time_acquired'] = all_images['time_acquired'].dt.strftime('%Y-%m-%d')

    image_geojson = all_images.to_json(drop_id=True)
    
    
    folium.Choropleth(geo_data=image_geojson,
                    name='Choropleth: Total Satellite Imagery per Country',
                    data=all_images,
                    columns=['id', 'cloud_cover'],
                    key_on ='feature.properties.id',
                    fill_color='YlGnBu',
                    legend_name='Total Satellite Images',
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
    
def heatmap_time(gdf, time_interval, start_date, end_date):
    
    map = folium.Map(location=[52.5200, 13.4050], 
                        zoom_start=7)
    #create time interval column in gdf datetime type
    gdf[time_interval] = gdf["time_acquired"].dt.to_period(time_interval[0]).astype(str)

    # create dataframe with time index to merge gdf with so that intervals without usage are also shown
    period_range = pd.period_range(start=start_date, end=end_date, freq=time_interval[0])
    interval_list = list(period_range.astype(str))
    df_intervals = pd.DataFrame({time_interval: interval_list})

    # merge df_agg, df_agg_mean to df_intervals
    gdf = pd.merge(left=df_intervals,
                        right=gdf,
                        how='left',
                        left_on=time_interval,
                        right_on=time_interval)

    # loop through each time interval for list of all geometries per time interval
    heat_time_data_list = []
    for t_i in gdf[time_interval].sort_values().unique(): 
        heat_time_data_list.append(gdf.loc[gdf[time_interval] == t_i,
        ['lat', 'lon']]\
        .groupby(['lat', 'lon'])\
        .sum().reset_index().values.tolist())

    # creating a time index with the time-interval
    time_index = []
    for i in gdf[time_interval].unique():
        time_index.append(i)

    # create heatmap with time
    HeatMapWithTime(data=heat_time_data_list,
                    index=time_index, 
                    name=f"All images{time_interval}", 
                    show=False).add_to(map)

    folium.LayerControl().add_to(map)
    st_folium(map, height= 500, width=700)

def main():
    #config
    st.set_page_config(page_title=APP_TITLE, layout='wide')
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)
    
    
    planetscope_images = get_images_from_satellite('Planetscope')
    skysat_images = get_images_from_satellite('Skysat')
    
    countries = get_total_images_countries()

    all_images = get_all_images()
    
    # #map
    choropleth_map(countries)
    heatmap(planetscope_images, skysat_images)
    # # heatmap_time(planetscope_images,time_interval, start_date, end_date)
    toolbar_map(all_images)

    
if __name__=='__main__':
    main()