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


    cities = query.query_cities_with_filters(_session=session,
                                            sat_names=sat_names,
                                            cloud_cover=cloud_cover,
                                            start_date=start_date,
                                            end_date=end_date,
                                            country_name=country_name)
    cities_geojson = query.create_cities_geojson(_cities=cities)
    df_cities = query.create_cities_df(_cities=cities)
    

    land_cover_classes = query.query_land_cover_classes_with_filters(_session=session,
                                                                sat_names=sat_names,
                                                                cloud_cover=cloud_cover,
                                                                start_date=start_date,
                                                                end_date=end_date,
                                                                country_name=country_name)
    
    gdf_land_cover = query.create_land_cover_gpd(land_cover_classes)
    
    if len(df_images.index) == 0:
        st.write('No Images available for selected filters')
    else:
        st.subheader("What is the amount of Planets satellite imagery in {} for a chosen timeframe?".format(country_name))
        st.write('Total Satellite Images: {}'.format(len(images)))
        plots.plot_images_per_satellite(df_images=df_images)
        
        st.subheader("Which areas in {} are most captured by Planet's satellites?".format(country_name))
        maps.heatmap(map=maps.create_basemap(lat_lon_list=lat_lon_lst),
                    lat_lon_lst=lat_lon_lst, 
                    sat_name=sat_names)
        
        st.write('Total images for each major city in {} with 30km buffer radius'.format(country_name))
        st.caption('This also displays cities near the borders due to the buffer polygon around the city and the geometry of the satellite image which may cross the border')
        maps.images_per_city(map=maps.create_basemap(lat_lon_list=lat_lon_lst),
                            cities_geojson=cities_geojson,
                            df_cities=df_cities)
        
        st.subheader("What is the imagery coverage for each land cover classification?")
        
        plots.plot_images_per_land_cover_class(df_images=df_images)

        st.caption('This displays all land cover class geometries that are covered by Planets satellite imagegery and specified filters,\
                    it does not display land cover geometries that are not covered by imagery with the specified filters')

        maps.images_per_land_cover_class(map=maps.create_basemap(lat_lon_list=lat_lon_lst),
                                        gdf_land_cover=gdf_land_cover)

        st.subheader('Which land cover classifications are covered for each individual satellite image?')
        maps.image_info_map(map=maps.create_basemap(lat_lon_list=lat_lon_lst), 
                            images_geojson=images_geojson, 
                            df_images=df_images)

        
if __name__=='__main__':
    main()

