#!/usr/bin/env python3
"""
Generate a fully synthetic healthcare encounters database.

No real patient data or protected health information (PHI) is used anywhere
in this project. Patients, dates, charges, and diagnosis assignments are all
generated with a fixed random seed so the dataset is reproducible.

Usage:
    python generate_synthetic_data.py [--db healthcare.db] [--seed 42]
"""

import argparse
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DEPARTMENTS = [
    "Cardiology",
    "Internal Medicine",
    "Emergency Medicine",
    "Orthopedics",
    "Pulmonology",
    "Endocrinology",
    "General Surgery",
]

# A small set of realistic ICD-10-CM codes across the departments above,
# used only to generate plausible synthetic diagnosis records.
ICD10_CODES = [
    ("I50.9", "Heart failure, unspecified"),
    ("I21.9", "Acute myocardial infarction, unspecified"),
    ("I10", "Essential (primary) hypertension"),
    ("E11.9", "Type 2 diabetes mellitus without complications"),
    ("E11.65", "Type 2 diabetes mellitus with hyperglycemia"),
    ("J44.9", "Chronic obstructive pulmonary disease, unspecified"),
    ("J18.9", "Pneumonia, unspecified organism"),
    ("N18.3", "Chronic kidney disease, stage 3"),
    ("M17.9", "Osteoarthritis of knee, unspecified"),
    ("S72.001A", "Fracture of neck of right femur, initial encounter"),
    ("K35.80", "Unspecified acute appendicitis"),
    ("I63.9", "Cerebral infarction, unspecified"),
    ("F32.9", "Major depressive disorder, single episode, unspecified"),
    ("R07.9", "Chest pain, unspecified"),
    ("A41.9", "Sepsis, unspecified organism"),
]

STATES = ["CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
    "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
]


def build_schema(conn: sqlite3.Connection, schema_path: Path) -> None:
    conn.executescript(schema_path.read_text())


def random_date(rng: random.Random, start: date, end: date) -> date:
    delta_days = (end - start).days
    return start + timedelta(days=rng.randint(0, delta_days))


def generate(conn: sqlite3.Connection, rng: random.Random,
             n_patients: int, n_encounters: int) -> None:
    cur = conn.cursor()

    # Departments
    cur.executemany(
        "INSERT INTO departments (department_id, department_name) VALUES (?, ?)",
        [(i + 1, name) for i, name in enumerate(DEPARTMENTS)],
    )

    # Providers: 3-6 per department
    provider_id = 1
    providers_by_dept = {}
    for dept_id, dept_name in enumerate(DEPARTMENTS, start=1):
        providers_by_dept[dept_id] = []
        for _ in range(rng.randint(3, 6)):
            name = f"Dr. {rng.choice(LAST_NAMES)}"
            cur.execute(
                "INSERT INTO providers (provider_id, provider_name, department_id) "
                "VALUES (?, ?, ?)",
                (provider_id, name, dept_id),
            )
            providers_by_dept[dept_id].append(provider_id)
            provider_id += 1

    # Patients
    today = date.today()
    for pid in range(1, n_patients + 1):
        gender = rng.choice(["F", "M"])
        age_years = rng.randint(18, 92)
        birth_date = today - timedelta(days=age_years * 365 + rng.randint(0, 364))
        state = rng.choice(STATES)
        cur.execute(
            "INSERT INTO patients (patient_id, gender, birth_date, state) "
            "VALUES (?, ?, ?, ?)",
            (pid, gender, birth_date.isoformat(), state),
        )

    # Encounters + diagnoses
    window_start = date(2024, 1, 1)
    window_end = date(2025, 12, 31)
    encounter_types = ["inpatient", "outpatient", "emergency"]
    type_weights = [0.35, 0.45, 0.20]
    diagnosis_id = 1

    # Give ~18% of patients a second encounter within 30 days of a first
    # inpatient stay, to produce a realistic, non-trivial readmission signal.
    for eid in range(1, n_encounters + 1):
        patient_id = rng.randint(1, n_patients)
        dept_id = rng.randint(1, len(DEPARTMENTS))
        provider_id_choice = rng.choice(providers_by_dept[dept_id])
        enc_type = rng.choices(encounter_types, weights=type_weights, k=1)[0]

        admit = random_date(rng, window_start, window_end)
        if enc_type == "inpatient":
            los = max(1, int(rng.gauss(4, 2)))
        elif enc_type == "emergency":
            los = rng.choice([0, 0, 1])
        else:
            los = 0
        discharge = admit + timedelta(days=los)

        base_charge = {
            "inpatient": rng.gauss(18000, 6000),
            "emergency": rng.gauss(4500, 1800),
            "outpatient": rng.gauss(900, 400),
        }[enc_type]
        total_charge = round(max(150.0, base_charge), 2)

        cur.execute(
            "INSERT INTO encounters (encounter_id, patient_id, provider_id, "
            "department_id, encounter_type, admission_date, discharge_date, total_charge) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (eid, patient_id, provider_id_choice, dept_id, enc_type,
             admit.isoformat(), discharge.isoformat(), total_charge),
        )

        n_dx = rng.choices([1, 2, 3], weights=[0.5, 0.35, 0.15], k=1)[0]
        chosen = rng.sample(ICD10_CODES, k=n_dx)
        for i, (code, desc) in enumerate(chosen):
            cur.execute(
                "INSERT INTO diagnoses (diagnosis_id, encounter_id, icd10_code, "
                "description, is_primary) VALUES (?, ?, ?, ?, ?)",
                (diagnosis_id, eid, code, desc, 1 if i == 0 else 0),
            )
            diagnosis_id += 1

    conn.commit()


def add_readmissions(conn: sqlite3.Connection, rng: random.Random) -> None:
    """Second pass: add a realistic number of 30-day readmission encounters."""
    cur = conn.cursor()
    cur.execute(
        "SELECT encounter_id, patient_id, department_id, discharge_date "
        "FROM encounters WHERE encounter_type = 'inpatient'"
    )
    inpatient_rows = cur.fetchall()

    cur.execute("SELECT MAX(encounter_id) FROM encounters")
    next_eid = cur.fetchone()[0] + 1
    cur.execute("SELECT MAX(diagnosis_id) FROM diagnoses")
    next_did = cur.fetchone()[0] + 1

    cur.execute("SELECT provider_id, department_id FROM providers")
    providers_by_dept = {}
    for provider_id, dept_id in cur.fetchall():
        providers_by_dept.setdefault(dept_id, []).append(provider_id)

    for encounter_id, patient_id, dept_id, discharge_date in inpatient_rows:
        if rng.random() < 0.19:
            gap = rng.randint(2, 29)
            admit = date.fromisoformat(discharge_date) + timedelta(days=gap)
            los = max(1, int(rng.gauss(3, 1.5)))
            discharge = admit + timedelta(days=los)
            total_charge = round(max(150.0, rng.gauss(16000, 5000)), 2)
            provider_id_choice = rng.choice(providers_by_dept[dept_id])

            cur.execute(
                "INSERT INTO encounters (encounter_id, patient_id, provider_id, "
                "department_id, encounter_type, admission_date, discharge_date, total_charge) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (next_eid, patient_id, provider_id_choice, dept_id, "inpatient",
                 admit.isoformat(), discharge.isoformat(), total_charge),
            )
            code, desc = rng.choice(ICD10_CODES)
            cur.execute(
                "INSERT INTO diagnoses (diagnosis_id, encounter_id, icd10_code, "
                "description, is_primary) VALUES (?, ?, ?, ?, 1)",
                (next_did, next_eid, code, desc),
            )
            next_eid += 1
            next_did += 1

    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="healthcare.db", help="Output SQLite file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--patients", type=int, default=600)
    parser.add_argument("--encounters", type=int, default=2200)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    db_path = Path(args.db)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    build_schema(conn, Path(__file__).parent / "schema.sql")
    generate(conn, rng, args.patients, args.encounters)
    add_readmissions(conn, rng)

    counts = {}
    for table in ["patients", "departments", "providers", "encounters", "diagnoses"]:
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()

    print(f"Synthetic database written to {db_path.resolve()}")
    for table, n in counts.items():
        print(f"  {table}: {n:,} rows")


if __name__ == "__main__":
    main()
