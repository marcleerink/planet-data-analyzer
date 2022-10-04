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

def centroid_from_polygon(gdf):
    '''Gets centroid of polygon using Albers Equal Area proj'''
    # Project to equal-area projected crs
    gdf = gdf.to_crs({'proj':'cea'}) 

    # convert polygons to points and add as column
    gdf['centroid'] = gdf.centroid

    # Project back to WGS84 geographic crs
    gdf= gdf.to_crs(epsg=4326)
    gdf['centroid'] = gdf['centroid'].to_crs(epsg=4326)

    return gdf

def folium_map(gdf):
    cities_sql = "SELECT * FROM cities WHERE name='Berlin'"
    cities = gpd.read_postgis(sql = cities_sql, con=ENGINE, crs=4326)


    planetscope = session.query(SatImage, Satellite).filter(Satellite.name == 'planetscope').all()
    for image in planetscope:
        print(image[0].get_centroid().get_wkt())
    map = folium.Map(location=[52.5200, 13.4050], zoom_start=7, tiles="cartodbpositron")

    gdf = centroid_from_polygon(gdf)
    lat_lon_list = [(x,y) for x,y in zip(gdf['centroid'].y , gdf['centroid'].x)]
    HeatMap(data=lat_lon_list,
            name='All Satellite Imagery').add_to(map)   
    
    # add footprints of sat images to map
    polygons_gjson = folium.features.GeoJson(gdf['geom'], name='Footprints Images', show=True)
    polygons_gjson.add_to(map)
     
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
    folium_map(gdf)


if __name__=='__main__':
    main()