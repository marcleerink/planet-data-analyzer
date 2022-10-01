from importlib.resources import path
from sqlite3 import Date, Timestamp
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from geoalchemy2 import Geometry
import os

BASE = declarative_base()
ENGINE = create_engine('postgresql://postgres:5jippie5@localhost:5432/planet', echo=True)

SESSION = sessionmaker(bind=ENGINE)
SESSION.configure(bind=ENGINE)

def db_engine(path='POSTGIS'):
    return create_engine(os.getenv(path), echo=True)

class Satellite(BASE):
    __tablename__='satellites'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    pixel_res = Column(Float)
    amount = Column(Integer, nullable=False)

    sat_images = relationship('SatImage', backref='satellites')

    def __init__(self, name, pixel_res, amount):
        self.name = name
        self.pixel_res = pixel_res
        self.amount = amount

class SatImage(BASE):
    __tablename__='sat_images'
    id = Column(Integer, primary_key=True)
    cloud_cover = Column(Float)
    pixel_res = Column(Float, nullable=False)
    time_acquired = Column(DateTime, nullable=False)
    geom = Column(Geometry(geometry_type='Polygon', srid=4326), nullable=False)

    sat_id = Column(Integer, ForeignKey('satellites.id'))

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


BASE.metadata.drop_all(ENGINE)
BASE.metadata.create_all(ENGINE)


planetscope = Satellite(name='PlanetScope', pixel_res=3.0, amount=130)

session = SESSION()
session.add(planetscope)
session.commit()