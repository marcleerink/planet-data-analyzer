import streamlit as st
from datetime import datetime, timedelta
import geopandas as gpd
import pandas as pd
from database.db import Country

def display_sat_name_filter(sat_name_list: list[str]) -> list[str]:
    return st.sidebar.multiselect('Satellite Providers', sat_name_list, default=sat_name_list)


def display_time_filter() -> tuple[datetime, datetime]:
    start_date = st.sidebar.date_input(
        'Start Date', datetime.utcnow() - timedelta(days=1))
    end_date = st.sidebar.date_input('End Date', datetime.utcnow())
    return start_date, end_date


def display_cloud_cover_filter() -> float:
    return st.sidebar.slider('Cloud Cover Threshold', 0.0, 1.0, step=0.1, value=1.0)


def display_country_filter(country_list: list[Country]) -> str:
    country_names = [i.name for i in country_list]
    default_index = country_names.index('Germany')
    return st.sidebar.selectbox('Country', country_names, index=default_index)


def filter_gdf_images(
    gdf_images: gpd.GeoDataFrame, start_date: datetime, end_date: datetime, sat_names: list[str], cloud_cover: float) -> gpd.GeoDataFrame:
    """filters the dataframe with set up streamlit filters"""
    
    gdf_images = gdf_images[gdf_images['time_acquired'] >= pd.to_datetime(start_date)]
    gdf_images = gdf_images[gdf_images['time_acquired'] <= pd.to_datetime(end_date)]
    gdf_images = gdf_images[gdf_images['sat_name'].isin(sat_names)]
    return gdf_images[gdf_images['cloud_cover'] <= cloud_cover]