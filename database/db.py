from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os
load_dotenv()

POSTGIS_URL = os.environ['POSTGIS_URL']
ENGINE = create_engine(POSTGIS_URL, echo=True)

BASE = declarative_base()

SESSION = sessionmaker(bind=ENGINE)
SESSION.configure(bind=ENGINE)

