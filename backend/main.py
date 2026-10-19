# AI: plik przygotowany z pomocą Claude (Anthropic) – szkielet backendu KM1
import os

import psycopg
from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row

app = FastAPI(title="Inwentaryzacja sprzętu IT")


def get_conn():
    """Połączenie z bazą – wszystkie dane z zmiennych środowiskowych."""
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        dbname=os.environ["DB_NAME"],
        row_factory=dict_row,
    )


@app.get("/api/health")
def health():
    """Sprawdza, czy backend działa i czy łączy się z bazą."""
    try:
        with get_conn() as conn:
            version = conn.execute("SELECT version() AS v").fetchone()["v"]
        return {"status": "ok", "db": "ok", "db_version": version}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Brak połączenia z bazą: {e}")


@app.get("/api/devices")
def list_devices():
    """Lista urządzeń z nazwą kategorii i lokalizacji."""
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT d.id, d.name, d.serial_number, d.status, d.created_at,
                   c.name AS category, l.name AS location
            FROM devices d
            LEFT JOIN categories c ON c.id = d.category_id
            LEFT JOIN locations  l ON l.id = d.location_id
            ORDER BY d.id
            """
        ).fetchall()
