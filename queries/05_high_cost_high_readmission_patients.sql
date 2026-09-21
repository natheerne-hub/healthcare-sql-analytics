-- =====================================================================
-- Query 5: High-cost, frequently-readmitted patients (utilization outliers)
--
-- Identifies patients in the top decile of total inpatient charges who
-- also had 2 or more inpatient stays, a common healthcare-BI pattern for
-- flagging patients who may benefit from case management review. Uses a
-- CTE, an aggregate HAVING clause, and NTILE() to bucket patients into
-- cost deciles.
-- =====================================================================

WITH patient_inpatient_summary AS (
    SELECT
        e.patient_id,
        COUNT(*)                      AS inpatient_stays,
        ROUND(SUM(e.total_charge), 2) AS total_inpatient_charges_usd
    FROM encounters e
    WHERE e.encounter_type = 'inpatient'
    GROUP BY e.patient_id
),
deciled AS (
    SELECT
        patient_id,
        inpatient_stays,
        total_inpatient_charges_usd,
        NTILE(10) OVER (ORDER BY total_inpatient_charges_usd) AS cost_decile
    FROM patient_inpatient_summary
)
SELECT
    p.patient_id,
    p.gender,
    p.state,
    d.inpatient_stays,
    d.total_inpatient_charges_usd
FROM deciled d
JOIN patients p ON p.patient_id = d.patient_id
WHERE d.cost_decile = 10        -- top 10% by inpatient spend
  AND d.inpatient_stays >= 2    -- and readmitted at least once
ORDER BY d.total_inpatient_charges_usd DESC
LIMIT 15;
