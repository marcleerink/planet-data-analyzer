import logging

# Logger
logging.basicConfig(level=logging.INFO, format="%(processName)s:%(message)s")
LOGGER = logging.getLogger(__name__)
f_handler = logging.FileHandler('reports/importer.log')
f_handler.setLevel(logging.ERROR)
LOGGER.addHandler(f_handler)