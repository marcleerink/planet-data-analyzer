import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium
import folium
from modules.database.db import ENGINE, SESSION, SatImage
from folium.plugins import HeatMap, HeatMapWithTime


session = SESSION()
APP_TITLE = "Satellite Images"
APP_SUB_TITLE = 'Source: Planet'


def folium_map(gdf):
    cities_sql = "SELECT * FROM cities WHERE name='berlin'"
    cities = gpd.read_postgis(sql = cities_sql, con=ENGINE)

    map = folium.Map(location=[52.5200, 13.4050], zoom_start=7, tiles="cartodbpositron")

    choropleth = folium.Choropleth(
                        geo_data=cities.geom, 
                        data=gdf, 
                        columns=['sat_id', 'geom'])
    choropleth.geojson.add_to(map)

    sat_images = session.query(SatImage).all()
    lon_lat = [image.get_lon_lat() for image in sat_images]
    lon_lat_list = [[lon, *lat] for lon, lat in lon_lat]
    
    # lon_lat_list = [lon, lat] for elem in lon_lat for item in elem]
    
    
    
    
    

    st_map = st_folium(map, width=700, height=450)
def main():
    #config
    st.set_page_config(APP_TITLE)
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)

    # load data
    sql = 'SELECT * FROM sat_images'
    gdf = gpd.read_postgis(sql = sql, con=ENGINE)
    st.write(gdf.columns)
    #map
    folium_map(gdf)


if __name__=='__main__':
    main()