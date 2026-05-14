from typing import Optional

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()


class Client(db.Model):
    __tablename__ = "client"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    surname: Mapped[str] = mapped_column(String(50), nullable=False)
    credit_card: Mapped[Optional[str]] = mapped_column(String(50))
    car_number: Mapped[Optional[str]] = mapped_column(String(10))

    def to_dict(self) -> dict[str, str | int | None]:
        return {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
            "credit_card": self.credit_card,
            "car_number": self.car_number,
        }


class Parking(db.Model):
    __tablename__ = "parking"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    address: Mapped[str] = mapped_column(String(100), nullable=False)
    opened: Mapped[bool] = mapped_column(Boolean(), default=True)
    count_places: Mapped[int] = mapped_column(Integer(), nullable=False)
    count_available_places: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)

    def to_dict(self) -> dict[str, str | bool | int]:
        return {
            "id": self.id,
            "address": self.address,
            "opened": self.opened,
            "count_places": self.count_places,
            "count_available_places": self.count_available_places,
        }


class ClientParking(db.Model):
    __tablename__ = "client_parking"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    client_id: Mapped[int] = mapped_column(Integer(), ForeignKey("client.id"))
    parking_id: Mapped[int] = mapped_column(Integer(), ForeignKey("parking.id"))
    time_in: Mapped[Optional[DateTime]] = mapped_column(DateTime())
    time_out: Mapped[Optional[DateTime]] = mapped_column(DateTime())

    __table_args__ = (
        db.UniqueConstraint("client_id", "parking_id", name="unique_client_parking"),
    )

    def to_dict(self) -> dict[str, int | DateTime | None]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "parking_id": self.parking_id,
            "time_in": self.time_in,
            "time_out": self.time_out,
        }
