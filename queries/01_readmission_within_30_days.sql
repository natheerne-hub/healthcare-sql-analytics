-- =====================================================================
-- Query 1: 30-day inpatient readmission rate by department
--
-- For each inpatient encounter, find whether the same patient had another
-- inpatient encounter starting within 30 days of that discharge. This uses
-- a self-join with a window function to look ahead to each patient's next
-- inpatient admission, mirroring how a real readmission KPI is computed.
-- =====================================================================

WITH inpatient_stays AS (
    SELECT
        e.encounter_id,
        e.patient_id,
        e.department_id,
        e.admission_date,
        e.discharge_date,
        LEAD(e.admission_date) OVER (
            PARTITION BY e.patient_id
            ORDER BY e.admission_date
        ) AS next_admission_date
    FROM encounters e
    WHERE e.encounter_type = 'inpatient'
),
flagged AS (
    SELECT
        encounter_id,
        department_id,
        discharge_date,
        next_admission_date,
        CASE
            WHEN next_admission_date IS NOT NULL
                 AND julianday(next_admission_date) - julianday(discharge_date) <= 30
                 AND julianday(next_admission_date) - julianday(discharge_date) >= 0
            THEN 1 ELSE 0
        END AS is_readmission_index
    FROM inpatient_stays
)
SELECT
    d.department_name,
    COUNT(*)                                   AS inpatient_discharges,
    SUM(f.is_readmission_index)                AS readmissions_within_30d,
    ROUND(100.0 * SUM(f.is_readmission_index) / COUNT(*), 1) AS readmission_rate_pct
FROM flagged f
JOIN departments d ON d.department_id = f.department_id
GROUP BY d.department_name
ORDER BY readmission_rate_pct DESC;
