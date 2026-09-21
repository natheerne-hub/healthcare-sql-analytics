-- =====================================================================
-- Query 4: Monthly admission volume and revenue trend by encounter type
--
-- Uses strftime to bucket encounters into calendar months, pivoting
-- encounter type into columns with conditional aggregation, plus a
-- running (cumulative) total of charges via a window function.
-- =====================================================================

WITH monthly AS (
    SELECT
        strftime('%Y-%m', admission_date)                              AS admit_month,
        COUNT(*)                                                        AS total_encounters,
        SUM(CASE WHEN encounter_type = 'inpatient'  THEN 1 ELSE 0 END)  AS inpatient_count,
        SUM(CASE WHEN encounter_type = 'outpatient' THEN 1 ELSE 0 END)  AS outpatient_count,
        SUM(CASE WHEN encounter_type = 'emergency'  THEN 1 ELSE 0 END)  AS emergency_count,
        ROUND(SUM(total_charge), 2)                                     AS total_charges_usd
    FROM encounters
    GROUP BY admit_month
)
SELECT
    admit_month,
    total_encounters,
    inpatient_count,
    outpatient_count,
    emergency_count,
    total_charges_usd,
    ROUND(SUM(total_charges_usd) OVER (ORDER BY admit_month), 2) AS cumulative_charges_usd
FROM monthly
ORDER BY admit_month;
