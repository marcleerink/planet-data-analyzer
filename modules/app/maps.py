import folium
from folium.plugins import HeatMap, HeatMapWithTime
from geoalchemy2.shape import to_shape
from geojson import Feature, FeatureCollection, dumps
from streamlit_folium import st_folium
import pandas as pd
import streamlit as st


def get_lat_lon_lst(images):
    lon_list = [image.lon for image in images]
    lat_list = [image.lat for image in images]
    return list(map(list,zip(lat_list,lon_list)))

def create_basemap(zoom=None, lat_lon_list=None):
    if zoom:
        map = folium.Map(location=[52.5200, 13.4050], zoom_start=zoom)
    else:
        map = folium.Map(location=[52.5200, 13.4050])

    folium.TileLayer('CartoDB positron',name="Light Map",control=False).add_to(map)

    if lat_lon_list:
        map.fit_bounds(lat_lon_list, max_zoom=7)
    return map

def heatmap(image, sat_names):
    lat_lon_lst = get_lat_lon_lst(image)
    map = create_basemap(lat_lon_list=lat_lon_lst)

    heat_data_list = [
        [lat_lon_lst, sat_names]
    ]

    for heat_data, title in heat_data_list:
        HeatMap(data=heat_data, name=title).add_to(map)

    st_folium(map, height= 500, width=700)

def tooltip_style_func():
    return lambda x: {'fillColor': '#ffffff', 
                        'color':'#000000', 
                        'fillOpacity': 0.1, 
                        'weight': 0.1}
def tooltip_highlight_func():
    return lambda x: {'fillColor': '#000000', 
                            'color':'#000000', 
                            'fillOpacity': 0.50, 
                            'weight': 0.1}

def images_per_country_map(countries_geojson, df_countries):
    map = create_basemap(zoom=4)
    
    folium.Choropleth(geo_data=countries_geojson,
                    name='Choropleth: Total Satellite Imagery per Country',
                    data=df_countries,
                    columns=['iso', 'total_images'],
                    key_on ='feature.id',
                    fill_color='YlGnBu',
                    legend_name='Satellite Image per Country',
                    smooth_factor=0).add_to(map)
    
    
                    
    folium.GeoJson(
        countries_geojson,
        control=False,
        style_function=tooltip_style_func(),
        highlight_function =tooltip_highlight_func(),
        tooltip=folium.GeoJsonTooltip(
            fields=['name', 'total_images'],
            aliases=['Country:  ','Total Images: '],
            
            )).add_to(map)

    st_folium(map, height= 500, width=700)


def image_info_map(images, images_geojson, df_images):
    map = create_basemap(lat_lon_list = get_lat_lon_lst(images))

    folium.Choropleth(geo_data=images_geojson,
                name='Choropleth: Satellite Imagery Cloud Cover',
                data=df_images,
                columns=['id', 'cloud_cover'],
                key_on ='feature.id',
                fill_color='YlGnBu',
                legend_name='Cloud Cover',
                smooth_factor=0).add_to(map)

    folium.GeoJson(
    images_geojson,
    control=False,
    style_function=tooltip_style_func(),
    highlight_function = tooltip_highlight_func(),
    tooltip=folium.GeoJsonTooltip(
        fields=['id', 'sat_name', 'cloud_cover' ,'area_sqkm', 'pixel_res', 'time_acquired'],
        aliases=['ID:  ','Satellite: ', 'Cloud Cover: ','Area Sqkm', 'Pixel Resolution: ', 'Time Acquired: ']
        )).add_to(map)
    
    st_folium(map, height= 500, width=700)