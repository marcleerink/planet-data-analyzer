from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, backref
from geoalchemy2 import Geometry
from database.db import BASE, ENGINE

class Satellite(BASE):
    __tablename__='satellites'
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    pixel_res = Column(Float)

    sat_images = relationship('SatImage', back_populates='satellites')
    items = relationship('ItemType', back_populates='satellites')

class SatImage(BASE):
    __tablename__='sat_images'
    id = Column(String(100), primary_key=True)
    clear_confidence_percent = Column(Float, nullable=False)
    cloud_cover = Column(Float, nullable=False)
    pixel_res = Column(Float, nullable=False)
    time_acquired = Column(DateTime, nullable=False)
    geom = Column(Geometry(geometry_type='Polygon', srid=4326), nullable=False)

    sat_id = Column(String(50), ForeignKey('satellites.id'))
    satellite = relationship('Satellite', back_populates='sat_images')

    item_type_id = Column(String(50), ForeignKey('item_types.id'))
    item_type = relationship('ItemType', back_populates='sat_images')


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
    satellite = relationship('Satellite', back_populates='item_types')

    sat_image = relationship('SatImage', back_populates='item_types')

    assets = relationship('AssetType', secondary=items_assets, back_populates='item_types')
    
    
class AssetType(BASE):
    __tablename__='asset_types'
    id = Column(String(50), primary_key=True) 
    items = relationship('ItemType', secondary=items_assets, back_populates='asset_types')


class Country(BASE):
    __tablename__='countries'
    iso3 = Column(String(3), primary_key=True)
    formal_name = Column(String(50), nullable=False)
    continent = Column(String(50), nullable=False)
    population  = Column(Integer)
    geom = Column(Geometry(geometry_type='Multipolygon', srid=4326), nullable=False)

    cities = relationship('City', backref='countries')

    sat_images = relationship(
        'SatImage',
        primaryjoin='func.ST_Contains(foreign(Country.geom), SatImage.geom).as_comparison(1,2)',
        backref=backref('countries', uselist=False),
        viewonly=True,
    )

class City(BASE):
    __tablename__='cities'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    population = Column(Integer)
    geom = Column(Geometry(geometry_type='Point', srid=4326), nullable=False)

    country_iso3 = Column(String(3), ForeignKey('countries.iso3'))

# BASE.metadata.drop_all(ENGINE)
# BASE.metadata.create_all(ENGINE)