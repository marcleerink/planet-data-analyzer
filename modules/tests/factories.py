import factory
from modules.database import db

class SatelliteFactory(factory.alchemy.SQLAlchemyModelFactory):
    id = factory.sequence(lambda n: '%s' % n)
    name = factory.Faker('name')
    pixel_res = factory.Faker('pyfloat', min_value=0, max_value=1)
    

    class Meta:
        model = db.Satellite