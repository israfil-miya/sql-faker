#!/usr/bin/env python3
"""
apply_sql.py — Idempotent SQL schema + data applicator.

Applies all sql/*.sql files in lexicographic order to the target database.
Designed to be run from the project root directory.

Usage:
    python scripts/apply_sql.py
    DATABASE_URL=postgresql://... python scripts/apply_sql.py

Environment:
    DATABASE_URL — PostgreSQL connection string (required, or in .env)
"""

import os
import sys
import glob
import logging
from pathlib import Path
import psycopg
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        log.error("DATABASE_URL is not set. Copy .env.example to .env and fill it in.")
        sys.exit(1)

    project_root = Path(__file__).parent.parent
    sql_dir = project_root / "sql"

    sql_files = sorted(sql_dir.glob("*.sql"))
    if not sql_files:
        log.error("No SQL files found in %s", sql_dir)
        sys.exit(1)

    log.info("Connecting to database...")
    try:
        conn = psycopg.connect(database_url, autocommit=False)
    except Exception as exc:
        log.error("Connection failed: %s", exc)
        sys.exit(1)

    with conn:
        for sql_file in sql_files:
            log.info("Applying %s ...", sql_file.name)
            sql_text = sql_file.read_text(encoding="utf-8")
            try:
                with conn.cursor() as cur:
                    cur.execute(sql_text)
                log.info("  ✓ %s applied", sql_file.name)
            except Exception as exc:
                log.error("  ✗ Failed on %s: %s", sql_file.name, exc)
                conn.rollback()
                sys.exit(1)

    conn.close()
    log.info("All SQL files applied successfully.")


if __name__ == "__main__":
    main()

