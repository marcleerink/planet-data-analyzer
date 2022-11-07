import pytest
import folium
from modules.app import maps
import pandas as pd
import geopandas as gpd
from tests.resources import fake_country_geojson, fake_image, fake_lat_lon_list


def test_create_basemap_fit_bounds_u():
    fake_map = folium.Map(location=[52.5200, 13.4050])
    fake_map.fit_bounds(fake_lat_lon_list.lat_lon_list, max_zoom=7)

    basemap = maps.create_basemap(zoom=None, lat_lon_list=fake_lat_lon_list.lat_lon_list)

    assert basemap.get_bounds() == fake_map.get_bounds()

def test_create_basemap_zoom_u():

    basemap = maps.create_basemap(zoom=8, lat_lon_list=None)

    assert basemap.location == [52.52, 13.405]

def test_create_basemaps_no_args():
    basemap = maps.create_basemap()
    
    assert basemap.location == [52.52, 13.405]


def test_heatmap():
    fake_map = folium.Map(location=[52.5200, 13.4050])
    fake_map.fit_bounds(fake_lat_lon_list.lat_lon_list, max_zoom=7)

    heatmap, streamlit_map = maps.heatmap(map=fake_map, 
                                        lat_lon_lst=fake_lat_lon_list.lat_lon_list, 
                                        sat_name='Planetscope')
    
    assert 'HeatMap' in heatmap.to_json()
    assert 'FitBounds' in heatmap.to_json()
    assert streamlit_map['bounds']['_southWest'] == {'lat': 52.05262899868792, 'lng': 12.225194113938409}
    assert streamlit_map['bounds']['_northEast'] == {'lat': 52.9729321645099, 'lng': 14.588654562576478}

def test_heatmap_exception_lat_lon_incorrect():
    with pytest.raises(TypeError):
        fake_map = folium.Map(location=[52.5200, 13.4050])
        fake_map.fit_bounds(fake_lat_lon_list.lat_lon_list, max_zoom=7)

        maps.heatmap(map=None, lat_lon_list=fake_lat_lon_list.lat_lon_list, name='Planetscope')
        maps.heatmap(map=fake_map, lat_lon_lst=1, sat_name='Planetscope')

def test_images_per_country_map():
    fake_map = folium.Map(location=[52.5200, 13.4050])
 
    fake_df_country = pd.DataFrame({'iso' : ['POL'], 'name': ['Poland'], 'total_images':[19]})

    country_map, streamlit_map= maps.images_per_country_map(
                                map=fake_map, 
                                countries_geojson=fake_country_geojson.country_geojson,
                                df_countries=fake_df_country)

    assert 'Choropleth' in country_map.to_json()
    assert 'GeoJsonTooltip' in country_map.to_json()
    assert 'ColorMap' in country_map.to_json()
    assert streamlit_map['bounds']['_southWest'] == {'lat': 49.020752, 'lng': 14.128613}
    assert streamlit_map['bounds']['_northEast'] == {'lat': 54.838184, 'lng': 24.105762}


def test_image_info_map():
    fake_map = folium.Map(location=[52.5200, 13.4050])
    fake_map.fit_bounds(fake_lat_lon_list.lat_lon_list, max_zoom=7)

    df_images = pd.DataFrame({'id':['6050990_3363309_2022-11-02_2446'],
                                'cloud_cover':[0.0],
                                'pixel_res':[3.125],
                                'time_acquired': ['2022-11-02 10:44:57'],
                                'sat_name':['Planetscope']})
    
    info_map, streamlit_map = maps.image_info_map(
                                map=fake_map,
                                images_geojson=fake_image.image_geojson,
                                df_images=df_images)

    assert 'Choropleth' in info_map.to_json()
    assert 'GeoJsonTooltip' in info_map.to_json()
    assert 'ColorMap' in info_map.to_json()
    assert streamlit_map['bounds']['_southWest'] == {'lat': 52.398654, 'lng': 12.921842}
    assert streamlit_map['bounds']['_northEast'] == {'lat': 52.629318, 'lng': 13.24332}