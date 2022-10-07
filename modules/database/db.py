from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref, column_property
from sqlalchemy import create_engine, Table, Column, Integer, Float, String,\
    DateTime, ForeignKey, select, func
from geoalchemy2 import Geometry, functions
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import insert
from geoalchemy2.shape import from_shape, to_shape

from modules.config import POSTGIS_URL



ENGINE = create_engine(POSTGIS_URL, echo=False)
BASE = declarative_base()
SESSION = sessionmaker(bind=ENGINE)
session = SESSION()

class CentroidFromPolygon(TypeDecorator):
    '''Insert the centroid points on each Polygon insert'''
    impl = Geometry
    cache_ok = True

    def bind_expression(self, bindvalue):
        return functions.ST_Centroid(self.impl.bind_expression(bindvalue))

class Centroid(BASE):
    __tablename__='centroid'
    id = Column(Integer, primary_key=True)
    centroid = Column(CentroidFromPolygon(srid=4326, geometry_type='POINT'))

class Satellite(BASE):
    __tablename__='satellites'
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    pixel_res = Column(Float)
    
    sat_images = relationship('SatImage', 
                            backref='satellite')
    items = relationship('ItemType', 
                        backref='satellites',)

class SatImage(BASE):
    __tablename__='sat_images'
    id = Column(String(100), primary_key=True)
    clear_confidence_percent = Column(Float)
    cloud_cover = Column(Float, nullable=False)
    pixel_res = Column(Float, nullable=False)
    time_acquired = Column(DateTime, nullable=False)
    geom = Column(Geometry(geometry_type='Polygon', srid=4326, spatial_index=True), nullable=False)
    centroid = Column(CentroidFromPolygon(srid=4326, geometry_type='POINT'))
    sat_id = Column(String(50), ForeignKey('satellites.id'))
    item_type_id = Column(String(50), ForeignKey('item_types.id'))

    
    def get_wkt(self):
        return to_shape(self.geom)

    def get_lon_lat(self):
        lon = session.query(self.centroid.ST_X()).all()
        lat = session.query(self.centroid.ST_Y()).all()
        return lon, lat

    def get_area(self):
        return session.query(self.geom.ST_Area()).all()

    def get_geojson(self):
        return session.query(self.geom.ST_AsGeoJSON()).all()

items_assets = Table(
    'items_assets',
    BASE.metadata,
    Column('item_id', ForeignKey('item_types.id'), primary_key=True),
    Column('asset_id', ForeignKey('asset_types.id'), primary_key=True)
)

class ItemType(BASE):
    __tablename__='item_types'
    id = Column(String(50), primary_key=True)

    sat_id = Column(String(50), ForeignKey('satellites.id'))

    sat_image = relationship('SatImage', backref='item_types')

    assets = relationship('AssetType', secondary=items_assets, backref='item_types')
    
    
class AssetType(BASE):
    __tablename__='asset_types'
    id = Column(String(50), primary_key=True) 


class Country(BASE):
    __tablename__='countries'
    iso = Column(String(3), primary_key=True)
    name = Column(String(50), nullable=False)
    geom = Column(Geometry(geometry_type='MultiPolygon', srid=4326, spatial_index=True), 
                            nullable=False)
    
    sat_images = relationship(
        'SatImage',
        primaryjoin='func.ST_Contains(foreign(Country.geom), remote(SatImage.geom)).as_comparison(1,2)',
        backref='countries',
        viewonly=True,
        uselist=False,
        lazy='joined')

class City(BASE):
    __tablename__='cities'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    geom = Column(Geometry(geometry_type='Point', srid=4326, spatial_index=True), 
                            nullable=False,
                            unique=True)

    sat_images = relationship(
        'SatImage',
        primaryjoin='func.ST_Contains(foreign(City.geom), SatImage.geom).as_comparison(1,2)',
        backref=backref('cities', uselist=False),
        viewonly=True,
        uselist=True)
    
    def get_cities_within_radius(self, radius):
        """Return all cities within a given radius (in meters) of this city."""
        return City.query.filter(func.ST_Distance_Sphere(City.geom, self.geom) < radius).all()


if __name__ == "__main__":
    BASE.metadata.drop_all(ENGINE, checkfirst=True)
    BASE.metadata.create_all(ENGINE)

    centroid = Centroid()
    
    centroid.centroid = 'POLYGON((0 0,1 0,1 1,0 1,0 0))'
    statement = insert(centroid)

   
    
    session.add(centroid)
    session.commit()

