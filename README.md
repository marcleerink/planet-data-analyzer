# Satellite Image Joiner

## Purpose
This is a tool for analyzing satellite image metadata from different constellations. It imports the metadata from [Planets Data API](https://developers.planet.com/docs/apis/data/) for a specified AOI and TOI into PostGIS. This is referenced against geospatial information about countries/cities and various land cover classification data within PostGIS. 
The aggregated and spatial statistics about the imagery are displayed on a Streamlit dashboard.  The dashboards includes various Folium maps displaying where and when images are available from what satellite, including various specifications (Bands / Pixel resolution / Cloud Cover) referenced against cities/countries and land cover classification data. 


## Dependencies

* Python 3
* Python packages:

      pip3 install -r requirements.txt

* Postgres with [PostGIS plugin installed](https://postgis.net/install/) and an active database.

* .env file containing the Postgres connection url: 
```POSTGIS_URL='postgresql://USERNAME:PASSWORD@localhost:5432/DATABASE_NAME'```

* [Planet API Key](https://www.planet.com/account/#/user-settings) 
You can create an account and access the Data API for free.

## Usage

* The importer.py file should first be run.
* The importer script accepts an API Key set as environmental variable (PL_API_KEY) or as an argument. 

### Run the importer.py
#### Arguments 
* --aoi_file -  Path to geojson file containing AOIs
* --api_key - Planet's API key
* --start_date - Optional. Start date of the time interval to create a report for, in ISO (YYYY-MM-DD) format.(gte), Defaults to yesterday.
* --end_date - Optional. End date of the time interval in ISO (YYYY-MM-DD) format.(lte). Defaults to today.
* --cc - Optional. Cloud cover value to be used for filtering. Defaults to 1.0"

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

![Heatmap](http://url/to/img.png)
![Choropleth Cloud Cover](http://url/to/img.png)
![Choropleth Images per Country](http://url/to/img.png)

## Future Implementations:
- Add more visualisations from spatial and statistic calculations.
- Add more land cover classifications to reference imagery against.
- Add satellite constellations from other companies.
- Automate the import to PostGIS by deploying it on a server.

