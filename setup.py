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
                        'geopandas',
                        'openpyxl',
                        'pandas',
                        'plotly',
                        'requests',
                        'retrying',
                        'Shapely'],
    entry_points = {
    'console_scripts': ['tasking-reporter=reporter.main:create_report']
    },    
 
)