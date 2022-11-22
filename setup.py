from setuptools import setup, find_packages

setup(
    name='planet-data-analyzer',  
    version='0.3',
    description='Tool for analyzing satellite image metadata from Planet ',
    url='https://github.com/marcleerink/planet_data_analyzer',
    author='Marc Leerink',
    author_email='marc.leerink@code.berlin',
    license='Planet-Labs',
    python_requires='>=3.6',
    packages=['planet-data-analyzer'],
    install_requires=['folium',
                    'GeoAlchemy2',
                    'geojson'
                    'geopandas'
                    'pandas'
                    'Pillow'
                    'plotly'
                    'psycopg2'
                    'pytest'
                    'pytest-cov'
                    'pytest-xdist'
                    'python-dotenv'
                    'SQLAlchemy'
                    'SQLAlchemy-Utils'
                    'streamlit==1.14.0'
                    'streamlit-folium'
                    'vcrpy'],  
 
)