import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium
import folium
from modules.database.db import ENGINE, SESSION, SatImage, Satellite
from folium.plugins import HeatMap, HeatMapWithTime
from sqlalchemy import select


session = SESSION()
APP_TITLE = "Satellite Images"
APP_SUB_TITLE = 'Source: Planet'


def folium_map():
    cities_sql = "SELECT * FROM cities WHERE name='Berlin'"
    cities = gpd.read_postgis(sql = cities_sql, con=ENGINE, crs=4326)

    planetscope_sql = """
                    SELECT ST_AsText(centroid) AS centroid,
                            ST_X(centroid) AS lon,
                            ST_Y(centroid) AS lat,
                            geom
                    FROM sat_images, satellites 
                    WHERE satellites.name = 'planetscope'
                    """
    planetscope_images = gpd.read_postgis(sql = planetscope_sql, con=ENGINE, crs=4326)
    print(planetscope_images)
    skysat_sql = "SELECT * FROM sat_images, satellites WHERE satellites.name = 'skysat'"
    
    skysat_images = gpd.read_postgis(sql = skysat_sql, con=ENGINE, crs=4326)
    
    
    map = folium.Map(location=[52.5200, 13.4050], zoom_start=7, tiles="cartodbpositron")

    # HeatMap(data=lat_lon_list,
    #         name='All Satellite Imagery').add_to(map)   
    
    # add footprints of sat images to map
    # polygons_gjson = folium.features.GeoJson(gdf['geom'], name='Footprints Images', show=True)
    # polygons_gjson.add_to(map)
     
    folium.LayerControl().add_to(map)
    st_map = st_folium(map, height= 700, width=700)
def main():
    #config
    st.set_page_config(APP_TITLE)
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)

    # load data
    sql = 'SELECT * FROM sat_images'
    gdf = gpd.read_postgis(sql = sql, con=ENGINE)
    
    #map
    folium_map()


if __name__=='__main__':
    main()