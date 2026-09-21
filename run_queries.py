#!/usr/bin/env python3
"""
Build the synthetic database (if missing), run every query in queries/,
print each result as a table, and write a CSV of each result to results/.

This is the project's reproducibility check: a clean run of this script
against a freshly generated database is what the CI workflow verifies.

Usage:
    python run_queries.py [--db healthcare.db]
"""

import argparse
import sqlite3
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
QUERIES_DIR = ROOT / "queries"
RESULTS_DIR = ROOT / "results"


def ensure_database(db_path: Path) -> None:
    if db_path.exists():
        return
    print(f"No database found at {db_path}, generating synthetic data...")
    subprocess.run(
        [sys.executable, str(ROOT / "generate_synthetic_data.py"), "--db", str(db_path)],
        check=True,
    )


def run_all(db_path: Path) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(db_path)

    query_files = sorted(QUERIES_DIR.glob("*.sql"))
    if not query_files:
        raise SystemExit(f"No .sql files found in {QUERIES_DIR}")

    for sql_file in query_files:
        sql = sql_file.read_text()
        df = pd.read_sql_query(sql, conn)

        out_csv = RESULTS_DIR / f"{sql_file.stem}.csv"
        df.to_csv(out_csv, index=False)

        print(f"\n=== {sql_file.name} ===")
        print(f"-> {len(df)} rows written to {out_csv.relative_to(ROOT)}")
        with pd.option_context("display.max_columns", None, "display.width", 120):
            print(df.head(10).to_string(index=False))

    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="healthcare.db")
    args = parser.parse_args()

    db_path = Path(args.db)
    ensure_database(db_path)
    run_all(db_path)
    print("\nAll queries executed successfully.")


if __name__ == "__main__":
    main()
