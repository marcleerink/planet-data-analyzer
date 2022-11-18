import plotly.graph_objects as go
import plotly.express as px

import pandas as pd
import streamlit as st

def plot_images_per_satellite(df_images: pd.DataFrame) -> st.plotly_chart:

    # create fig to plot on
    fig = go.Figure()
   
    for sat_name in df_images['sat_name'].unique():
        df = df_images[df_images['sat_name'] == sat_name]
        grouped_sat_df = df.groupby('sat_name').count()
    
        fig.add_trace(go.Bar(x=grouped_sat_df.index, y=grouped_sat_df['id'], name=sat_name))
    
    
    fig.update_layout(title='Total amount of satellite images per satellite',
                        xaxis_title='Satellite',
                        yaxis_title='Amount of Satellite Images')
    return fig, st.plotly_chart(fig)

def plot_images_per_land_cover_class(df_images: pd.DataFrame) -> st.plotly_chart:

    # create fig to plot on
    fig = go.Figure()
    
    #explode land cover classes lists to do proper groupby
    df_ex_images = df_images.explode('land_cover_class')
    
    for featureclass in df_ex_images['land_cover_class'].unique():
        df = df_ex_images[df_ex_images['land_cover_class'] == featureclass]
        
        grouped_land_cover = df.groupby('land_cover_class').count()
    
        fig.add_trace(go.Bar(x=grouped_land_cover.index, y=grouped_land_cover['id'], name=featureclass))

    fig.update_layout(title='Total amount of satellite images per Land Cover Classification',
                        xaxis_title='Land Cover Classification',
                        yaxis_title='Amount of Satellite Images')

    return fig, st.plotly_chart(fig)