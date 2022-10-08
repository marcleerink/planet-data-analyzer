import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium
import folium
from modules.database.db import ENGINE, SESSION, SatImage, Satellite, City, Country
from folium.plugins import HeatMap, HeatMapWithTime
from sqlalchemy import select
import json

APP_TITLE = "Satellite Images"
APP_SUB_TITLE = 'Source: Planet'


def init_db_connect():
    return SESSION()

def get_images_from_satellite(sat_name):
    sql = """
        SELECT DISTINCT sat_images.id,
                        sat_images.cloud_cover,
                        sat_images.pixel_res,
                        sat_images.clear_confidence_percent,
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
            # tooltip=folium.GeoJsonTooltip(
            # fields=['id', 'sat_name', 'pixel_res', 'cloud_cover'],
            # aliases=['ID:  ','Satellite Type: ', 'Pixel Resolution(meter per pixel): ', 'cloud_cover: ']
            ).add_to(map)
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

    planetscope_lat_lon_lst = get_lat_lon_lst(planetscope_images['lat'], 
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

def toolbar_map(planetscope_images, skysat_images):
    map = folium.Map(location=[52.5200, 13.4050], 
                        zoom_start=7)
    folium.TileLayer('CartoDB positron',name="Light Map",control=False).add_to(map)

    map = footprints(map, planetscope_images, name='PlanetScope Footprints')
    map = footprints(map, skysat_images, name='SkySat Footprints')

    folium.LayerControl().add_to(map)
    st_folium(map, height= 500, width=700)
    


def main():
    #config
    st.set_page_config(APP_TITLE)
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)
    
    planetscope_images = get_images_from_satellite('Planetscope')
    
    skysat_images = get_images_from_satellite('Skysat')
    countries = get_total_images_countries()

    #map
    choropleth_map(countries)
    heatmap(planetscope_images, skysat_images)
    toolbar_map(planetscope_images,skysat_images)

    


if __name__=='__main__':
    main()