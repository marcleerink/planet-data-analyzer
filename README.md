# planet-data-analyzer

## Purpose
This is a tool for analyzing satellite image metadata from different constellations. It imports the metadata from [Planets Data API](https://developers.planet.com/docs/apis/data/) for a specified AOI and TOI into PostGIS. This is referenced against geospatial information about countries/cities and various land cover classification data within PostGIS. The land cover classification data is imported from http://geojson.xyz/ naturalearth API.
The aggregated and spatial statistics about the imagery are displayed on a Streamlit dashboard.  The dashboards includes Plotly Graphs with general statistics and Folium maps displaying where and when images are available from what satellite, including various specifications (Bands / Pixel resolution / Cloud Cover / Area covered) referenced against cities/countries and land cover classification data. 

### Research questions
* What is the amount of Planets satellite imagery in a specified country for a chosen timeframe?
* Which areas in a specified country are most captured by Planet's satellites?
* What is the amount of satellite images per city??
* What is the amount of Planets satellite imagery for each land cover classification?
* Which land cover classifications are covered for each individual satellite image?

## Dependencies

* Python 3
* Python packages:

      pip3 install -r requirements.txt

* .env file containing:
```DB_NAME=YOUR_DB_NAME```
```DB_PW=YOUR_DB_PASS```
```DB_USER=YOUR_DB_USER```
```DB_HOST=YOUR_DB_HOST```
```DB_PORT=YOUR DB_PORT```


* [Planet API Key](https://www.planet.com/account/#/user-settings) 
You can create an account and access the Data API for free.

## Usage

### Setup the database
The database should first be setup.
Run the modules/database/db.py file to create a Postgres database with the PostGIS extension installed. 
This will also create all necessary tables.
```
python -m database.db
```

### Run the importer.py
Secondly, the importer.py file should be run.

#### Arguments 
* --aoi_file -  Path to geojson file containing AOIs
* --api_key - Planet's API key
* --start_date - Optional. Start date of the time interval, in ISO (YYYY-MM-DD) format.(gte), Defaults to yesterday.
* --end_date - Optional. End date of the time interval in ISO (YYYY-MM-DD) format.(lte). Defaults to today.
* --cc - Optional. Cloud cover value to be used for filtering (0.0 - 1.0). Defaults to 1.0"

To run the importer from your command line with only the required arguments, you need to pass the following arguments:

```
python importer.py --aoi_file=data/germany_bb.geojson
```

Here's an example of how the command looks when passing optional arguments, too:

```
python main.py --aoi_file=data/germany_bb.geojson --api_key=API_KEY --start_date=2022-02-01 --end_date=2022-08-25 --cc=0.3
```

To get a full description of all the arguments or further help with the script:

```
python importer.py --help
```

### Run the app.py
After the data has been importer the app.py can be started:

```
streamlit run app.py
```

## Database Setup

![ER-Diagram](https://github.com/marcleerink/sat_img_joiner/blob/main/data/er_diagram.jpg)

## App Screenshots
![Landingpage](https://github.com/marcleerink/sat_img_joiner/blob/main/data/app_screenshots/landing_page.png)
![Total Images Plot](https://github.com/marcleerink/sat_img_joiner/blob/main/data/app_screenshots/total_images_plotly.png)
![Heatmap](https://github.com/marcleerink/sat_img_joiner/blob/main/data/app_screenshots/heatmap_images.png)
![Cities Choropleth Map](https://github.com/marcleerink/sat_img_joiner/blob/main/data/app_screenshots/cities_map.png)
![Land Cover Plot](https://github.com/marcleerink/sat_img_joiner/blob/main/data/app_screenshots/land_cover_plot.png)
![Land Cover Choropleth Map](https://github.com/marcleerink/sat_img_joiner/blob/main/data/app_screenshots/land_cover_ch_map.png)
![Images Choropleth Map](https://github.com/marcleerink/sat_img_joiner/blob/main/data/app_screenshots/images_ch_map.png)

## Future Implementations:
- Add more visualisations from spatial and statistic calculations. (e.g. coverage percentage of country/city/land cover classification for each satellite)
- Add more land cover classifications to reference imagery against.
- Add satellite constellations from other companies.
- Automate the import to PostGIS by deploying it on a server.



Source: https://developers.planet.com/docs/apis/data/

Image ?? 2022 Planet Labs PBC