import logging
import os
from dotenv import load_dotenv

load_dotenv()
POSTGIS_URL = os.environ['POSTGIS_URL']
PL_API_KEY = os.environ['PL_API_KEY']


logging.basicConfig(level=logging.INFO, format="%(processName)s:%(message)s")
LOGGER = logging.getLogger(__name__)
f_handler = logging.FileHandler('reports/importer.log')
f_handler.setLevel(logging.ERROR)
LOGGER.addHandler(f_handler)

