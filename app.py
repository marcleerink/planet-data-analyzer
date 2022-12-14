import streamlit as st


from app import maps, plots, query, filters
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from config import POSTGIS_URL

APP_TITLE = "Planets Satellite Imagery"
APP_SUB_TITLE = 'Source: Planet  https://developers.planet.com/docs/apis/data/'


@st.experimental_singleton
def app_db_session():
    """Database session to use in app with streamlit caching decorator"""
    engine = create_engine(POSTGIS_URL, echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


def main():

    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)

    session = app_db_session()

    # small queries for filters
    sat_name_list = query.query_distinct_satellite_names(session)
    country_list = query.query_all_countries(session)

    # add sidebar with filters
    sat_names = filters.display_sat_name_filter(sat_name_list)
    start_date, end_date = filters.display_time_filter()
    time_interval = filters.display_time_interval_filter()
    cloud_cover = filters.display_cloud_cover_filter()
    country_name = filters.display_country_filter(country_list=country_list)

    # convert minute to proper offset alias
    if time_interval == 'Minute':
        time_interval = 'T'

    # query postgis
    gdf_images = query.query_sat_images_with_filter(_session=session,
                                                    sat_names=sat_names,
                                                    cloud_cover=cloud_cover,
                                                    start_date=start_date,
                                                    end_date=end_date,
                                                    country_name=country_name)
    lat_lon_lst = query.get_lat_lon_from_images(gdf_images)

    gdf_cities = query.query_cities_with_filters(_session=session,
                                                 sat_names=sat_names,
                                                 cloud_cover=cloud_cover,
                                                 start_date=start_date,
                                                 end_date=end_date,
                                                 country_name=country_name)

    gdf_land_cover = query.query_land_cover_classes_with_filters(_session=session,
                                                                 sat_names=sat_names,
                                                                 cloud_cover=cloud_cover,
                                                                 start_date=start_date,
                                                                 end_date=end_date,
                                                                 country_name=country_name)
    gdf_land_cover_coverage = query.query_land_cover_classes_with_filters_image_coverage(_session=session,
                                                                                         sat_names=sat_names,
                                                                                         cloud_cover=cloud_cover,
                                                                                         start_date=start_date,
                                                                                         end_date=end_date,
                                                                                         country_name=country_name)
    gdf_land_cover_dissolved = query.query_land_cover_geom_dissolved(_session=session,
                                                                     country_name=country_name)
    if len(gdf_images.index) == 0:
        st.write('No Images available for selected filters')
    else:
        st.subheader(
            f"What is the amount of Planets satellite imagery in {country_name} from {start_date} \
                to {end_date} for {', '.join(sat_names)} satellites?")
        st.write('Total Satellite Images: {}'.format(len(gdf_images.index)))
        plots.plot_images_per_satellite(df_images=gdf_images)

        st.subheader(
            f"Which areas in {country_name} are most captured by {', '.join(sat_names)} satellites\
                 from {start_date} to {end_date}?")
        maps.heatmap(map=maps.create_basemap(lat_lon_list=lat_lon_lst),
                     gdf=gdf_images,
                     lat_lon_lst=lat_lon_lst,
                     sat_name=sat_names)

        st.subheader(
            f"When are areas in {country_name} most captured by {', '.join(sat_names)} satellites\
                 from {start_date} to {end_date}?")
        maps.heatmap_time_series(map=maps.create_basemap(lat_lon_list=lat_lon_lst),
                                 gdf=gdf_images,
                                 sat_name=sat_names,
                                 start_date=start_date,
                                 end_date=end_date,
                                 time_interval=time_interval)
        st.write(
            f"Total images for each major city in {country_name} with 30km buffer radius \
                from {start_date} to {end_date} for {', '.join(sat_names)} satellites")

        st.caption('This also displays cities near the borders due to the buffer polygon around the city\
             and the geometry of the satellite image which may cross the border')

        if len(gdf_cities.index) == 0:
            st.write('No Images near cities in selected country')
        else:
            maps.images_per_city(map=maps.create_basemap(lat_lon_list=lat_lon_lst),
                                 gdf_cities=gdf_cities)

        st.subheader(
            f"What is the amount of imagery for each land cover classification in \
                {country_name} from {start_date} to {end_date} for {', '.join(sat_names)} satellites?")

        plots.plot_images_per_land_cover_class(gdf_land_cover=gdf_land_cover)

        st.caption('This displays all land cover class geometries that are covered by Planets satellite imagery and specified filters,\
                    it does not display land cover geometries that are not covered by imagery with the specified filters')

        map = maps.images_per_land_cover_class(map=maps.create_basemap(lat_lon_list=lat_lon_lst),
                                               gdf_land_cover=gdf_land_cover)

        st.subheader(
            f"What is the percentage of coverage for each land cover classification \
                in {country_name} from {start_date} to {end_date} for {', '.join(sat_names)} satellites?")

        plots.plot_land_cover_image_coverage(gdf_land_cover_coverage)

        st.subheader(
            f"Where is the coverage of each land cover classification {country_name}\
                 from {start_date} to {end_date} for {', '.join(sat_names)} satellites?")

        maps.land_cover_image_coverage(map=maps.create_basemap(
            lat_lon_list=lat_lon_lst),
            gdf=gdf_land_cover_coverage,
            gdf_land_cover_dissolved=gdf_land_cover_dissolved)

        st.subheader(
            f"Which land cover classifications are covered for each individual satellite image in {country_name} from {start_date} to {end_date} for {', '.join(sat_names)}?")
       
        maps.image_info_map(map=maps.create_basemap(lat_lon_list=lat_lon_lst),
                            gdf_images=gdf_images)


if __name__ == '__main__':
    main()
