import pytest
from sqlalchemy import select
from typing import Any, Dict

from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy

from module_30.src.factories import ClientFactory, ParkingFactory
from module_30.src.models import Client, ClientParking, Parking


class TestParkingAPI:
    @pytest.mark.parametrize(
        "url_template,expected_status",
        [
            ("/clients", 200),
            ("/clients/{client_id}", 200),
        ],
    )
    def test_get_methods_return_200(
        self,
        client: FlaskClient,
        app: Flask,
        db_instance: SQLAlchemy,
        url_template: str,
        expected_status: int
    ) -> None:
        """Тест: все GET‑методы возвращают код 200"""
        if "{client_id}" in url_template:
            with app.app_context():
                test_client = db_instance.session.scalar(select(Client))
                if test_client is None:
                    pytest.fail("Тестовый клиент не найден в БД")
                client_id = test_client.id
            url = url_template.format(client_id=client_id)
        else:
            url = url_template

        response = client.get(url)
        assert response.status_code == expected_status

    def test_create_client(
            self,
            client: FlaskClient,
            db_instance: SQLAlchemy
    ) -> None:
        """Тест: создание клиента"""
        data: Dict[str, Any] = {
            "name": "New",
            "surname": "Client",
            "credit_card": "5678123456781234",
            "car_number": "B456DE777",
        }
        response = client.post("/clients", json=data)
        assert response.status_code == 201

        response_data: Dict[str, Any] = response.get_json()
        assert response_data["name"] == "New"
        assert response_data["surname"] == "Client"

        with client.application.app_context():
            stmt = select(Client).where(
                Client.name == "New", Client.surname == "Client"
            )
            created_client = db_instance.session.scalar(stmt)
            assert created_client is not None
            assert created_client.car_number == "B456DE777"

    def test_create_client_with_factory(
            self,
            client: FlaskClient,
            db_instance: SQLAlchemy,
    ) -> None:
        new_client = ClientFactory()

        client_data: Dict[str, Any] = new_client.to_dict()  # type: ignore[attr-defined]

        response = client.post("/clients", json=client_data)
        assert response.status_code == 201

        response_data: Dict[str, Any] = response.get_json()
        assert response_data["name"] == new_client.name
        assert response_data["surname"] == new_client.surname

        with client.application.app_context():
            stmt = select(Client).where(
                Client.name == new_client.name, Client.surname == new_client.surname
            )
            created_client = db_instance.session.scalar(stmt)
            assert created_client is not None
            assert created_client.car_number == new_client.car_number

    def test_create_parking(
            self,
            client: FlaskClient,
            db_instance: SQLAlchemy,
    ) -> None:
        """Тест: создание парковки"""
        data: Dict[str, Any] = {"address": "New Parking Address", "count_places": 20}
        response = client.post("/parkings", json=data)
        assert response.status_code == 201

        response_data: Dict[str, Any] = response.get_json()
        assert response_data["address"] == "New Parking Address"
        assert response_data["count_available_places"] == 20

        with client.application.app_context():
            stmt = select(Parking).where(Parking.address == "New Parking Address")
            created_parking = db_instance.session.scalar(stmt)
            assert created_parking is not None
            assert created_parking.count_places == 20
            assert created_parking.count_available_places == 20

    def test_create_parking_with_factory(
            self,
            client: FlaskClient,
            db_instance: SQLAlchemy,
    ) -> None:
        new_parking = ParkingFactory()
        parking_data: Dict[str, Any] = new_parking.to_dict() # type: ignore[attr-defined]

        response = client.post("/parkings", json=parking_data)
        assert response.status_code == 201

        response_data: Dict[str, Any] = response.get_json()
        assert response_data["address"] == new_parking.address
        assert (
            response_data["count_available_places"]
            == new_parking.count_available_places
        )

        with client.application.app_context():
            stmt = select(Parking).where(Parking.address == new_parking.address)
            created_parking = db_instance.session.scalar(stmt)
            assert created_parking is not None
            assert created_parking.count_places == new_parking.count_places
            assert (
                created_parking.count_available_places
                == new_parking.count_available_places
            )

    @pytest.mark.parking
    def test_enter_parking_success(
            self,
            client: FlaskClient,
            db_instance: SQLAlchemy,
    ) -> None:
        """Тест: успешный заезд на парковку"""
        new_client_data: Dict[str, Any] = {
            "name": "NewTest",
            "surname": "Client",
            "credit_card": "1111222233334444",
            "car_number": "C789EF777",
        }
        client.post("/clients", json=new_client_data)

        with client.application.app_context():
            stmt = select(Client).where(
                Client.name == "NewTest", Client.surname == "Client"
            )
            new_client = db_instance.session.scalar(stmt)

            stmt = select(Parking)
            parking_obj = db_instance.session.scalar(stmt)

            available_places_before = db_instance.session.scalar(
                select(Parking.count_available_places).where(
                    Parking.id == parking_obj.id
                )
            )

            data: Dict[str, Any] = {"client_id": new_client.id, "parking_id": parking_obj.id}
            response = client.post("/client_parkings", json=data)
            assert response.status_code == 201

            response_data: Dict[str, Any] = response.get_json()
            assert response_data["client_id"] == new_client.id
            assert response_data["parking_id"] == parking_obj.id
            assert response_data["time_in"] is not None
            assert response_data["time_out"] is None

            # Проверяем уменьшение свободных мест
            updated_parking = db_instance.session.get(Parking, parking_obj.id)
            assert updated_parking.count_available_places == available_places_before - 1

            # Проверяем создание записи в логе
            stmt = select(ClientParking).where(
                ClientParking.client_id == new_client.id,
                ClientParking.parking_id == parking_obj.id,
            )
            log_entry = db_instance.session.scalar(stmt)
            assert log_entry is not None
            assert log_entry.time_in is not None
            assert log_entry.time_out is None

    @pytest.mark.parking
    def test_exit_parking_success(
            self,
            client: FlaskClient,
            db_instance: SQLAlchemy,
    ) -> None:
        """Тест: успешный выезд с парковки"""
        new_client_data: Dict[str, Any] = {
            "name": "NewTest",
            "surname": "Client",
            "credit_card": "1111222233334444",
            "car_number": "C789EF777",
        }
        client.post("/clients", json=new_client_data)

        with client.application.app_context():
            stmt = select(Client).where(
                Client.name == "NewTest", Client.surname == "Client"
            )
            new_client = db_instance.session.scalar(stmt)

            stmt = select(Parking)
            parking_obj = db_instance.session.scalar(stmt)

            data: Dict[str, Any] = {"client_id": new_client.id, "parking_id": parking_obj.id}
            client.post("/client_parkings", json=data)

            available_places_before = db_instance.session.scalar(
                select(Parking.count_available_places).where(
                    Parking.id == parking_obj.id
                )
            )

            # Теперь выезжаем
            exit_data: Dict[str, Any] = {"client_id": new_client.id, "parking_id": parking_obj.id}
            response = client.delete("/client_parkings", json=exit_data)
            assert response.status_code == 200

            # Проверяем увеличение свободных мест
            updated_parking = db_instance.session.get(Parking, parking_obj.id)
            assert updated_parking.count_available_places == available_places_before + 1

            # Проверяем время выезда
            stmt = select(ClientParking).where(
                ClientParking.client_id == new_client.id,
                ClientParking.parking_id == parking_obj.id,
            )
            log_entry = db_instance.session.execute(stmt).scalar_one_or_none()
            assert log_entry.time_out is not None
            assert log_entry.time_out >= log_entry.time_in
