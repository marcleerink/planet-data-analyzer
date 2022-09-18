from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geometry
import pandas as pd
import os

def db_engine():
    engine = create_engine(os.getenv('POSTGIS'), echo=True)
    return engine
   

# engine = db_engine()
# Session = sessionmaker(bind=engine)
# session = Session()
# Base = declarative_base()

# class GwWell(Base):
#     __tablename__ = 'gwwells'
#     id = Column(Integer, primary_key=True)
#     station = Column(String)
#     lat = Column(Float)
#     lon = Column(Float)
#     date = Column(DateTime)
#     geom = Column(Geometry(geometry_type='POINT', srid='4269'))
# GwWell.__table__.create(engine)
# GwWell.__table__