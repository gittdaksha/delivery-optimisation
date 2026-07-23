-- Mart model: FADR by delivery window and address type combined
SELECT
    delivery_window,          -- Morning, Afternoon, Evening time slot
    address_type,             -- type of delivery location
    has_delivery_preference,  -- 1 = customer set a preferred delivery time
    proximity_alert_sent,     -- 1 = SMS alert sent when courier was nearby
    COUNT(*)                                  AS total_attempts, -- total rows in this group
    ROUND(AVG(is_successful), 4)              AS fadr            -- success rate 0 to 1
FROM {{ ref('stg_deliveries_cleaned') }}  -- use the staging model as input
-- GROUP BY with 4 columns: one output row for every unique combination of all four values
-- e.g. "Morning" + "Apartment" + 1 + 0 becomes its own aggregated row
GROUP BY delivery_window, address_type, has_delivery_preference, proximity_alert_sent
-- HAVING filters OUTPUT ROWS after GROUP BY (WHERE filters input rows before grouping)
-- HAVING total_attempts > 50: discard any group that produced fewer than 50 rows
-- → a group with 3 rows would give an unreliable FADR of 0.33 or 1.00 — not meaningful
HAVING total_attempts > 50  -- only show groups with enough data to be meaningful