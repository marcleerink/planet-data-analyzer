import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from factories import SatelliteFactory
from modules.database.db import Satellite
import os

engine = create_engine(os.environ['POSTGIS_URL'], echo=True)
Session = sessionmaker()

@pytest.fixture(scope='module')
def connection():
    connection = engine.connect()
    yield connection
    connection.close()

@pytest.fixture(scope='function')
def session(connection):
    transaction = connection.begin()
    session = Session(bind=connection)
    SatelliteFactory._meta.sqlalchemy_session = session # NB: This line added
    yield session
    session.close()
    transaction.rollback()
    
def delete_satellite(session, sat_id):
    session.query(Satellite).filter(Satellite.id == sat_id).delete()

def test_case_satellite(session):
    satellite = SatelliteFactory.create()
    assert session.query(Satellite).one()

    delete_satellite(session, satellite.id)

    result = session.query(Satellite).one_or_none()
    assert result is None