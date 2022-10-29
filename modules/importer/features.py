from typing_extensions import assert_type
from shapely.geometry import shape
from sqlalchemy import create_engine
from modules.config import POSTGIS_URL
from sqlalchemy.orm import sessionmaker
from geoalchemy2.shape import from_shape

from modules.database.db import AssetType, ItemType, SatImage, Satellite, get_db_session

class Feature:
    """Represents a single feature imported from Planets Data API"""
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)
        self.id = self.id
        self.sat_id = self.properties["satellite_id"]
        self.time_acquired = self.properties["acquired"]
        self.published = self.properties["published"]
        self.satellite = self.properties["provider"].title()
        self.pixel_res = self.properties["pixel_resolution"]
        self.item_type_id = self.properties["item_type"]
        self.asset_types = self.assets
        self.cloud_cover = self.properties["cloud_cover"] \
            if "cloud_cover" in self.properties else 0
        self.clear_confidence_percent = self.properties["clear_confidence_percent"] \
            if "clear_confidence_percent" in self.properties else 0
        self.geom = shape(self.geometry)
        
        self.quality_category = self.properties["quality_category"] if "quality_category" in self.properties \
            else "Standard"
        if "ground_control" in self.properties:
            self.ground_control = self.properties["ground_control"]
        elif "ground_control_lock" in self.properties:
            self.ground_control = self.properties["ground_control_lock"] == 1
        else:
            self.ground_control = True
        self.instrument = self.properties["instrument"] if "instrument" in self.properties else self.type
        
        self.clear_percent = self.properties["clear_percent"] if "clear_percent" in self.properties else 0
        
        self.cloud_percent = self.properties["cloud_percent"] if "cloud_percent" in self.properties else 0
        self.heavy_haze_percent = self.properties["heavy_haze_percent"] \
            if "heavy_haze_percent" in self.properties else 0
        self.light_haze_percent = self.properties["light_haze_percent"] \
            if "light_haze_percent" in self.properties else 0
        self.shadow_percent = self.properties["shadow_percent"] if "shadow_percent" in self.properties else 0
        self.snow_ice_percent = self.properties["snow_ice_percent"] if "snow_ice_percent" in self.properties else 0
        self.visible_confidence_percent = self.properties["visible_confidence_percent"] \
            if "visible_confidence_percent" in self.properties else 0
        self.visible_percent = self.properties["visible_percent"] if "visible_percent" in self.properties else 0

    def to_dict(self):
        return vars(self)
    
    def _sql_alch_session(self):
        engine = create_engine(POSTGIS_URL, echo=False)
        Session = sessionmaker(bind=engine)
        return Session()

    def _sql_alch_commit(self,model):
        session = self._sql_alch_session()
        session.add(model)
        session.commit()

    def to_satellite_model(self):
        satellite = Satellite(
            id = self.sat_id,
            name = self.satellite)
        self._sql_alch_commit(satellite)

    def to_item_type_model(self):
        item_type = ItemType(
            id = self.item_type_id,
            sat_id = self.sat_id)
        self._sql_alch_commit(item_type)
    
    def to_sat_image_model(self):
        sat_image = SatImage(
                id = self.id, 
                clear_confidence_percent = self.clear_confidence_percent,
                cloud_cover = self.cloud_cover,
                time_acquired = self.time_acquired,
                centroid = from_shape(self.geom, srid=4326),
                geom = from_shape(self.geom, srid=4326),
                sat_id = self.sat_id,
                item_type_id = self.item_type_id
                )
        self._sql_alch_commit(sat_image)
    
    def to_asset_type_model(self):
        for id in self.asset_types:
            asset_type = AssetType(
                id = id
            )
            self._sql_alch_commit(asset_type)



def postgis_import(features_list):
    for i in features_list:
        
        feature= Feature(i)
        
        feature.to_satellite_model()
        feature.to_item_type_model()
        feature.to_sat_image_model()
        feature.to_asset_type_model()


