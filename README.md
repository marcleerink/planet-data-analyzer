# Satellite Image Joiner

## Purpose
This is a tool for analyzing satellite image metadata from different constellations. It imports the metadata from [Planets Data API](https://developers.planet.com/docs/apis/data/) for a specified AOI and TOI into PostGIS. This is referenced against geospatial information about countries/cities and various land cover classification data within PostGIS. 
The aggregated and spatial statistics about the imagery are displayed on a Streamlit dashboard.  The dashboards includes various Folium maps displaying where and when images are available from what satellite, including various specifications (Bands / Pixel resolution / Cloud Cover / Area covered) referenced against cities/countries and land cover classification data. 

### Research questions
* Which areas in Germany are most captured by Planet's satellites?
* What is the overlap of area coverage for the different satellite constelations for a choses point in time.
* Where is the highest density of overlap?
* When is the highest denistity of overlap?

Futher down the road:
* What is the percentage of coverage of each land cover class for each image.

## Database setup
```mermaid
classDiagram
direction BT
class alembic_version {
   varchar(32) version_num
}
class asset_types {
   varchar(50) id
}
class cities {
   varchar(50) name
   geometry(point,4326) geom
   integer id
}
class countries {
   varchar(50) name
   geometry(geometry,4326) geom
   varchar(3) iso
}
class item_types {
   varchar(50) sat_id
   varchar(50) id
}
class items_assets {
   varchar(50) item_id
   varchar(50) asset_id
}
class land_cover_classes {
   varchar(50) featureclass
   geometry(geometry,4326) geom
   integer id
}
class sat_images {
   double precision clear_confidence_percent
   double precision cloud_cover
   timestamp time_acquired
   geometry(geometry,4326) geom
   geometry(point,4326) centroid
   varchar(50) sat_id
   varchar(50) item_type_id
   varchar(100) id
}
class satellites {
   varchar(100) name
   double precision pixel_res
   varchar(50) id
}
class spatial_ref_sys {
   varchar(256) auth_name
   integer auth_srid
   varchar(2048) srtext
   varchar(2048) proj4text
   integer srid
}

item_types  -->  satellites : sat_id:id
items_assets  -->  asset_types : asset_id:id
items_assets  -->  item_types : item_id:id
sat_images  -->  item_types : item_type_id:id
sat_images  -->  satellites : sat_id:id
```

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
python -m modules.database.db
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
python importer.py --aoi_file=PATH_TO_GEOJSON
```

Here's an example of how the command looks when passing optional arguments, too:

```
python main.py --aoi_file=PATH_TO_GEOJSON --api_key=API_KEY --start_date=2022-02-01 --end_date=2022-08-25 --cc=0.3
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

### Screenshots

![Heatmap](https://github.com/marcleerink/sat_img_joiner/blob/main/app_screenshots/Screenshot%202022-10-15%20at%2013.30.56.png)
![Choropleth Cloud Cover](https://github.com/marcleerink/sat_img_joiner/blob/main/app_screenshots/Screenshot%202022-10-15%20at%2013.48.20.png)
![Choropleth Images per Country](https://github.com/marcleerink/sat_img_joiner/blob/main/app_screenshots/Screenshot%202022-10-15%20at%2013.50.50.png)

## Future Implementations:
- Add more visualisations from spatial and statistic calculations.
- Add more land cover classifications to reference imagery against.
- Add satellite constellations from other companies.
- Automate the import to PostGIS by deploying it on a server.


Source: "https://developers.planet.com/docs/apis/data/"
"Image © 2022 Planet Labs PBC"