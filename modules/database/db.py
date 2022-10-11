from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref, column_property
from sqlalchemy import create_engine, Table, Column, Integer, Float, String,\
    DateTime, ForeignKey, func, CheckConstraint
from geoalchemy2 import Geometry
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import insert
from geoalchemy2.shape import from_shape, to_shape
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Insert
from modules.config import POSTGIS_URL



ENGINE = create_engine(POSTGIS_URL, echo=False)
BASE = declarative_base()
SESSION = sessionmaker(bind=ENGINE)
session = SESSION()

# hack that sets every insert to ON CONFLICT DO NOTHING
@compiles(Insert)
def prefix_inserts(insert, compiler, **kw):
    return compiler.visit_insert(insert, **kw) + " ON CONFLICT DO NOTHING"

class MultiGeomFromSingle(TypeDecorator):
    '''Converts single geometries to multi geometries(multipolygon/multilinestring'''
    impl = Geometry
    cache_ok = True

    def bind_expression(self, bindvalue):
        return func.ST_Multi(self.impl.bind_expression(bindvalue))

class CentroidFromPolygon(TypeDecorator):
    '''Insert the centroid points on each Polygon insert'''
    impl = Geometry
    cache_ok = True

    def bind_expression(self, bindvalue):
        return func.ST_Centroid(self.impl.bind_expression(bindvalue))

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
    centroid = Column(CentroidFromPolygon(srid=4326, geometry_type='POINT', nullable=False))
    sat_id = Column(String(50), ForeignKey('satellites.id'))
    item_type_id = Column(String(50), ForeignKey('item_types.id'))
    
    def check_wkb(wkb, x, y):
        pt = to_shape(wkb)
        assert round(pt.x, 5) == x
        assert round(pt.y, 5) == y

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
    geom = Column(MultiGeomFromSingle(geometry_type='MultiPolygon', srid=4326, spatial_index=True), 
                            nullable=False)
    
    sat_images = relationship(
        'SatImage',
        primaryjoin='func.ST_Contains(foreign(Country.geom), remote(SatImage.geom)).as_comparison(1,2)',
        backref='countries',
        viewonly=True,
        uselist=False,
        lazy='joined')

    cities = relationship(
        'City',
        primaryjoin='func.ST_Contains(foreign(Country.geom), remote(City.geom)).as_comparison(1,2)',
        backref='countries',
        viewonly=True,
        uselist=False,
        lazy='joined')

    urban_areas = relationship(
        'UrbanArea',
        primaryjoin='func.ST_Intersects(foreign(Country.geom), remote(UrbanArea.geom)).as_comparison(1,2)',
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
        primaryjoin='func.ST_Intersects(func.ST_Buffer(foreign(City.geom),5), remote(SatImage.geom)).as_comparison(1,2)',
        backref='cities',
        viewonly=True,
        uselist=False,
        lazy='joined')
    
    def get_cities_within_radius(self, radius):
        """Return all cities within a given radius (in meters) of this city."""
        return City.query.filter(func.ST_Distance_Sphere(City.geom, self.geom) < radius).all()

class LandCoverClass(BASE):
    __tablename__='land_cover_classes'
    featureclass = Column(String(50), primary_key=True)
    
    rivers_lakes = relationship('RiverLake', backref='land_cover_classes')
    urban_areas = relationship('UrbanArea', backref='land_cover_classes')

class UrbanArea(BASE):
    __tablename__='urban_areas'
    id = Column(Integer, primary_key=True)
    area_sqkm = Column(Float)
    featureclass = Column(String(50), 
                    ForeignKey('land_cover_classes.featureclass'),
                    nullable=False)
    geom = Column(Geometry(geometry_type='Polygon', srid=4326, spatial_index=True),
                    nullable=False)
    
    cities = relationship(
        'City',
        primaryjoin='func.ST_Within(foreign(UrbanArea.geom), remote(City.geom)).as_comparison(1,2)',
        backref='urban_areas',
        viewonly=True,
        uselist=False,
        lazy='joined')

class RiverLake(BASE):
    __tablename__='rivers_lakes'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    featureclass = Column(String(50), 
                    ForeignKey('land_cover_classes.featureclass'), 
                    nullable=False)
    geom = Column(MultiGeomFromSingle(geometry_type='MultiLineString', srid=4326, spatial_index=True),
                            nullable=False)

    cities = relationship(
        'City',
        primaryjoin='func.ST_Within(foreign(RiverLake.geom), remote(City.geom)).as_comparison(1,2)',
        backref='rivers_lakes',
        viewonly=True,
        uselist=False,
        lazy='joined')

if __name__ == "__main__":
    BASE.metadata.drop_all(ENGINE, checkfirst=True)
    BASE.metadata.create_all(ENGINE)

