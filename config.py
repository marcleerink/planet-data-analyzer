import logging
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.environ['DB_USER']
DB_PW = os.environ['DB_PW']
DB_NAME = os.environ['DB_NAME']
DB_HOST = os.environ['DB_HOST']
DB_PORT = os.environ['DB_PORT']

POSTGIS_URL=f"postgresql://{DB_USER}:{DB_PW}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

PL_API_KEY = os.environ['PL_API_KEY']

logging.basicConfig(level=logging.INFO, format="%(processName)s:%(message)s")
LOGGER = logging.getLogger(__name__)
f_handler = logging.FileHandler('importer.log')
f_handler.setLevel(logging.ERROR)
LOGGER.addHandler(f_handler)

