import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd
from typing import Tuple
import geopandas as gpd

from modules.app.query import query_lat_lon_sat_images

def create_basemap(zoom: int=None, lat_lon_list: list=None) -> folium.Map:
    if zoom:
        map = folium.Map(location=[52.5200, 13.4050], zoom_start=zoom)
    else:
        map = folium.Map(location=[52.5200, 13.4050])

    folium.TileLayer('CartoDB positron',name="Light Map",control=False).add_to(map)

    if lat_lon_list:
        map.fit_bounds(lat_lon_list, max_zoom=7)
    return map

def heatmap(map: folium.Map, lat_lon_lst: list, sat_name: str) -> Tuple[folium.Map, dict]:
    """instantiates a HeatMap with lat_lon coordinates."""
    heat_data_list = [
        [lat_lon_lst, sat_name]
    ]

    for heat_data, title in heat_data_list:
        HeatMap(data=heat_data, name=title).add_to(map)
    
    return map , st_folium(map, height= 500, width=700)
    

def _tooltip_style_func():
    return lambda x: {'fillColor': '#ffffff', 
                        'color':'#000000', 
                        'fillOpacity': 0.1, 
                        'weight': 0.1}
def _tooltip_highlight_func():
    return lambda x: {'fillColor': '#000000', 
                            'color':'#000000', 
                            'fillOpacity': 0.50, 
                            'weight': 0.1}


def image_info_map(
    map: folium.Map, images_geojson: str, df_images: pd.DataFrame) -> Tuple[folium.Map, dict]:
    
    
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
    style_function=_tooltip_style_func(),
    highlight_function = _tooltip_highlight_func(),
    tooltip=folium.GeoJsonTooltip(
        aliases=['ID:  ','Satellite: ', 'Cloud Cover: ','Area Sqkm', 'Pixel Resolution: ', 'Item Type: ' , 'Asset_Types: ', 'Time Acquired: '],
        fields=['id', 'sat_name', 'cloud_cover' ,'area_sqkm', 'pixel_res', 'item_type_id', 'asset_types', 'time_acquired'],
        )).add_to(map)
    
    return map, st_folium(map, height= 500, width=700)
    


def images_per_country_map(
    map: folium.Map, countries_geojson: str, df_countries: pd.DataFrame) -> Tuple[folium.Map, dict]:
    """instantiates a Chloropleth map that dislays images per country"""

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
        style_function=_tooltip_style_func(),
        highlight_function =_tooltip_highlight_func(),
        tooltip=folium.GeoJsonTooltip(
            fields=['name', 'total_images'],
            aliases=['Country:  ','Total Images: '],
            
            )).add_to(map)
    
    return map, st_folium(map, height= 500, width=700, key='Country')


def images_per_city(
     map: folium.Map, cities_geojson: str, df_cities: pd.DataFrame) -> Tuple[folium.Map, dict]:
    """instantiates a Chloropleth map that dislays images per country"""
    
    folium.Choropleth(geo_data=cities_geojson,
                    name='Choropleth: Total Satellite Imagery per City',
                    data=df_cities,
                    columns=['id', 'total_images'],
                    key_on ='feature.id',
                    fill_color='YlGnBu',
                    legend_name='Satellite Image per City',
                    smooth_factor=0).add_to(map)

    folium.GeoJson(
        cities_geojson,
        control=False,
        style_function=_tooltip_style_func(),
        highlight_function =_tooltip_highlight_func(),
        tooltip=folium.GeoJsonTooltip(
            fields=['name', 'total_images'],
            aliases=['City:  ','Total Images: '],
            )).add_to(map)

    return map, st_folium(map, height= 500, width=700, key='City')
