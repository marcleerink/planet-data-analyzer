from typing_extensions import assert_type
from shapely.geometry import shape
from sqlalchemy import create_engine
from modules.config import POSTGIS_URL
from sqlalchemy.orm import sessionmaker
from geoalchemy2.shape import from_shape

from modules.database.db import AssetType, ItemType, LandCoverClass, SatImage, Satellite

class ImageDataFeature:
    """
    Represents a image feature its metadata. 
    Imported from Planets Data API.
    """
    def __init__(self, image_feature):
        """
        :param dict image_feature:
            A dictionary containing metadata of a image from the Data API.
        """
        for key, value in image_feature.items():
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
            name = self.satellite,
            pixel_res = self.pixel_res)
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
                id = id)
            self._sql_alch_commit(asset_type)


class LandCoverClassFeature:
    """
    Represents a landcoverclass feature its metadata.
    Imported from Planets Data API.
    """
    def __init__(self, land_cover_feature):
        """
        :param dict land_cover_feature:
            A dictionary containing metadata of a land cover class feature.
        """
        for key, value in land_cover_feature.items():
            setattr(self, key, value)
        self.id = self.id
        self.featureclass = self.featureclass
        self.geom = shape(self.geom)

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

    def to_land_cover_model(self):
        land_cover_class = LandCoverClass(
                id = self.id, 
                featureclass = self.featureclass,
                geom = from_shape(self.geom, srid=4326),
                )
        self._sql_alch_commit(land_cover_class)





