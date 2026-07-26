-- ============================================================
-- QUERY 1: Overall FADR (the headline metric)
-- Business question: What % of deliveries succeed on first attempt?
-- ============================================================
-- COUNT(*): counts every row regardless of value
-- → 50 000 rows in table → total_attempts = 50000

-- SUM(is_successful): is_successful is 0 or 1; summing 1s = counting successes
-- → values: 1,0,1,1,0 → SUM = 3 → successful = 3

-- AVG(is_successful) * 100: AVG of a 0/1 column = the proportion that are 1
-- → AVG(1,0,1,1,0) = 3/5 = 0.60  → × 100 = 60.0  → ROUND(..., 2) = 60.00
-- → fadr_percent = 60.00 means "60% first-attempt success rate"

-- SUM(1 - is_successful): flips 1→0 and 0→1, then sums — counts the 0s (failures)
-- → row is_successful=1 → 1-1=0 (not counted)
-- → row is_successful=0 → 1-0=1 (counted as failure)
-- → failed = total rows where is_successful was 0
SELECT
    COUNT(*)                                      AS total_attempts,     -- count every row
    SUM(is_successful)                            AS successful,         -- sum 1s = count successes
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent,       -- avg of 0/1 = rate; *100 = percent
    SUM(1 - is_successful)                        AS failed,             -- 1-1=0, 1-0=1 flips the flag
    ROUND(AVG(1 - is_successful) * 100, 2)        AS failure_rate_percent -- same trick for failures
FROM deliveries;                                                         -- the raw data table


-- ============================================================
-- QUERY 2: FADR by delivery window
-- Business question: When do deliveries fail most?
-- Insight: Morning slots have lowest FADR because people are at work.
-- ============================================================
-- GROUP BY delivery_window: collapses all rows with the same window into one output row
-- example rows in table: Morning,1 / Morning,0 / Afternoon,1 / Morning,1
-- → after GROUP BY:  Morning group   (3 rows) → COUNT=3, AVG=0.67 → fadr=66.67
--                    Afternoon group (1 row)  → COUNT=1, AVG=1.00 → fadr=100.00

-- ORDER BY fadr_percent ASC: ASC = ascending = smallest number first
-- → worst-performing window appears at the top of results (easiest to spot problems)
SELECT
    delivery_window,                              -- group label (Morning / Afternoon etc)
    COUNT(*)                                      AS total_attempts,     -- rows in each group
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent        -- success rate per window
FROM deliveries
GROUP BY delivery_window                          -- one result row per time window
ORDER BY fadr_percent ASC;                        -- ASC = worst (lowest) first


-- ============================================================
-- QUERY 3: FADR by address type
-- Business question: Which address types are hardest to deliver to?
-- Insight: Apartments/PGs fail more — access restrictions, no one home.
-- ============================================================
-- GROUP BY address_type: same mechanics as Query 2 — one output row per distinct address_type value
-- → Apartment group → its own COUNT and AVG
-- → Office group    → its own COUNT and AVG
-- ORDER BY fadr_percent ASC: lowest success rate (worst) appears first
SELECT
    address_type,                                 -- group label (Apartment / Office etc)
    COUNT(*)                                      AS total_attempts,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY address_type                             -- one result row per address type
ORDER BY fadr_percent ASC;                        -- worst performer at top


-- ============================================================
-- QUERY 4: Impact of delivery preferences
-- Business question: Does having a saved preference improve success?
-- This validates Feature 4 from the LinkedIn post.
-- ============================================================
-- GROUP BY has_delivery_preference: only two distinct values (0 and 1) so result is exactly 2 rows
-- → group 0: all rows with no preference → their own COUNT, AVG → fadr_percent
-- → group 1: all rows with a preference  → their own COUNT, AVG → fadr_percent
-- reading the two rows side by side shows the impact of having a preference
SELECT
    has_delivery_preference,                      -- 0 = no preference, 1 = has preference
    COUNT(*)                                      AS total_attempts,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY has_delivery_preference;                 -- compare 0 vs 1 side by side


-- ============================================================
-- QUERY 5: Impact of proximity alerts
-- Business question: Does a 15-minute early alert improve success?
-- This validates Feature 5 from the LinkedIn post.
-- ============================================================
-- GROUP BY proximity_alert_sent: same 2-row pattern as Query 4
-- → group 0: deliveries where no alert was sent → COUNT and AVG → fadr_percent
-- → group 1: deliveries where alert was sent    → COUNT and AVG → fadr_percent
-- difference between the two fadr_percent values = measurable impact of the alert feature
SELECT
    proximity_alert_sent,                         -- 0 = no alert, 1 = alert sent
    COUNT(*)                                      AS total_attempts,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY proximity_alert_sent;                    -- compare 0 vs 1 side by side


-- ============================================================
-- QUERY 6: Top failure reasons
-- Business question: Why are deliveries failing?
-- ============================================================

-- What a subquery is: (SELECT COUNT(*) FROM deliveries WHERE is_successful = 0) is a
-- "subquery" — a query inside a query. It runs first and returns one number (the total
-- failed count), which the outer query then divides by to calculate a percentage.

-- WHERE is_successful = 0: filters BEFORE grouping — only failed rows enter GROUP BY
-- → rows with is_successful=1 are discarded entirely from this query

-- subquery (SELECT COUNT(*) FROM deliveries WHERE is_successful = 0):
-- → runs once, returns a single number, e.g. 12 000 (total failed deliveries)
-- → the outer query divides each group's count by that number

-- COUNT(*) * 100.0 / subquery: step-by-step for one group
-- → failure_reason = 'Wrong Address', COUNT(*) = 3600
-- → 3600 * 100.0 = 360000.0   (the .0 forces decimal division, not integer division)
-- → 360000.0 / 12000 = 30.0   → ROUND(..., 2) = 30.00
-- → pct_of_failures = 30.00 means "Wrong Address is 30% of all failures"

-- ORDER BY count DESC: DESC = descending = largest number first → most common reason at top
SELECT
    failure_reason,                               -- text label for why it failed
    COUNT(*)                                      AS count,              -- how many times this reason occurred
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM deliveries WHERE is_successful = 0), 2) AS pct_of_failures  -- share of all failures
FROM deliveries
WHERE is_successful = 0                           -- only look at failed deliveries
GROUP BY failure_reason                           -- one row per failure reason
ORDER BY count DESC;                              -- most common reason first


-- ============================================================
-- QUERY 7: Cost of failure (estimated)
-- Business question: What is the operational cost of failed deliveries?
-- Assumptions: avg repeat attempt costs Rs 45 in fuel + time
-- ============================================================
-- SUM(1 - is_successful): flip-and-sum trick from Query 1 — counts failures per city group
-- → city='Mumbai': rows 1,0,0,1,0 → 1-values: 0,1,1,0,1 → SUM = 3 → failed_deliveries = 3

-- SUM(1 - is_successful) * 45: multiply the failure count by cost assumption
-- → failed_deliveries = 3 → 3 * 45 = 135 → estimated_cost_inr = 135

-- ORDER BY estimated_cost_inr DESC: DESC = largest first → most expensive city at the top
SELECT
    city,                                         -- group by city
    SUM(1 - is_successful)                        AS failed_deliveries,  -- count failures per city
    SUM(1 - is_successful) * 45                   AS estimated_cost_inr, -- failures * Rs 45 per attempt
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY city
ORDER BY estimated_cost_inr DESC;                 -- most expensive city at top


-- ============================================================
-- QUERY 8: Worst combination (cross-segment analysis)
-- Business question: What is the single worst address+window combination?
-- ============================================================

-- What HAVING does: HAVING filters groups after aggregation — WHERE filters
-- individual rows before grouping. You cannot use WHERE here because
-- total_attempts does not exist until after GROUP BY creates it.
-- Think of it as: WHERE filters rows, HAVING filters groups.

-- GROUP BY address_type, delivery_window: creates one row per PAIR of values
-- → ('Apartment', 'Morning') → one row
-- → ('Apartment', 'Afternoon') → separate row
-- → ('Office', 'Morning') → separate row
-- total distinct combinations could be 3 address types × 4 windows = up to 12 rows

-- HAVING total_attempts > 200: filters the GROUPS produced by GROUP BY
-- execution order:  1) GROUP BY runs → creates groups
--                   2) COUNT(*) is calculated for each group → total_attempts exists now
--                   3) HAVING filters out groups where total_attempts <= 200
-- → you cannot use WHERE here because total_attempts does not exist until after step 1

-- LIMIT 10: after ORDER BY sorts all remaining rows, LIMIT cuts the output to 10 rows
-- → only the 10 worst address+window combinations are returned
SELECT
    address_type,
    delivery_window,
    COUNT(*)                                      AS total_attempts,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY address_type, delivery_window            -- one row per address+window pair
HAVING total_attempts > 200                       -- HAVING = filter groups (not rows)
ORDER BY fadr_percent ASC                         -- worst combo first
LIMIT 10;                                         -- show only top 10 worst results


-- ============================================================
-- QUERY 9: Repeat attempt analysis
-- Business question: How many parcels needed 2 or 3 attempts?
-- ============================================================
-- subquery (SELECT COUNT(*) FROM deliveries): returns total row count, e.g. 50 000
-- COUNT(*) * 100.0 / 50000: step-by-step for attempt_number = 2
-- → COUNT(*) for group 2 = 11 000
-- → 11000 * 100.0 = 1100000.0   (100.0 not 100 → forces decimal division)
-- → 1100000.0 / 50000 = 22.0    → ROUND(..., 2) = 22.00
-- → pct_of_total = 22.00 means "22% of all deliveries needed a 2nd attempt"

-- ORDER BY attempt_number: no ASC/DESC specified → defaults to ASC → 1, 2, 3 in order
SELECT
    attempt_number,                               -- 1, 2, or 3
    COUNT(*)                                      AS deliveries,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM deliveries), 2) AS pct_of_total  -- share of all deliveries
FROM deliveries
GROUP BY attempt_number                           -- one row per attempt number
ORDER BY attempt_number;                          -- show 1, 2, 3 in order


-- ============================================================
-- QUERY 10: Impact of high order value on failure
-- Business question: Do expensive orders fail more (hand-over only)?
-- ============================================================

-- What CASE WHEN does: it is SQL's version of an if/else statement.
-- It reads each row and assigns a label based on the value in a column.
-- WHEN condition THEN 'label' — the first matching condition wins.
-- ELSE covers anything that did not match any earlier WHEN.

-- CASE WHEN evaluates conditions top-to-bottom; the FIRST matching WHEN wins
-- example row: order_value = 350
-- → WHEN 350 < 500  → TRUE  → result = 'Under Rs 500'  (stops here, skips rest)
-- example row: order_value = 800
-- → WHEN 800 < 500  → FALSE → try next
-- → WHEN 800 < 1500 → TRUE  → result = 'Rs 500-1500'   (stops here)
-- example row: order_value = 4500
-- → WHEN 4500 < 500  → FALSE
-- → WHEN 4500 < 1500 → FALSE
-- → WHEN 4500 < 3000 → FALSE
-- → ELSE             → result = 'Above Rs 3000'         (catch-all for remaining rows)
-- END AS value_bucket: closes the CASE expression and names the resulting column
SELECT
    CASE
        WHEN order_value < 500  THEN 'Under Rs 500'   -- first matching WHEN wins
        WHEN order_value < 1500 THEN 'Rs 500-1500'
        WHEN order_value < 3000 THEN 'Rs 1500-3000'
        ELSE 'Above Rs 3000'                           -- ELSE = catch-all for remaining rows
    END                                           AS value_bucket,       -- label for this bucket
    COUNT(*)                                      AS total_attempts,
    ROUND(AVG(is_successful) * 100, 2)            AS fadr_percent
FROM deliveries
GROUP BY value_bucket                             -- one row per price bucket
ORDER BY fadr_percent ASC;                        -- cheapest bucket vs most expensive