import streamlit as st

from database import db
from app import maps, plots, query, filters

APP_TITLE = "Satellite Image Joins"
APP_SUB_TITLE = 'Source: Planet  https://developers.planet.com/docs/apis/data/'

def main():
    st.set_page_config(page_title=APP_TITLE, layout='centered')
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)

    session = db.get_db_session()

    #small queries for filters
    sat_name_list = query.query_distinct_satellite_names(session)
    country_list = query.query_all_countries_name(session)

    # add sidebar with filters
    sat_names = filters.display_sat_name_filter(sat_name_list)
    start_date, end_date = filters.display_time_filter()
    cloud_cover = filters.display_cloud_cover_filter()
    country_name = filters.display_country_filter(country_name_list=country_list)
    
    # query postgis
    images = query.query_sat_images_with_filter(_session=session,
                                            sat_names=sat_names, 
                                            cloud_cover=cloud_cover, 
                                            start_date=start_date, 
                                            end_date=end_date,
                                            country_name=country_name)

    lat_lon_lst = query.query_lat_lon_from_images(images)
    images_geojson = query.create_images_geojson(images)
    df_images = query.create_images_df(images)


    # cities = query.query_cities_with_filters(_session=session,
    #                                         sat_names=sat_names,
    #                                         cloud_cover=cloud_cover,
    #                                         start_date=start_date,
    #                                         end_date=end_date,
    #                                         country_name=country_name)
    # cities_geojson = query.create_cities_geojson(_cities=cities)
    # df_cities = query.create_cities_df(_cities=cities)
    

    if len(df_images.index) == 0:
        st.write('No Images available for selected filters')
    else:
        st.subheader("What is the total amount of satellite images in {} for a chosen timeframe?".format(country_name))
        st.write('Total Satellite Images: {}'.format(len(images)))
        plots.plot_images_per_satellite(df_images=df_images)
        
        st.subheader("Which areas in {} are most captured by Planet's satellites?".format(country_name))
        maps.heatmap(map=maps.create_basemap(lat_lon_list=lat_lon_lst),
                    lat_lon_lst=lat_lon_lst, 
                    sat_name=sat_names)
        
        st.subheader("What is the overlap of area coverage for the different satellite constelations for a choses timeframe?")

        st.subheader("What is the coverage of each land cover class for each image?")
        # maps.image_info_map(map=maps.create_basemap(lat_lon_list=lat_lon_lst), 
        #                     images_geojson=images_geojson, 
        #                     df_images=df_images)

        # maps.images_per_city(map=maps.create_basemap(lat_lon_list=lat_lon_lst),
        #                     cities_geojson=cities_geojson,
        #                     df_cities=df_cities)

if __name__=='__main__':
    main()

