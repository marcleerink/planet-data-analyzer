import plotly.express as px
import folium
from folium.plugins import HeatMap, HeatMapWithTime
import pandas as pd
import os

def zero_capture_plot(gdf_orders, export_filename, export_directory):
    """Creates a plot of the Zero Capture Count per order and exports it as a html in the export_directory

    Parameters
    ----------
    gdf_orders : GeoDataFrame
        A geopandas GeoDataFrame containing all orders.
    export_filename : str
        Filename
    export_directory: str
        Filesystem path for storing the resulting report and plots
    """

    # Get only orders with zero captures
    gdf_zero_capture = gdf_orders[gdf_orders['zero_capture_count'] > 0]
    
    # create barplot showing only the orders with zero captures
    fig = px.bar(gdf_zero_capture, x="name", y="zero_capture_count")
    fig.update_layout(xaxis_title='Order Name', yaxis_title='Zero Capture Count',title="Zero Capture Count Per Order Location")

    # export
    filename = "".join(["zero_capture_count_plot_", export_filename, ".html"])
    webmap_path = os.path.join(export_directory, filename)
    fig.write_html(webmap_path)

def folium_marker(gdf, map):
        # add markers with name of order location
        for i in range(0,len(gdf)):
            folium.Marker(location=[gdf.iloc[i]['centroid'].y, 
                            gdf.iloc[i]['centroid'].x], 
                            popup=gdf.iloc[i]['name']
                            ).add_to(map)

        return map

def folium_web_map(gdf, export_filename, export_directory, time_interval, start_date, end_date):
    """Creates an html file with a folium web map that contains 4 heatmaps and a Footprints layer.

    Parameters
    ----------
    gdf : GeoDataFrame
        Contains all tasks including centroid coordinates and polygon geometries.
    export_filename : str
        Filename
    export_directory : str
        Directory in which to save the heatmaps and footprints in (must already exist).
    time_interval: str
        Time Interval the heatmap with time will be created on. Options: Quarterly, Monthly, Weekly, Daily 
    """
   
    # create folium map
    my_webmap = folium.Map(location=[50.1155, 8.6842], zoom_start=2, tiles="cartodbpositron")
    
    # create lat_long columns
    gdf['lat'] = gdf['centroid'].y
    gdf['lon'] = gdf['centroid'].x

    # #add markers
    # my_webmap = folium_marker(gdf, my_webmap)

    # create a geometry list from the all tasks
    tasks_centroid_list = [(x,y) for x,y in zip(gdf['centroid'].y ,
                                                 gdf['centroid'].x)]
    
    
    # create a list of tasks and orders
    heat_data_list = [
        [tasks_centroid_list, 'All Tasks'],
    ]

    # instantiate heatmap with different layers
    show_map = True
    for heat_data, title in heat_data_list:
        HeatMap(data=heat_data, name=title, show=show_map).add_to(my_webmap)
        if show_map:
            show_map = False

    #create time interval column in gdf datetime type
    gdf[time_interval] = gdf["properties.acquired"].dt.to_period(time_interval[0]).astype(str)

    # create dataframe with time index to merge gdf with so that intervals without usage are also shown
    period_range = pd.period_range(start=start_date, end=end_date, freq=time_interval[0])
    interval_list = list(period_range.astype(str))
    df_intervals = pd.DataFrame({time_interval: interval_list})

    
    # merge df_agg, df_agg_mean to df_intervals
    gdf = pd.merge(left=df_intervals,
                        right=gdf,
                        how='left',
                        left_on=time_interval,
                        right_on=time_interval)
    
    # loop through each time interval for list of all geometries per time interval
    heat_time_data_list = []
    for t_i in gdf[time_interval].sort_values().unique(): 
        heat_time_data_list.append(gdf.loc[gdf[time_interval] == t_i,
        ['lat', 'lon']]\
        .groupby(['lat', 'lon'])\
        .sum().reset_index().values.tolist())

    # creating a time index with the time-interval
    time_index = []
    for i in gdf[time_interval].unique():
        time_index.append(i)
    
    
    # create heatmap with time
    HeatMapWithTime(data=heat_time_data_list,
                    index=time_index, 
                    name=f"All images{time_interval}", 
                    show=False).add_to(my_webmap)

    # # add footprints to map
    # polygons_gjson = folium.features.GeoJson(gdf['geometry'], name='Footprints Orders', show=True)
    # polygons_gjson.add_to(my_webmap)

    # add layer control for heatmap and footprints layers
    folium.LayerControl().add_to(my_webmap)

    # save the map
    filename = "".join(["heat_maps_", export_filename, ".html"])
    webmap_path = os.path.join(export_directory, filename)
    my_webmap.save(webmap_path)

    
    
