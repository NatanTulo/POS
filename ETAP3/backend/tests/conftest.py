"""
@file conftest.py
@brief Konfiguracja pytest oraz fixture'ów dla testów jednostkowych i integracyjnych.
@details Definiuje tymczasową bazę danych SQLite w pamięci (in-memory) oraz
         klienta testowego FastAPI z nadpisaną zależnością sesji bazy danych.

@author Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich
@date 2026-06-11
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database.connection import get_db
from backend.database.models import Base

## @brief Adres URL testowej bazy danych w pamięci.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

## @brief Silnik testowej bazy danych (StaticPool pozwala na współdzielenie bazy w pamięci przez połączenia).
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

## @brief Fabryka sesji testowych.
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    @brief Fixture dostarczający sesję testowej bazy danych.
    @details Tworzy tabele przed testem i usuwa je po jego zakończeniu.
    @yield Zwraca sesję SQLAlchemy.
    """
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """
    @brief Fixture dostarczający TestClient dla FastAPI z nadpisaną sesją bazy.
    @param db Fixture sesji bazy danych.
    @yield Zwraca skonfigurowany TestClient.
    """

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
