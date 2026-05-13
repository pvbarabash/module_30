import pytest
from module_30.src.app import create_app
from module_30.src.models import db, Client, Parking, ClientParking
from datetime import datetime, timezone


@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()

        test_client = Client(
            name='Test',
            surname='User',
            credit_card='1234567890123456',
            car_number='A123BC777'
        )


        test_parking = Parking(
            address='Test Parking Address',
            count_places=10,
            count_available_places=10
        )


        db.session.add(test_client)
        db.session.add(test_parking)
        db.session.commit()

        client_id = test_client.id
        parking_id = test_parking.id

        test_log = ClientParking(
            client_id=client_id,
            parking_id=parking_id,
            time_in=datetime(2023, 10, 1, 10, 0, 0, tzinfo=timezone.utc),
            time_out=datetime(2023, 10, 1, 12, 0, 0, tzinfo=timezone.utc)
        )
        db.session.add(test_log)
        db.session.commit()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db_instance(app):
    with app.app_context():
        yield db