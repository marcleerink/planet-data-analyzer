import streamlit as st

from modules.database.db import get_db_session
from modules.app.maps import heatmap, image_info_map, images_per_country_map
from modules.app.query import get_countries_with_filters, get_images_with_filter
from modules.app.filters import display_cloud_cover_filter, display_sat_name_filter, display_time_filter

APP_TITLE = "Satellite Image Joins"
APP_SUB_TITLE = 'Source: Planet'

def main():
    # st.set_page_config(page_title=APP_TITLE, layout='wide')
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)
    
    session = get_db_session()

    # add sidebar with filters
    sat_names = display_sat_name_filter(session)
    start_date, end_date = display_time_filter()
    cloud_cover = display_cloud_cover_filter()
    
    # get data from postgis
    images, images_geojson, df_images = get_images_with_filter(session,
                                                            sat_names, 
                                                            cloud_cover, 
                                                            start_date, 
                                                            end_date)

    countries, countries_geojson, df_countries = get_countries_with_filters(session,
                                                                            sat_names,
                                                                            cloud_cover, 
                                                                            start_date, 
                                                                            end_date)
                                                                        
    if len(images) == 0:
        st.write('No Images available for selected filters')
    else:
        st.write('Total Satellite Images: {}'.format(len(images)))
        heatmap(images, sat_names)
        image_info_map(images, images_geojson, df_images)
        images_per_country_map(countries_geojson, df_countries)

if __name__=='__main__':
    main()

