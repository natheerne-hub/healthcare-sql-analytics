-- =====================================================================
-- Healthcare SQL Analytics — Schema
-- Dr. Nather Yunis Suliaman, MD
--
-- A small, normalized healthcare data warehouse schema representing
-- patients, providers, departments, encounters, and diagnoses.
-- Designed to demonstrate relational modeling and analytical SQL over
-- a realistic (fully synthetic) clinical encounter dataset.
-- =====================================================================

DROP TABLE IF EXISTS diagnoses;
DROP TABLE IF EXISTS encounters;
DROP TABLE IF EXISTS providers;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS patients;

CREATE TABLE patients (
    patient_id      INTEGER PRIMARY KEY,
    gender          TEXT NOT NULL CHECK (gender IN ('F', 'M')),
    birth_date      TEXT NOT NULL,          -- ISO date
    state           TEXT NOT NULL           -- US state abbreviation (synthetic)
);

CREATE TABLE departments (
    department_id   INTEGER PRIMARY KEY,
    department_name TEXT NOT NULL UNIQUE
);

CREATE TABLE providers (
    provider_id     INTEGER PRIMARY KEY,
    provider_name   TEXT NOT NULL,
    department_id   INTEGER NOT NULL REFERENCES departments(department_id)
);

CREATE TABLE encounters (
    encounter_id    INTEGER PRIMARY KEY,
    patient_id      INTEGER NOT NULL REFERENCES patients(patient_id),
    provider_id     INTEGER NOT NULL REFERENCES providers(provider_id),
    department_id   INTEGER NOT NULL REFERENCES departments(department_id),
    encounter_type  TEXT NOT NULL CHECK (encounter_type IN ('inpatient', 'outpatient', 'emergency')),
    admission_date  TEXT NOT NULL,          -- ISO date
    discharge_date  TEXT NOT NULL,          -- ISO date, >= admission_date
    total_charge    REAL NOT NULL CHECK (total_charge >= 0)
);

CREATE TABLE diagnoses (
    diagnosis_id    INTEGER PRIMARY KEY,
    encounter_id    INTEGER NOT NULL REFERENCES encounters(encounter_id),
    icd10_code      TEXT NOT NULL,
    description     TEXT NOT NULL,
    is_primary      INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1))
);

CREATE INDEX idx_encounters_patient   ON encounters(patient_id);
CREATE INDEX idx_encounters_provider  ON encounters(provider_id);
CREATE INDEX idx_encounters_admit     ON encounters(admission_date);
CREATE INDEX idx_diagnoses_encounter  ON diagnoses(encounter_id);
CREATE INDEX idx_diagnoses_icd10      ON diagnoses(icd10_code);
