-- Raw deliveries table: one row per delivery attempt
CREATE TABLE IF NOT EXISTS deliveries (     -- IF NOT EXISTS = skip if already there
    delivery_id       TEXT PRIMARY KEY,     -- TEXT = string; PRIMARY KEY = unique ID
    customer_id       TEXT NOT NULL,        -- NOT NULL = this column must have a value
    city              TEXT NOT NULL,        -- city name e.g. Mumbai
    address_type      TEXT NOT NULL,        -- apartment / office / house etc
    delivery_window   TEXT NOT NULL,        -- time slot e.g. Morning (9-12)
    order_value       REAL NOT NULL,        -- REAL = decimal number (Rs amount)
    is_successful     INTEGER NOT NULL,     -- 1 = success, 0 = failed
    failure_reason    TEXT,                 -- NULL if successful
    attempt_number    INTEGER NOT NULL,     -- INTEGER = whole number
    attempt_date      TEXT NOT NULL,        -- stored as YYYY-MM-DD string
    attempt_hour      INTEGER NOT NULL,     -- hour extracted from window
    has_delivery_preference INTEGER NOT NULL,  -- 0 or 1 flag
    proximity_alert_sent    INTEGER NOT NULL   -- 0 or 1 flag
);

-- Summary table: FADR by city and address type
CREATE TABLE IF NOT EXISTS fadr_by_segment (
    city            TEXT,                   -- one row per city+address_type combo
    address_type    TEXT,
    total_attempts  INTEGER,                -- count of deliveries in this group
    successful      INTEGER,                -- count of successful ones
    fadr            REAL,                   -- successful / total_attempts
    PRIMARY KEY (city, address_type)        -- composite key: pair must be unique
);