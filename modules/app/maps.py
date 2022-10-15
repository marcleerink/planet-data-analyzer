import folium
from folium.plugins import HeatMap, HeatMapWithTime
from geoalchemy2.shape import to_shape
from geojson import Feature, FeatureCollection, dumps
from streamlit_folium import st_folium
import pandas as pd
import streamlit as st


def get_lat_lon_lst(all_images):
    lon_list = [image.lon for image in all_images]
    lat_list = [image.lat for image in all_images]
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

def heatmap(all_images, sat_names):
    all_images_lat_lon_lst = get_lat_lon_lst(all_images)
    map = create_basemap(lat_lon_list=all_images_lat_lon_lst)

    heat_data_list = [
        [all_images_lat_lon_lst, sat_names]
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