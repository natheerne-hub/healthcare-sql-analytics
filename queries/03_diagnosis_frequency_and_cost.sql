-- =====================================================================
-- Query 3: Most frequent primary diagnoses and their average encounter cost
--
-- Joins diagnoses (primary diagnosis only) to their parent encounter to
-- rank ICD-10 codes by frequency and show the average total charge of the
-- encounters they appear on.
-- =====================================================================

SELECT
    dx.icd10_code,
    dx.description,
    COUNT(*)                          AS encounter_count,
    ROUND(AVG(e.total_charge), 2)     AS avg_encounter_charge_usd,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM diagnoses WHERE is_primary = 1), 1)
                                       AS pct_of_primary_diagnoses
FROM diagnoses dx
JOIN encounters e ON e.encounter_id = dx.encounter_id
WHERE dx.is_primary = 1
GROUP BY dx.icd10_code, dx.description
ORDER BY encounter_count DESC
LIMIT 10;
