"""Module containing Folium Streamlit Maps"""
import folium
from folium.plugins import HeatMap, HeatMapWithTime
from streamlit_folium import st_folium, folium_static
import streamlit as st
from datetime import datetime
import geopandas as gpd
import pandas as pd


def create_basemap(zoom: int = None, lat_lon_list: list = None) -> folium.Map:
    """Creates a folium basemap layer. 
    Optionally sets a zoom level or zooms the map according to a lsit with lat_lon coordinates"""
    if zoom:
        map = folium.Map(location=[52.5200, 13.4050], zoom_start=zoom)
    else:
        map = folium.Map(location=[52.5200, 13.4050])

    folium.TileLayer('CartoDB positron', name="Light Map",
                     control=False).add_to(map)

    if lat_lon_list:
        map.fit_bounds(lat_lon_list, max_zoom=7)
    return map


def heatmap(map: folium.Map,
            gdf: gpd.GeoDataFrame,
            lat_lon_lst: list, 
            sat_name: list, 
            ) -> tuple[folium.Map, dict]:
    """instantiates a HeatMap with lat_lon coordinates."""
    # add polygon footprints to map layers
    folium.GeoJson(gdf['geom'],
                    name='Satellite Images Footprints').add_to(map)
    heat_data_list = [
        [lat_lon_lst, sat_name]
    ]

    for heat_data, title in heat_data_list:
        HeatMap(data=heat_data, name=title).add_to(map)
    

    return map, st_folium(map, height=500, width=700, key='Heatmap')

def heatmap_time_series(map: folium.Map, 
                        gdf: gpd.GeoDataFrame ,
                        sat_name: list, 
                        start_date: datetime, 
                        end_date: datetime, 
                        time_interval: str):
    
    #create time interval column in gdf datetime type
    gdf[time_interval] = gdf["time_acquired"].dt.to_period(time_interval[0]).astype(str)

    # create dataframe with time index to merge gdf with so that intervals without data are also shown
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
                    name=f"All Satellite Images Per {time_interval} for {sat_name}", 
                    show=False,
                    auto_play=True).add_to(map)

    return folium_static(map)

def _tooltip_style_func():
    return lambda x: {'fillColor': '#ffffff',
                      'color': '#000000',
                      'fillOpacity': 0.1,
                      'weight': 0.1}


def _tooltip_highlight_func():
    return lambda x: {'fillColor': '#000000',
                      'color': '#000000',
                      'fillOpacity': 0.50,
                      'weight': 0.1}


def image_info_map(
        map: folium.Map, gdf_images: gpd.GeoDataFrame) -> tuple[folium.Map, dict]:
    """instantiates a Choropleth map with tooltips per satellite image"""

    gdf_images['time_acquired'] = gdf_images['time_acquired'].dt.strftime(
        "%Y-%m-%d %H:%M:%S")
    images_geojson = gdf_images.to_json()

    folium.Choropleth(geo_data=images_geojson,
                      name='Choropleth: Satellite Imagery Cloud Cover',
                      data=gdf_images,
                      columns=['id', 'area_sqkm'],
                      key_on='feature.properties.id',
                      fill_color='YlGnBu',
                      legend_name='Area Coverage in Sqkm',
                      smooth_factor=0).add_to(map)

    folium.GeoJson(
        images_geojson,
        control=False,
        style_function=_tooltip_style_func(),
        highlight_function=_tooltip_highlight_func(),
        tooltip=folium.GeoJsonTooltip(
            aliases=['ID:  ', 'Satellite: ', 'Cloud Cover: ', 'Area Sqkm',
                     'Pixel Resolution: ', 'Item Type: ', 'Time Acquired: ', 'Land Cover Classes: '],
            fields=['id', 'sat_name', 'cloud_cover', 'area_sqkm',
                    'pixel_res', 'item_type_id', 'time_acquired', 'land_cover_class'],
        )).add_to(map)

    return map, st_folium(map, height=500, width=700, key='Image')


def images_per_city(
        map: folium.Map, gdf_cities: gpd.GeoDataFrame) -> tuple[folium.Map, dict]:
    """instantiates a Chloropleth map that dislays images per city"""

    cities_geojson = gdf_cities.to_json()

    folium.Choropleth(geo_data=cities_geojson,
                      name='Choropleth: Total Satellite Imagery per City',
                      data=gdf_cities,
                      columns=['id', 'total_images'],
                      key_on='feature.properties.id',
                      fill_color='YlGnBu',
                      legend_name='Satellite Image per City',
                      smooth_factor=0).add_to(map)

    folium.GeoJson(
        cities_geojson,
        control=False,
        style_function=_tooltip_style_func(),
        highlight_function=_tooltip_highlight_func(),
        tooltip=folium.GeoJsonTooltip(
            fields=['name', 'total_images'],
            aliases=['City:  ', 'Total Images: '],
        )).add_to(map)

    return map, st_folium(map, height=500, width=700, key='City')


def images_per_land_cover_class(
        map: folium.Map, gdf_land_cover: gpd.GeoDataFrame) -> tuple[folium.Map, dict]:
    """instantiates a Chloropleth map that dislays images per land cover class"""

    land_cover_geojson = gdf_land_cover.to_json()

    folium.Choropleth(geo_data=land_cover_geojson,
                      name='Choropleth: Total Satellite Imagery per Land Cover Class',
                      data=gdf_land_cover,
                      columns=['id', 'total_images'],
                      key_on='feature.properties.id',
                      fill_color='YlGnBu',
                      legend_name='Satellite Image per Land Cover Class',
                      smooth_factor=0).add_to(map)

    folium.GeoJson(
        land_cover_geojson,
        control=False,
        style_function=_tooltip_style_func(),
        highlight_function=_tooltip_highlight_func(),
        tooltip=folium.GeoJsonTooltip(
            fields=['featureclass', 'total_images'],
            aliases=['Featureclass:  ', 'Total Images: '],
        )).add_to(map)

    return map, st_folium(map, height=500, width=700, key='Land_Cover')


def land_cover_image_coverage(
        map: folium.Map, gdf: gpd.GeoDataFrame, gdf_land_cover_dissolved: gpd.GeoDataFrame) -> tuple[folium.Map, dict]:

    # add dissolved land cover class footprints
    land_cover_footprints = folium.GeoJson(gdf_land_cover_dissolved['geom'],
                                           name='Land Cover Class Footprints',)
    land_cover_footprints.add_to(map)

    # add choropleth layer with intersection between land cover classes and sat_images
    geojson = gdf.to_json()

    folium.Choropleth(geo_data=geojson,
                      name='Choropleth: Coverage per Land Cover Class',
                      data=gdf,
                      columns=['featureclass', 'coverage_percentage'],
                      key_on='feature.properties.featureclass',
                      fill_color='YlGnBu',
                      legend_name='Coverage percentage per Land Cover Class',
                      smooth_factor=0).add_to(map)

    folium.GeoJson(
        geojson,
        control=False,
        style_function=_tooltip_style_func(),
        highlight_function=_tooltip_highlight_func(),
        tooltip=folium.GeoJsonTooltip(
            fields=['featureclass', 'coverage_percentage'],
            aliases=['Featureclass:  ', 'Coverage Percentage: '],
        )).add_to(map)

    folium.LayerControl().add_to(map)

    return map, st_folium(map, height=500, width=700, key='coverage_percentage')
