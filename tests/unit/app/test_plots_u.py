import pandas as pd
from app import plots
import plotly.graph_objects as go


def test_plot_images_per_satellite():

    fake_df_images = pd.DataFrame({'id':['6050990_3363309_2022-11-02_2446'],
                                'cloud_cover':[0.0],
                                'pixel_res':[3.125],
                                'time_acquired': ['2022-11-02 10:44:57'],
                                'sat_name':['Planetscope']})
    fig, st_fig = plots.plot_images_per_satellite(fake_df_images)
    

    assert fig.__dict__['_data_objs'][0]['x'][0] == 'Planetscope'
    assert fig.__dict__['_data_objs'][0]['y'][0] == 1


def test_plot_image_per_land_cover_class():
    fake_df_images = pd.DataFrame({'id':['6050990_3363309_2022-11-02_2446'],
                                'cloud_cover':[0.0],
                                'pixel_res':[3.125],
                                'time_acquired': ['2022-11-02 10:44:57'],
                                'sat_name':['Planetscope'],
                                'land_cover_class': [['Urban Area', 'River']]})

    fig,st_fig = plots.plot_images_per_land_cover_class(fake_df_images)

    assert fig.__dict__['_data_objs'][0]['x'][0] == 'Urban Area'
    assert fig.__dict__['_data_objs'][1]['x'][0] == 'River'