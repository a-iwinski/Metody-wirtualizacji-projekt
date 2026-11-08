# AI: plik przygotowany z pomocą Claude (Anthropic) – API backendu (KM1 + KM2)
import os
from typing import Literal

import psycopg
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

app = FastAPI(title="Inwentaryzacja sprzętu IT")

# Dozwolone statusy urządzenia
Status = Literal["w_uzyciu", "w_magazynie", "w_naprawie", "wycofany"]


class DeviceIn(BaseModel):
    """Dane wejściowe dla POST i PUT – walidowane automatycznie przez Pydantic."""
    name: str = Field(min_length=1, max_length=150)
    serial_number: str = Field(min_length=1, max_length=100)
    category_id: int = Field(gt=0)
    location_id: int = Field(gt=0)
    status: Status = "w_uzyciu"


def get_conn():
    """Połączenie z bazą – wszystkie dane ze zmiennych środowiskowych."""
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        dbname=os.environ["DB_NAME"],
        row_factory=dict_row,
    )


# ---------- obsługa błędów ----------

@app.exception_handler(RequestValidationError)
def validation_error(request: Request, exc: RequestValidationError):
    """Błędne dane wejściowe → 400 (domyślnie FastAPI zwraca 422)."""
    errors = [
        {"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(status_code=400, content={"detail": "Błędne dane wejściowe", "errors": errors})


def db_error(e: psycopg.Error):
    """Zamiana błędów bazy na czytelne kody HTTP."""
    if isinstance(e, psycopg.errors.UniqueViolation):
        raise HTTPException(409, "Urządzenie o tym numerze seryjnym już istnieje")
    if isinstance(e, psycopg.errors.ForeignKeyViolation):
        raise HTTPException(400, "Podana kategoria lub lokalizacja nie istnieje")
    raise e


# ---------- health ----------

@app.get("/health")
@app.get("/api/health")
def health():
    """Stan backendu i połączenia z bazą (używany przez healthcheck w compose)."""
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "db": "ok"}
    except Exception:
        raise HTTPException(503, "Brak połączenia z bazą")


# ---------- słowniki ----------

@app.get("/api/categories")
def list_categories():
    with get_conn() as conn:
        return conn.execute("SELECT id, name FROM categories ORDER BY name").fetchall()


@app.get("/api/locations")
def list_locations():
    with get_conn() as conn:
        return conn.execute("SELECT id, name FROM locations ORDER BY name").fetchall()


# ---------- urządzenia (CRUD) ----------

DEVICE_SELECT = """
    SELECT d.id, d.name, d.serial_number, d.status, d.created_at,
           d.category_id, c.name AS category,
           d.location_id, l.name AS location
    FROM devices d
    LEFT JOIN categories c ON c.id = d.category_id
    LEFT JOIN locations  l ON l.id = d.location_id
"""


def fetch_device(conn, device_id: int):
    device = conn.execute(DEVICE_SELECT + " WHERE d.id = %s", (device_id,)).fetchone()
    if device is None:
        raise HTTPException(404, f"Urządzenie o id={device_id} nie istnieje")
    return device


@app.get("/api/devices")
def list_devices():
    """Lista wszystkich urządzeń."""
    with get_conn() as conn:
        return conn.execute(DEVICE_SELECT + " ORDER BY d.id").fetchall()


@app.get("/api/devices/{device_id}")
def get_device(device_id: int):
    """Pojedyncze urządzenie; 404 jeśli nie istnieje."""
    with get_conn() as conn:
        return fetch_device(conn, device_id)


@app.post("/api/devices", status_code=201)
def create_device(data: DeviceIn):
    """Dodanie urządzenia; 400 przy błędnych danych, 409 przy duplikacie nr seryjnego."""
    try:
        with get_conn() as conn:
            new_id = conn.execute(
                """INSERT INTO devices (name, serial_number, category_id, location_id, status)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (data.name, data.serial_number, data.category_id, data.location_id, data.status),
            ).fetchone()["id"]
            return fetch_device(conn, new_id)
    except psycopg.Error as e:
        db_error(e)


@app.put("/api/devices/{device_id}")
def update_device(device_id: int, data: DeviceIn):
    """Pełna aktualizacja urządzenia; 404 jeśli nie istnieje."""
    try:
        with get_conn() as conn:
            updated = conn.execute(
                """UPDATE devices
                   SET name = %s, serial_number = %s, category_id = %s, location_id = %s, status = %s
                   WHERE id = %s RETURNING id""",
                (data.name, data.serial_number, data.category_id, data.location_id, data.status, device_id),
            ).fetchone()
            if updated is None:
                raise HTTPException(404, f"Urządzenie o id={device_id} nie istnieje")
            return fetch_device(conn, device_id)
    except psycopg.Error as e:
        db_error(e)


@app.delete("/api/devices/{device_id}", status_code=204)
def delete_device(device_id: int):
    """Usunięcie urządzenia; 404 jeśli nie istnieje."""
    with get_conn() as conn:
        deleted = conn.execute("DELETE FROM devices WHERE id = %s RETURNING id", (device_id,)).fetchone()
    if deleted is None:
        raise HTTPException(404, f"Urządzenie o id={device_id} nie istnieje")
    return Response(status_code=204)
