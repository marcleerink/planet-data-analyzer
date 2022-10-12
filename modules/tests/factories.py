import factory
from modules.database import db
from geofactory import GeoFactory
from geojson.utils import generate_random
from shapely.geometry import shape

class SatelliteFactory(factory.alchemy.SQLAlchemyModelFactory):
    id = factory.sequence(lambda n: '%s' % n)
    name = factory.Faker('name')
    pixel_res = factory.Faker('pyfloat', min_value=0, max_value=10)

    class Meta:
        model = db.Satellite

class SatImageFactory(factory.alchemy.SQLAlchemyModelFactory):
    id = factory.sequence(lambda n: '%s' % n)
    clear_confidence_percent = factory.Faker('pyfloat', min_value=0, max_value=100)
    cloud_cover = factory.Faker('pyfloat', min_value=0, max_value=1)
    pixel_res = factory.Faker('pyfloat', min_value=0, max_value=10)
    time_acquired = factory.Faker('date_object')
    geom = shape(generate_random('Polygon')).wkt
    centroid = shape(generate_random('Polygon')).wkt
    sat_id = factory.Faker('pystr', max_chars=50)
    item_type_id = factory.Faker('pystr', max_chars=50)

    class Meta:
        model = db.SatImage