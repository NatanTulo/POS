"""
@file main.py
@brief Główny punkt wejścia aplikacji backendowej systemu monitorowania pojazdu.
@details Inicjalizuje serwer FastAPI, rejestruje routery oraz konfiguruje
         połączenie z bazą danych przy starcie aplikacji.

@author Natan Tułodziecki, Maksymilian Szmigiel, Paweł Reich
@date 2026-05-28
@copyright MIT
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.endpoints import router as api_router
from backend.database.connection import create_tables, engine

## @brief Konfiguracja loggera dla modułu głównego.
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    @brief Zarządza cyklem życia aplikacji FastAPI.
    @details Przy starcie tworzy tabele w bazie danych (jeśli nie istnieją),
             a przy zamknięciu zamyka połączenie z silnikiem bazy.
    @param app Instancja aplikacji FastAPI.
    """
    logger.info("Initializing database tables...")
    create_tables()
    logger.info("Application started successfully.")
    yield
    logger.info("Shutting down engine...")
    engine.dispose()
    logger.info("Engine disposed.")


def create_application() -> FastAPI:
    """
    @brief Tworzy i konfiguruje instancję aplikacji FastAPI.
    @details Rejestruje mechanizm lifespan, dodaje middleware CORS
             oraz dołącza router z endpointami API.
    @return Skonfigurowana instancja FastAPI.
    """
    app = FastAPI(
        title="Vehicle Monitoring System API",
        description=(
            "System monitorowania parametrów pojazdu – "
            "API do zarządzania sesjami, odczytami czujników OBD, "
            "alertami oraz eksportem danych."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    return app


## @brief Globalna instancja aplikacji FastAPI.
app = create_application()
