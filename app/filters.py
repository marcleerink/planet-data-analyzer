import streamlit as st
from datetime import datetime, timedelta


def _display_sat_name_filter(sat_name_list: list[str]) -> list[str]:
    return st.sidebar.radio('Satellite Providers',sat_name_list)

def display_sat_name_filter(sat_name_list: list[str]) -> list[str]:
    return st.sidebar.multiselect('Satellite Providers',sat_name_list, default=sat_name_list)

def display_time_filter() -> tuple[datetime, datetime]:
    start_date = st.sidebar.date_input('Start Date', datetime.utcnow() - timedelta(days=1))
    end_date = st.sidebar.date_input('End Date', datetime.utcnow())
    return start_date, end_date

def display_cloud_cover_filter() -> float:
    return st.sidebar.slider('Cloud Cover Threshold', 0.0, 1.0, step=0.1, value=1.0)

def display_country_filter(country_name_list: list[str]) -> str:
    default_index = country_name_list.index('Germany')
    return st.sidebar.selectbox('Country', country_name_list, index=default_index)