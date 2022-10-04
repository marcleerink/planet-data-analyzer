import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium
import folium
from modules.database.db import ENGINE, SESSION, SatImage, Satellite, City, Country
from folium.plugins import HeatMap, HeatMapWithTime
from sqlalchemy import select


session = SESSION()
APP_TITLE = "Satellite Images"
APP_SUB_TITLE = 'Source: Planet'

def get_images_from_satellite(sat_name):
    sql = """
        SELECT ST_AsText(centroid) AS centroid,
                ST_X(centroid) AS lon,
                ST_Y(centroid) AS lat,
                geom
        FROM sat_images, satellites 
        WHERE satellites.name = '{}'
        """.format(sat_name)
    return gpd.read_postgis(sql = sql, con=ENGINE, crs=4326)

def get_lat_lon_lst(lat,lon):
    return list(map(list,zip(lat,lon)))

def get_sat_image_country(session, iso_code):
    '''gets a list of sat_images objects in a country'''
    query = session.query(Country).join(Country.sat_images)
    return [image for row in query for image in row.sat_images]

def folium_map():
    
    planetscope_images = get_images_from_satellite('planetscope')
    planetscope_lat_lon_lst = get_lat_lon_lst(planetscope_images['lat'], 
                                            planetscope_images['lon'])

    skysat_images = get_images_from_satellite('skysat')
    skysat_lat_lon_lst = get_lat_lon_lst(skysat_images['lat'],
                                        skysat_images['lon'])

    heat_data_list = [
        [planetscope_lat_lon_lst, 'PlanetScope Images'],
        [skysat_lat_lon_lst, 'SkySat Images']
    ]
    
    map = folium.Map(location=[52.5200, 13.4050], 
                        zoom_start=7, 
                        tiles="cartodbpositron",)

    for heat_data, title in heat_data_list:
        HeatMap(data=heat_data, name=title).add_to(map)
       
    
    # add footprints of sat images to map
    folium.features.GeoJson(planetscope_images['geom'], 
                                        name='PlanetScope Footprints', 
                                        show=True).add_to(map)
    folium.features.GeoJson(skysat_images['geom'], 
                                        name='Skysat Footprints', 
                                        show=True).add_to(map)
    
    countries_sql = """
                    SELECT iso, countries.geom, count(sat_images.geom) AS total_images
                    FROM countries
                    LEFT JOIN sat_images ON ST_DWithin(countries.geom, sat_images.geom, 0)
                    GROUP BY countries.iso
                    """
    
    countries = gpd.read_postgis(sql = countries_sql, con=ENGINE, crs=4326)
    countries_geojson = gpd.GeoSeries(countries.set_index('iso')['geom']).to_json()

    folium.Choropleth(geo_data=countries_geojson,
                    name='Total Satellite Imagery per Country',
                    data=countries,
                    columns=['iso', 'total_images'],
                    key_on ='feature.id',
                    legend_name='Total Satellite Images').add_to(map)
    
     
    folium.LayerControl().add_to(map)
    st_map = st_folium(map, height= 700, width=700)

def main():
    #config
    st.set_page_config(APP_TITLE)
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)
    
    #map
    folium_map()


if __name__=='__main__':
    main()