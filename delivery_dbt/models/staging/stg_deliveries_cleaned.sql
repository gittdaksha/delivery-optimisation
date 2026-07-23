-- Staging model: clean and type-cast raw deliveries
-- This is the first layer — we standardise columns but don't add business logic yet
SELECT
    delivery_id,                -- pass through the unique delivery ID unchanged
    customer_id,                -- pass through the customer identifier unchanged
    city,                       -- city of the delivery address
    address_type,               -- Apartment, House, Office, etc.
    delivery_window,            -- time slot: Morning, Afternoon, Evening
    -- CAST(expr AS type): converts a column's data type; CSVs load all columns as text by default
    -- CAST(order_value AS REAL): "134" (text string) → 134.0 (decimal number usable in math)
    CAST(order_value AS REAL)           AS order_value,      -- convert to decimal number
    -- CAST(is_successful AS INTEGER): "1" (text) → 1 (integer; guarantees 0 or 1, not "0"/"1")
    CAST(is_successful AS INTEGER)      AS is_successful,    -- ensure stored as 0 or 1
    failure_reason,             -- why delivery failed (NULL if successful)
    -- CAST(attempt_number AS INTEGER): "2" (text) → 2 (integer; needed for ORDER BY and arithmetic)
    CAST(attempt_number AS INTEGER)     AS attempt_number,   -- which attempt: 1, 2, 3
    -- DATE(attempt_date): strips the time portion from a datetime value
    -- → "2024-01-15 08:32:11" → "2024-01-15" (date string only, no time)
    DATE(attempt_date)                  AS attempt_date,     -- extract date only, drop time
    CAST(attempt_hour AS INTEGER)       AS attempt_hour,     -- hour 0-23 as integer
    CAST(has_delivery_preference AS INTEGER) AS has_delivery_preference, -- 0 or 1
    CAST(proximity_alert_sent AS INTEGER)    AS proximity_alert_sent     -- 0 or 1
FROM {{ source('main', 'deliveries') }} -- raw table defined in sources.yml
-- WHERE filters individual rows BEFORE any grouping or aggregation
-- IS NOT NULL: true if the column has a value; false if the cell is empty/missing (NULL)
WHERE delivery_id IS NOT NULL           -- drop rows that have no delivery ID
-- What {{ source() }} means: this is dbt's way of referencing a raw table that already
-- exists in the database (the one you loaded from CSV in Guide 02). It tells dbt
-- "this table is an external source, not one I built." dbt tracks it in the lineage graph.