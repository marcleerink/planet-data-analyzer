import psycopg2
import os

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy import create_engine, Table, Column, Integer, Float, String,\
    DateTime, ForeignKey, func
from sqlalchemy.types import TypeDecorator
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Insert
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils import database_exists, create_database

from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from geojson import Feature, FeatureCollection, dumps

from modules.config import POSTGIS_URL

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

def create_tables(engine, Base):
    if not database_exists(engine.url):
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
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

# set every insert to ON CONFLICT DO NOTHING
@compiles(Insert)
def prefix_inserts(insert, compiler, **kw):
    return compiler.visit_insert(insert, **kw) + " ON CONFLICT DO NOTHING"

class MultiGeomFromSingle(TypeDecorator):
    '''Converts single geometries to multi geometries(MultiPolygon/MultiLinestring'''
    impl = Geometry
    cache_ok = True

    def bind_expression(self, bindvalue):
        return self.impl.bind_expression(bindvalue).ST_Multi()
        

class CentroidFromPolygon(TypeDecorator):
    '''
    Calculate the centroid points of each Polygon on insert.
    Reprojects to equal area proj CRS:3035.
    '''
    impl = Geometry
    cache_ok = True

    def bind_expression(self, bindvalue):
        return self.impl.bind_expression(bindvalue).ST_Transform(3035)\
                                                    .ST_Centroid()\
                                                    .ST_Transform(4326)

class Satellite(Base):
    __tablename__='satellites'
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
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
    __tablename__='sat_images'
    id = Column(String(100), primary_key=True)
    clear_confidence_percent = Column(Float)
    cloud_cover = Column(Float, nullable=False)
    time_acquired = Column(DateTime, nullable=False)
    geom = Column(Geometry(srid=4326, spatial_index=True), nullable=False)
    centroid = Column(CentroidFromPolygon(srid=4326, geometry_type='POINT', nullable=False))
    sat_id = Column(String(50), ForeignKey('satellites.id'))
    item_type_id = Column(String(50), ForeignKey('item_types.id'))
    
    land_cover_class = relationship(
                    'LandCoverClass',
                    primaryjoin='func.ST_Intersects(foreign(SatImage.geom), remote(LandCoverClass.geom)).as_comparison(1,2)',
                    backref='sat_image',
                    viewonly=True,
                    uselist=True,
                    lazy='joined')
    
    @hybrid_property
    def check_wkb(wkb, x, y):
        pt = to_shape(wkb)
        assert round(pt.x, 5) == x
        assert round(pt.y, 5) == y

    @hybrid_property
    def wkt(self):
        return to_shape(self.geom)

    @hybrid_property
    def srid(self):
        return session.scalar(self.geom.ST_SRID())

    @hybrid_property
    def lon(self):
        return session.scalar(self.centroid.ST_X())

    @hybrid_property   
    def lat(self):
        return session.scalar(self.centroid.ST_Y())
  
    @hybrid_property
    def area_sqkm(self):
        area_mm = session.scalar((self.geom.ST_Transform(3035).ST_Area()))
        return round((area_mm / 1000000), 3)

    @hybrid_property
    def image_covers_land_cover_class(self, land_cover_geom):
        session.scalar(self.geom.ST_Overlaps())

    @hybrid_property
    def geojson(self): 
        return Feature(
                id=self.id,
                geometry=to_shape(self.geom),
                properties={
                    "id" : self.id,
                    "cloud_cover" : self.cloud_cover,
                    "pixel_res" : self.satellites.pixel_res,
                    "time_acquired" : self.time_acquired.strftime("%Y-%m-%d"),
                    "sat_id" : self.sat_id,
                    "sat_name" : self.satellites.name,
                    "item_type_id" : self.item_type_id,
                    "srid" : self.srid,
                    "area_sqkm": self.area_sqkm,
                    "land_cover_class" : self.land_cover_class,
                    "asset_types": self.item_types.assets,
                })

items_assets = Table(
    'items_assets',
    Base.metadata,
    Column('item_id', ForeignKey('item_types.id'), primary_key=True),
    Column('asset_id', ForeignKey('asset_types.id'), primary_key=True)
)

class ItemType(Base):
    __tablename__='item_types'
    id = Column(String(50), primary_key=True)

    sat_id = Column(String(50), ForeignKey('satellites.id'))

    sat_image = relationship('SatImage', 
                            backref='item_types',)

    assets = relationship('AssetType', 
                            secondary=items_assets, 
                            backref='item_types',
                            lazy='dynamic')
    
    
class AssetType(Base):
    __tablename__='asset_types'
    id = Column(String(50), primary_key=True) 


class Country(Base):
    __tablename__='countries'
    iso = Column(String(3), primary_key=True)
    name = Column(String(50), nullable=False)
    geom = Column(Geometry(srid=4326, spatial_index=True), 
                            nullable=False)
    
    sat_images = relationship(
        'SatImage',
        primaryjoin='func.ST_Intersects(foreign(Country.geom), remote(SatImage.geom)).as_comparison(1,2)',
        backref='countries',
        viewonly=True,
        uselist=False,
        lazy='joined')

    cities = relationship(
        'City',
        primaryjoin='func.ST_Intersects(foreign(Country.geom), remote(City.geom)).as_comparison(1,2)',
        backref='countries',
        viewonly=True,
        uselist=True,
        lazy='joined')
    
    

class City(Base):
    __tablename__='cities'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    geom = Column(Geometry(geometry_type='Point', srid=4326, spatial_index=True), 
                            nullable=False,
                            unique=True)

    join_query = 'func.ST_Intersects(foreign(City.buffer), remote(SatImage.geom)).as_comparison(1,2)'
    sat_images = relationship(
        'SatImage',
        primaryjoin= join_query,
        backref='cities',
        viewonly=True,
        uselist=True,
        lazy='joined')
    
    @hybrid_property
    def buffer(self):
        return self.geom.ST_Transform(3035).ST_Buffer(50000).ST_Transform(4326)


class LandCoverClass(Base):
    __tablename__='land_cover_classes'
    id = Column(Integer, primary_key=True)
    featureclass = Column(String(50))
    geom = Column(Geometry(srid=4326, spatial_index=True),
                            nullable=False)



if __name__=='__main__':
    engine = get_db_engine()
    create_tables(engine, Base)