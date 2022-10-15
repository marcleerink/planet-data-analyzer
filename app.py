import streamlit as st
from sqlalchemy import select, func
import pandas as pd
from datetime import datetime, timedelta

from modules.database.db import Satellite, SESSION
from modules.app.maps import heatmap, image_info_map, images_per_country_map
from modules.app.query import get_countries_with_filters, get_images_with_filter

APP_TITLE = "Satellite Image Joins"
APP_SUB_TITLE = 'Source: Planet'
session = SESSION()

def display_sat_name_filter(session):
    satellites = session.query(Satellite.name).distinct()
    sat_name_list = [sat.name for sat in satellites]
    return st.sidebar.radio('Satellite Providers',sat_name_list)

def display_time_filter():
    start_date = st.sidebar.date_input('Start Date', datetime.utcnow() - timedelta(days=7))
    end_date = st.sidebar.date_input('End_date', datetime.utcnow())

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    return start_date, end_date

def display_cloud_cover_filter():
    return st.sidebar.slider('Cloud Cover Threshold', 0.0, 1.0, step=0.1)
    
def main():
    st.set_page_config(page_title=APP_TITLE, layout='wide')
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)
    
    # add sidebar with filters
    sat_names = display_sat_name_filter(session)
    start_date, end_date = display_time_filter()
    cloud_cover = display_cloud_cover_filter()
    
    # get data
    images = get_images_with_filter(session,
                                    sat_names, 
                                    cloud_cover, 
                                    start_date, 
                                    end_date)

    countries = get_countries_with_filters(session,sat_names,cloud_cover, start_date, end_date)
    
    if len(images) == 0:
        st.write('No Images available for selected filters')
    else:
        st.write('Total Satellite Images: {}'.format(len(images)))
        heatmap(images, sat_names)
        image_info_map(images)
        images_per_country_map(countries)

if __name__=='__main__':
    main()

