import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

from modules.app.query import get_distinct_satellite_names

def display_sat_name_filter(session):
    satellites = get_distinct_satellite_names(session)
    sat_name_list = [sat.name for sat in satellites]
    return st.sidebar.radio('Satellite Providers',sat_name_list)

def display_time_filter():
    start_date = st.sidebar.date_input('Start Date', datetime.utcnow() - timedelta(days=7))
    end_date = st.sidebar.date_input('End_date', datetime.utcnow())
    
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    return start_date, end_date

def display_cloud_cover_filter():
    return st.sidebar.slider('Cloud Cover Threshold', 0.0, 1.0, step=0.1, value=1.0)
    