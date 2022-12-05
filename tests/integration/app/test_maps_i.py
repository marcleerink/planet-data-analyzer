import streamlit as st
import folium
import pytest
from app import maps
from tests.resources import fake_country_geojson, fake_image, fake_lat_lon_list

APP_DEV_URL = 'http://localhost:8501'
OUT_PATH = 'tests/resources/html_tests/'

@pytest.fixture
def fake_st_app():
    st.set_page_config(layout='centered')
    return st
    

# def test_heatmap_streamlit(fake_st_app):
    
#     fake_map = folium.Map(location=[52.5200, 13.4050])
#     fake_map.fit_bounds(fake_lat_lon_list.lat_lon_list, max_zoom=7)

#     _, streamlit_map = maps.heatmap(map=fake_map,
#                               lat_lon_lst=fake_lat_lon_list.lat_lon_list,
#                               sat_name='Planetscope')

#     assert streamlit_map ==  ''