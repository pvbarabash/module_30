import factory
from faker import Faker

from module_30.src.models import Client, Parking

fake = Faker()

class ClientFactory(factory.Factory):
    class Meta:
        model = Client

    name = factory.Faker('first_name')
    surname = factory.Faker('last_name')

    credit_card = factory.LazyAttribute(
        lambda _: fake.credit_card_number() if fake.pybool() else None
    )

    car_number = factory.LazyAttribute(lambda _: fake.bothify(text='??-####-??'))


class ParkingFactory(factory.Factory):
    class Meta:
        model = Parking

    address = factory.Faker('address')
    opened = factory.Faker('pybool')
    count_places = factory.Faker('random_int', min=10, max=100)

    count_available_places = factory.LazyAttribute(
        lambda obj: fake.random_int(min=0, max=obj.count_places)
    )