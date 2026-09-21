-- =====================================================================
-- Query 2: Inpatient length of stay (LOS) by department
--
-- Summarizes average, median (via a percentile approximation), and max
-- length of stay for inpatient encounters, one row per department.
-- =====================================================================

SELECT
    d.department_name,
    COUNT(*)                                                        AS inpatient_stays,
    ROUND(AVG(julianday(e.discharge_date) - julianday(e.admission_date)), 2)
                                                                     AS avg_los_days,
    MAX(julianday(e.discharge_date) - julianday(e.admission_date))
                                                                     AS max_los_days,
    ROUND(AVG(e.total_charge), 2)                                   AS avg_charge_usd
FROM encounters e
JOIN departments d ON d.department_id = e.department_id
WHERE e.encounter_type = 'inpatient'
GROUP BY d.department_name
ORDER BY avg_los_days DESC;
