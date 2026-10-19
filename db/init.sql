-- AI: plik przygotowany z pomocą Claude (Anthropic) – schemat i dane testowe KM1
-- Wykonuje się tylko przy pierwszym starcie (pusty wolumen db_data).

CREATE TABLE categories (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE locations (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE devices (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(150) NOT NULL,
    serial_number VARCHAR(100) NOT NULL UNIQUE,
    category_id   INT REFERENCES categories(id),
    location_id   INT REFERENCES locations(id),
    status        VARCHAR(30) NOT NULL DEFAULT 'w_uzyciu',
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

INSERT INTO categories (name) VALUES ('Laptop'), ('Monitor'), ('Drukarka'), ('Switch');
INSERT INTO locations  (name) VALUES ('Pokój 101'), ('Pokój 102'), ('Serwerownia');

INSERT INTO devices (name, serial_number, category_id, location_id, status) VALUES
    ('Dell Latitude 5440',  'DL5440-001', 1, 1, 'w_uzyciu'),
    ('Dell P2422H',         'P2422H-014', 2, 1, 'w_uzyciu'),
    ('HP LaserJet M404',    'HPM404-007', 3, 2, 'w_naprawie'),
    ('Cisco Catalyst 2960', 'C2960-0001', 4, 3, 'w_uzyciu');
