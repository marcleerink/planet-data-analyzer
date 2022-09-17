import json

def geojson_import(aoi_file):
    with open(aoi_file) as f:
        geometry = json.load(f)
    return geometry['features'][0]['geometry']
