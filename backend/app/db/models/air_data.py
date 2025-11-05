from app.db.database import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class Airline(Base):
    __tablename__ = "airlines"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(
        String(10), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    logo_url: Mapped[str] = mapped_column(String(255), nullable=True)


class Airport(Base):
    __tablename__ = "airports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    city_name: Mapped[str] = mapped_column(String(100), nullable=False)
    city_code: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    country_code: Mapped[str] = mapped_column(String(10), nullable=False)
    country_name: Mapped[str] = mapped_column(String(100), nullable=False)
    airport_code: Mapped[str] = mapped_column(
        String(10), unique=True, index=True, nullable=False
    )
    airport_name: Mapped[str] = mapped_column(String(255), nullable=False)
