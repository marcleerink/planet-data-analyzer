"""Module containing the database"""
import os
import psycopg2

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, Table, Column, Integer, Float, String,\
    DateTime, ForeignKey, select, func, inspect, event
from sqlalchemy.types import TypeDecorator
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Insert
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils import database_exists, create_database

from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from geojson import Feature


from config import POSTGIS_URL

Base = declarative_base()


def get_db_engine():
    return create_engine(POSTGIS_URL, echo=False)


def get_db_session():
    engine = get_db_engine()
    Session = sessionmaker(bind=engine)
    return Session()


session = get_db_session()


def sql_alch_commit(model):
    session = get_db_session()
    session.add(model)
    session.commit()

def create_postgis_db(engine):
    create_database(url=engine.url)
    conn = psycopg2.connect(dbname=os.environ['DB_NAME'],
                            user=os.environ['DB_USER'],
                            password=os.environ['DB_PW'],
                            host=os.environ['DB_HOST'],
                            port=os.environ['DB_PORT'])
    cursor = conn.cursor()
    cursor.execute('CREATE EXTENSION postgis')
    conn.commit()
    cursor.close()
    conn.close()

def create_tables(engine, Base):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    # check tables exists
    ins = inspect(engine)
    for _t in ins.get_table_names():
        print(_t)

@compiles(Insert)
def prefix_inserts(insert, compiler, **kw):
    """
    set every insert to ON CONFLICT DO NOTHING for efficient skipping op double items
    """
    return compiler.visit_insert(insert, **kw) + " ON CONFLICT DO NOTHING"


class CentroidFromPolygon(TypeDecorator):
    '''
    Calculate the centroid points of each Polygon on insert.
    Reprojects to equal area proj CRS:3035 for accurate calculation.
    '''
    impl = Geometry
    cache_ok = True

    def bind_expression(self, bindvalue):
        return self.impl.bind_expression(bindvalue).ST_Transform(3035)\
            .ST_Centroid()\
            .ST_Transform(4326)


class Satellite(Base):
    __tablename__ = 'satellites'
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(50), nullable=False, index=True)
    pixel_res = Column(Float)

    sat_images = relationship('SatImage',
                              backref='satellites',
                              lazy='joined'
                              )
    items = relationship('ItemType',
                         backref='satellites',
                         lazy='joined'
                         )


class SatImage(Base):
    __tablename__ = 'sat_images'
    id = Column(String(50), primary_key=True, index=True)
    clear_confidence_percent = Column(Float)
    cloud_cover = Column(Float, nullable=False, index=True)
    time_acquired = Column(DateTime, nullable=False, index=True)
    geom = Column(Geometry(srid=4326, spatial_index=True), nullable=False)
    centroid = Column(CentroidFromPolygon(
        srid=4326, geometry_type='POINT', nullable=False, spatial_index=True))
    sat_id = Column(String(50), ForeignKey('satellites.id'), nullable=False)
    item_type_id = Column(String(50), ForeignKey(
        'item_types.id'), nullable=False)

    land_cover_class = relationship(
        'LandCoverClass',
        primaryjoin='func.ST_Intersects(foreign(SatImage.geom), remote(LandCoverClass.geom)).as_comparison(1,2)',
        backref='sat_image',
        lazy='select',
        viewonly=True,
        uselist=True)



    @hybrid_property
    def sat_name(self):
        return session.scalar(self.satellites.name)

    @sat_name.expression
    def sat_name(cls):
        return cls.satellites.name

    @hybrid_property
    def lon(self):
        return session.scalar(self.centroid.ST_X())

    @lon.expression
    def lon(cls):
        return cls.centroid.ST_X()

    @hybrid_property
    def lat(self):
        return session.scalar(self.centroid.ST_Y())

    @lat.expression
    def lat(cls):
        return cls.centroid.ST_Y()

    @hybrid_property
    def area_sqkm(self):
        area_mm = session.scalar((self.geom.ST_Transform(3035).ST_Area()))
        return round((area_mm / 1000000), 3)
    
    @area_sqkm.expression
    def area_sqkm(cls):
        area_mm = cls.geom.ST_Transform(3035).ST_Area()
        return (area_mm / 1000000)

    @hybrid_property
    def geojson(self):
        return Feature(
            id=self.id,
            geometry=to_shape(self.geom),
            properties={
                "id": self.id,
                "cloud_cover": self.cloud_cover,
                "pixel_res": self.satellites.pixel_res,
                "time_acquired": self.time_acquired.strftime("%Y-%m-%d"),
                "sat_id": self.sat_id,
                "sat_name": self.satellites.name,
                "item_type_id": self.item_type_id,
                "srid": self.srid,
                "area_sqkm": self.area_sqkm,
                "land_cover_class": self.land_cover_class,
                "asset_types": self.item_types.assets,
            })


items_assets = Table(
    'items_assets',
    Base.metadata,
    Column('item_id', ForeignKey('item_types.id'), primary_key=True),
    Column('asset_id', ForeignKey('asset_types.id'), primary_key=True)
)


class ItemType(Base):
    __tablename__ = 'item_types'
    id = Column(String(50), primary_key=True, index=True)

    sat_id = Column(String(50), ForeignKey('satellites.id'), nullable=False)

    sat_image = relationship('SatImage',
                             backref='item_types',)

    assets = relationship('AssetType',
                          secondary=items_assets,
                          backref='item_types',
                          lazy='dynamic')


class AssetType(Base):
    __tablename__ = 'asset_types'
    id = Column(String(50), primary_key=True, index=True)


class Country(Base):
    __tablename__ = 'countries'
    iso = Column(String(3), primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    geom = Column(Geometry(srid=4326, spatial_index=True),
                  nullable=False)

    cities = relationship('City',
                          backref='country',
                          lazy='dynamic')

    sat_images = relationship(
        'SatImage',
        primaryjoin='func.ST_Intersects(foreign(Country.geom), remote(SatImage.geom)).as_comparison(1,2)',
        backref='countries',
        viewonly=True,
        uselist=True)


class City(Base):
    __tablename__ = 'cities'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    country_iso = Column(String(3), ForeignKey('countries.iso'))
    geom = Column(Geometry(geometry_type='Point', srid=4326, spatial_index=True),
                  nullable=False,
                  unique=True)

    sat_images = relationship(
        'SatImage',
        primaryjoin='func.ST_Intersects(foreign(City.buffer), remote(SatImage.geom)).as_comparison(1,2)',
        backref='cities',
        viewonly=True,
        uselist=True)

    @hybrid_property
    def buffer(self):
        return self.geom.ST_Transform(3035).ST_Buffer(30000).ST_Transform(4326)


class LandCoverClass(Base):
    __tablename__ = 'land_cover_classes'
    id = Column(Integer, primary_key=True)
    featureclass = Column(String(50))
    geom = Column(Geometry(srid=4326, spatial_index=True),
                  nullable=False)



if __name__ == '__main__':
    engine = get_db_engine()
    if not database_exists(engine.url):
        create_postgis_db(engine)
    create_tables(engine, Base)

