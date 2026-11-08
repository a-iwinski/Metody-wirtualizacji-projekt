# Metody-wirtualizacji-projekt

Projekt zaliczeniowy z przedmiotu **Metody wirtualizacji** (Cyberbezpieczeństwo, I stopień, sem. 3, 2026/2027), Politechnika Poznańska.

## Temat

**Inwentaryzacja sprzętu IT** – aplikacja webowa do ewidencji urządzeń IT w organizacji (komputery, monitory, drukarki, sprzęt sieciowy itp.) z przypisaniem do kategorii i lokalizacji.

## Zespół

| Imię i nazwisko |
|---|
| Wojciech Młynarczyk |
| Antoni Iwiński |

## Architektura

Trzy kontenery uruchamiane przez Docker Compose:

```
[ przeglądarka ] → [ frontend (nginx) ] → [ backend (FastAPI) ] → [ db (PostgreSQL) ]
     :8080              /api/* proxy           :8000                brak portu na zewnątrz
```

- **frontend** – nginx serwuje HTML/JS i przekazuje `/api/*` do backendu; frontend łączy się wyłącznie z backendem
- **backend** – REST API (Python, FastAPI), komunikacja HTTP/JSON
- **db** – PostgreSQL 16 (oficjalny obraz), dane na nazwanym wolumenie `db_data`, dostępny tylko w sieci compose

Kolejność startu: `db` (healthcheck `pg_isready`) → `backend` (healthcheck `GET /health`) → `frontend`.

## Uruchomienie

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:8080
- API: http://localhost:8000 (dokumentacja Swagger: http://localhost:8000/docs)

Reset bazy (ponowne wykonanie `db/init.sql`):

```bash
docker compose down -v
docker compose up --build
```

## Konfiguracja

Hasła i adresy są w zmiennych środowiskowych (plik `.env`, niecommitowany). Wzór w `.env.example`:

| Zmienna | Opis |
|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | dane dostępowe do bazy |
| `DB_HOST`, `DB_PORT` | adres bazy widziany z backendu (`db:5432`) |
| `BACKEND_URL` | adres backendu widziany z nginx (`http://backend:8000`) |
| `BACKEND_PORT`, `FRONTEND_PORT` | porty wystawione na hosta |

## Model danych

```
categories (id, name UNIQUE)
locations  (id, name UNIQUE)
devices    (id, name, serial_number UNIQUE, category_id → categories, location_id → locations, status, created_at)
```

Relacje 1:N: kategoria i lokalizacja mają wiele urządzeń. Schemat i dane startowe: `db/init.sql`.

## API

Wszystkie odpowiedzi i ciała żądań w formacie JSON.

| Metoda | Ścieżka | Opis | Kody |
|---|---|---|---|
| GET | `/health` | stan backendu i bazy | 200, 503 |
| GET | `/api/devices` | lista urządzeń | 200 |
| GET | `/api/devices/{id}` | pojedyncze urządzenie | 200, 400, 404 |
| POST | `/api/devices` | dodanie urządzenia | 201, 400, 409 |
| PUT | `/api/devices/{id}` | aktualizacja urządzenia | 200, 400, 404, 409 |
| DELETE | `/api/devices/{id}` | usunięcie urządzenia | 204, 404 |
| GET | `/api/categories` | lista kategorii | 200 |
| GET | `/api/locations` | lista lokalizacji | 200 |

### Urządzenie – żądanie (POST / PUT)

```json
{
  "name": "Lenovo ThinkPad T14",
  "serial_number": "LT14-0001",
  "category_id": 1,
  "location_id": 2,
  "status": "w_magazynie"
}
```

| Pole | Typ | Wymagane | Reguły |
|---|---|---|---|
| `name` | string | tak | 1–150 znaków |
| `serial_number` | string | tak | 1–100 znaków, unikalny |
| `category_id` | int | tak | > 0, musi istnieć |
| `location_id` | int | tak | > 0, musi istnieć |
| `status` | string | nie | `w_uzyciu` (domyślnie), `w_magazynie`, `w_naprawie`, `wycofany` |

### Urządzenie – odpowiedź

```json
{
  "id": 5,
  "name": "Lenovo ThinkPad T14",
  "serial_number": "LT14-0001",
  "status": "w_magazynie",
  "created_at": "2026-11-08T12:00:00",
  "category_id": 1,
  "category": "Laptop",
  "location_id": 2,
  "location": "Pokój 102"
}
```

### Błędy

| Kod | Kiedy | Przykład |
|---|---|---|
| 400 | błędne dane wejściowe, nieistniejąca kategoria/lokalizacja | `{"detail": "Błędne dane wejściowe", "errors": [{"field": "name", "message": "..."}]}` |
| 404 | zasób nie istnieje | `{"detail": "Urządzenie o id=99 nie istnieje"}` |
| 409 | duplikat numeru seryjnego | `{"detail": "Urządzenie o tym numerze seryjnym już istnieje"}` |
| 503 | brak połączenia z bazą (`/health`) | `{"detail": "Brak połączenia z bazą"}` |

### Przykłady (curl)

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/devices
curl http://localhost:8000/api/devices/1
curl -X POST http://localhost:8000/api/devices -H "Content-Type: application/json" \
     -d '{"name":"Lenovo ThinkPad T14","serial_number":"LT14-0001","category_id":1,"location_id":2}'
curl -X PUT http://localhost:8000/api/devices/1 -H "Content-Type: application/json" \
     -d '{"name":"Dell Latitude 5440","serial_number":"DL5440-001","category_id":1,"location_id":3,"status":"w_naprawie"}'
curl -X DELETE http://localhost:8000/api/devices/1
```

## Frontend

| Widok | Plik | Funkcja |
|---|---|---|
| Lista urządzeń | `index.html` + `list.js` | tabela urządzeń, usuwanie, przejście do edycji |
| Urządzenie | `device.html` + `device.js` | formularz dodawania (`device.html`) i edycji (`device.html?id=1`) |

## Testy

Automatyczny test API (15 przypadków: kody 200/201/204/400/404/409):

```bash
docker compose up -d --build
./tests/api_test.sh            # domyślnie http://localhost:8000
```

## Struktura repozytorium

```
.
├── backend/            # FastAPI: Dockerfile, main.py, requirements.txt
├── frontend/           # nginx: Dockerfile, default.conf.template, public/ (HTML, JS, CSS)
├── db/init.sql         # schemat + dane startowe
├── tests/api_test.sh   # test API curl-em
├── docker-compose.yml
├── .env.example
└── README.md
```

## Kamienie milowe

- [x] KM1 – działający szkielet (3 kontenery, frontend pobiera JSON z backendu, backend łączy się z bazą)
- [x] KM2 – endpointy backendu (CRUD, walidacja 400, 404, `/health`, healthcheck w compose)
- [ ] KM3 – relacje w bazie danych i frontend
- [ ] Zmiana od klienta
- [ ] Moduły bonusowe
- [ ] Finalna dokumentacja

