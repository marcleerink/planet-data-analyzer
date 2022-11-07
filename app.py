import streamlit as st

from modules.database import db
from modules.app import maps
from modules.app import query
from modules.app import filters

APP_TITLE = "Satellite Image Joins"
APP_SUB_TITLE = 'Source: Planet'

def main():
    st.set_page_config(page_title=APP_TITLE, layout='centered')
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)
    
    session = db.get_db_session()
    engine = db.get_db_engine()

    # add sidebar with filters
    sat_name_list = query.query_distinct_satellite_names(session)
    sat_names = filters.display_sat_name_filter(sat_name_list)
    start_date, end_date = filters.display_time_filter()
    cloud_cover = filters.display_cloud_cover_filter()
    
    # query postgis
    images = query.query_sat_images_with_filter(_session=session,
                                            sat_names=sat_names, 
                                            cloud_cover=cloud_cover, 
                                            start_date=start_date, 
                                            end_date=end_date)
    
    
    images_geojson = query.create_images_geojson(images)
    df_images = query.create_images_df(images)
    
    countries = query.query_countries_with_filters(session,
                                            sat_names,
                                            cloud_cover, 
                                            start_date, 
                                            end_date)

    countries_geojson = query.create_country_geojson(countries)
    df_countries = query.create_countries_df(countries)
                                                                        
    if len(df_images.index) == 0:
        st.write('No Images available for selected filters')
    else:
        st.write('Total Satellite Images: {}'.format(len(df_images.index)))
        
        lat_lon_lst = maps.query_lat_lon_sat_images(images)

        maps.heatmap(map=maps.create_basemap(lat_lon_list=lat_lon_lst),
                    lat_lon_lst=lat_lon_lst, 
                    sat_name=sat_names)
        
        maps.image_info_map(map=maps.create_basemap(lat_lon_list=lat_lon_lst), 
                            images_geojson=images_geojson, 
                            df_images=df_images)

        maps.images_per_country_map(map=maps.create_basemap(zoom=4),
                                    countries_geojson=countries_geojson, 
                                    df_countries=df_countries)

if __name__=='__main__':
    main()

