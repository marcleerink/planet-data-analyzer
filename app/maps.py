import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd
import geopandas as gpd


def create_basemap(zoom: int=None, lat_lon_list: list=None) -> folium.Map:
    if zoom:
        map = folium.Map(location=[52.5200, 13.4050], zoom_start=zoom)
    else:
        map = folium.Map(location=[52.5200, 13.4050])

    folium.TileLayer('CartoDB positron',name="Light Map",control=False).add_to(map)

    if lat_lon_list:
        map.fit_bounds(lat_lon_list, max_zoom=7)
    return map

def heatmap(map: folium.Map, lat_lon_lst: list, sat_name: str) -> tuple[folium.Map, dict]:
    """instantiates a HeatMap with lat_lon coordinates."""
    heat_data_list = [
        [lat_lon_lst, sat_name]
    ]

    for heat_data, title in heat_data_list:
        HeatMap(data=heat_data, name=title).add_to(map)
    
    return map , st_folium(map, height= 500, width=700, key='Heatmap')
    

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
    map: folium.Map, images_geojson: str, df_images: pd.DataFrame) -> tuple[folium.Map, dict]:
    
    
    folium.Choropleth(geo_data=images_geojson,
                name='Choropleth: Satellite Imagery Cloud Cover',
                data=df_images,
                columns=['id', 'area_sqkm'],
                key_on ='feature.id',
                fill_color='YlGnBu',
                legend_name='Area Coverage in Sqkm',
                smooth_factor=0).add_to(map)

    folium.GeoJson(
    images_geojson,
    control=False,
    style_function=_tooltip_style_func(),
    highlight_function = _tooltip_highlight_func(),
    tooltip=folium.GeoJsonTooltip(
        aliases=['ID:  ','Satellite: ', 'Cloud Cover: ','Area Sqkm', 
            'Pixel Resolution: ', 'Item Type: ' , 'Time Acquired: ', 'Land Cover Classes: '],
        fields=['id', 'sat_name', 'cloud_cover' ,'area_sqkm', 
        'pixel_res', 'item_type_id', 'time_acquired', 'land_cover_class'],
        )).add_to(map)
    
    return map, st_folium(map, height= 500, width=700, key='Image')


def images_per_city(
     map: folium.Map, cities_geojson: str, df_cities: pd.DataFrame) -> tuple[folium.Map, dict]:
    """instantiates a Chloropleth map that dislays images per city"""
    
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

def images_per_land_cover_class( 
    map: folium.Map, gdf_land_cover: gpd.GeoDataFrame) -> tuple[folium.Map, dict]:
    """instantiates a Chloropleth map that dislays images per land cover class"""

    land_cover_geojson = gdf_land_cover.to_json()
    
    folium.Choropleth(geo_data=land_cover_geojson,
                    name='Choropleth: Total Satellite Imagery per Land Cover Class',
                    data=gdf_land_cover,
                    columns=['id', 'total_images'],
                    key_on ='feature.properties.id',
                    fill_color='YlGnBu',
                    legend_name='Satellite Image per Land Cover Class',
                    smooth_factor=0).add_to(map)

    folium.GeoJson(
        land_cover_geojson,
        control=False,
        style_function=_tooltip_style_func(),
        highlight_function =_tooltip_highlight_func(),
        tooltip=folium.GeoJsonTooltip(
            fields=['featureclass', 'total_images'],
            aliases=['Featureclass:  ','Total Images: '],
            )).add_to(map)

    return map, st_folium(map, height= 500, width=700, key='Land_Cover')