import pytest
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape

from modules.importer.clients.geojson_xyz import GeojsonXYZClient, CityFeature, CountryFeature, LandCoverClassFeature

@pytest.fixture
def fake_countries():
        return gpd.read_file('tests/resources/fake_countries.geojson').reset_index(names='id')\
                                                               .to_dict(orient='records')

@pytest.fixture
def fake_cities():
    return gpd.read_file('tests/resources/fake_cities.geojson').reset_index(names='id')\
                                                    .to_dict(orient='records')

@pytest.fixture
def fake_land_cover():
        rivers_lakes = gpd.read_file('tests/resources/fake_rivers_lakes.geojson')
        urban_areas = gpd.read_file('tests/resources/fake_urban_areas.geojson')
        gdf_list = [rivers_lakes, urban_areas]

        return pd.concat(gdf_list, axis=0, ignore_index=True).reset_index(names='id')\
                                                            .to_dict(orient='records')

def test_CountryFeature(fake_countries):
    """test if all metadata from multiple features is converted correctly"""
    
    fake_feature_list = [CountryFeature(i) for i in fake_countries]
    
    fake_iso_list = [i.iso for i in fake_feature_list]
    fake_name_list = [i.name for i in fake_feature_list]
    fake_geom_list = [i.geom for i in fake_feature_list]

    assert len(fake_countries) == len(fake_feature_list)
    assert fake_iso_list == [str(i["adm0_a3"]) for i in fake_countries]
    assert fake_name_list == [str(i["name"]) for i in fake_countries]
    assert fake_geom_list == [shape(i["geometry"]) for i in fake_countries]


def test_CityFeature(fake_cities):
    """test if all metadata from multiple features is converted correctly"""
    
    fake_feature_list = [CityFeature(i) for i in fake_cities]

    fake_id_list = [i.id for i in fake_feature_list]
    fake_name_list = [i.name for i in fake_feature_list]
    fake_geom_list = [i.geom for i in fake_feature_list]

    assert len(fake_cities) == len(fake_feature_list)
    assert fake_id_list == [int(i["id"]) for i in fake_cities]
    assert fake_name_list == [str(i["name"]) for i in fake_cities]
    assert fake_geom_list == [shape(i["geometry"]) for i in fake_cities]
    

def test_LandCoverClassFeature(fake_land_cover):
    """test if all metadata from multiple features is converted correctly"""
    fake_feature_list = [LandCoverClassFeature(i) for i in fake_land_cover]

    fake_id_list = [i.id for i in fake_feature_list]
    fake_feat_list = [i.featureclass for i in fake_feature_list]
    fake_geom_list = [i.geom for i in fake_feature_list]

    assert len(fake_land_cover) == len(fake_feature_list)
    assert fake_id_list == [int(i["id"]) for i in fake_land_cover]
    assert fake_feat_list == [str(i["featureclass"]) for i in fake_land_cover]
    assert fake_geom_list == [shape(i["geometry"]) for i in fake_land_cover]

