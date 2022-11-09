import streamlit as st
from datetime import datetime, timedelta


def display_sat_name_filter(sat_name_list):
    return st.sidebar.radio('Satellite Providers',sat_name_list)

def display_time_filter():
    start_date = st.sidebar.date_input('Start Date', datetime.utcnow() - timedelta(days=7))
    end_date = st.sidebar.date_input('End Date', datetime.utcnow())
    return start_date, end_date

def display_cloud_cover_filter():
    return st.sidebar.slider('Cloud Cover Threshold', 0.0, 1.0, step=0.1, value=1.0)
    