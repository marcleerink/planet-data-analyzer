import pytest
import streamlit as st
from datetime import datetime, timedelta

from modules.app import filters

def test_display_sat_name_filter():
    fake_sat_name_list = ['Planetscope', 'Skysat']
    fake_radio_filter = st.sidebar.radio('dummy', fake_sat_name_list)
    sat_name_filter = filters.display_sat_name_filter(fake_sat_name_list)

    assert sat_name_filter == fake_radio_filter

def test_display_time_filter():
    
    start_date, end_date = filters.display_time_filter()

    assert start_date == st.sidebar.date_input('Start Date', datetime.utcnow() - timedelta(days=7))
    assert end_date == st.sidebar.date_input('End Date', datetime.utcnow())


def test_display_cloud_cover_filter():

    cloud_filter = filters.display_cloud_cover_filter()

    assert cloud_filter == st.sidebar.slider('Cloud Cover Threshold', 0.0, 1.0, step=0.1, value=1.0)