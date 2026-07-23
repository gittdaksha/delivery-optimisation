-- Mart model: FADR aggregated by city and address type
-- This is what the dashboard and ML model will read from
SELECT
    city,                                             -- group output by city
    address_type,                                     -- group output by address type
    -- COUNT(*): counts every row in the group regardless of NULL values
    COUNT(*)                                  AS total_attempts,         -- rows per group
    -- SUM(is_successful): adds up all values; since is_successful is 0 or 1, sum = count of successes
    -- → rows [1, 0, 1, 1, 0] → SUM = 3 (three successful deliveries)
    SUM(is_successful)                        AS successful_deliveries,  -- count of 1s = successes
    -- AVG(is_successful): mean of a 0/1 column = fraction of 1s = success rate
    -- → rows [1, 0, 1, 1, 0] → AVG = 0.6 (60% success rate)
    -- ROUND(value, 4): keep 4 decimal places  → 0.600000 → 0.6000
    ROUND(AVG(is_successful), 4)              AS fadr,         -- avg of 0/1 = success rate
    -- AVG(1 - is_successful): flip 0→1 and 1→0, then average = failure fraction
    -- → rows [1, 0, 1, 1, 0] → (1-is_successful) = [0,1,0,0,1] → AVG = 0.4
    ROUND(AVG(1 - is_successful), 4)          AS failure_rate, -- 1 - fadr = failure rate
    AVG(order_value)                          AS avg_order_value -- mean order value per group
-- What {{ ref() }} means: this is dbt's way of referencing another model you built
-- (rather than a raw source table). dbt uses this to build a dependency graph —
-- it knows stg_deliveries must run before mart_fadr_by_segment.
FROM {{ ref('stg_deliveries_cleaned') }}        -- use the staging model as input
-- GROUP BY collapses all rows with the same combination of values into ONE output row
-- GROUP BY city, address_type: e.g. all "Mumbai" + "Apartment" rows become one aggregated row
GROUP BY city, address_type             -- one output row per city + address type combo