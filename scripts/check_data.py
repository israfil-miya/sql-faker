#!/usr/bin/env python3
"""
check_data.py — Validates data integrity in the database.

Checks:
  1. pool_sizes matches actual COUNT(*) for each pool.
  2. idx columns are gap-free (1..N with no holes).
  3. Every locale has all required pools and choice categories.
  4. cities postal_min <= postal_max.
  5. body_params exist for all required (locale, gender, attribute) combos.

Usage:
    python scripts/check_data.py
    DATABASE_URL=postgresql://... python scripts/check_data.py
"""

import os
import sys
import logging
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

REQUIRED_NAME_POOLS    = ["first_male", "first_female", "last"]
REQUIRED_POOLS         = REQUIRED_NAME_POOLS + ["streets", "cities"]
REQUIRED_CHOICE_CATS   = [
    "title_male", "title_female",
    "name_template",
    "addr_template",
    "street_type",
    "phone_template",
    "email_sep", "email_num", "email_domain",
    "eye_color",
]
REQUIRED_BODY_ATTRS    = ["height_cm", "weight_kg"]
REQUIRED_GENDERS       = ["male", "female"]
MIN_POOL_SIZE          = 500   # warn (not fail) below this


def check(conn) -> bool:
    ok = True

    with conn.cursor() as cur:
        # --- Get locales ---
        cur.execute("SELECT code FROM locales ORDER BY code")
        locales = [r["code"] for r in cur.fetchall()]
        if not locales:
            log.error("No locales found in database.")
            return False
        log.info("Locales: %s", locales)

        for locale in locales:
            log.info("--- Checking locale: %s ---", locale)

            # 1. pool_sizes vs actual counts
            for pool in REQUIRED_NAME_POOLS:
                cur.execute(
                    "SELECT COUNT(*) AS n FROM names WHERE locale=%s AND kind=%s",
                    (locale, pool)
                )
                actual = cur.fetchone()["n"]
                cur.execute(
                    "SELECT size FROM pool_sizes WHERE locale=%s AND pool=%s",
                    (locale, pool)
                )
                row = cur.fetchone()
                if row is None:
                    log.error("  pool_sizes missing: %s / %s", locale, pool)
                    ok = False
                elif row["size"] != actual:
                    log.error("  pool_sizes mismatch: %s / %s — pool_sizes=%d, actual=%d",
                              locale, pool, row["size"], actual)
                    ok = False
                else:
                    log.info("  ✓ names.%s: %d rows", pool, actual)
                if actual < MIN_POOL_SIZE:
                    log.warning("  ⚠ names.%s has only %d rows (recommend ≥ %d)",
                                pool, actual, MIN_POOL_SIZE)

            for pool, table_col in [("streets", "streets"), ("cities", "cities")]:
                cur.execute(
                    f"SELECT COUNT(*) AS n FROM {pool} WHERE locale=%s", (locale,)
                )
                actual = cur.fetchone()["n"]
                cur.execute(
                    "SELECT size FROM pool_sizes WHERE locale=%s AND pool=%s",
                    (locale, pool)
                )
                row = cur.fetchone()
                if row is None:
                    log.error("  pool_sizes missing: %s / %s", locale, pool)
                    ok = False
                elif row["size"] != actual:
                    log.error("  pool_sizes mismatch: %s / %s — pool_sizes=%d, actual=%d",
                              locale, pool, row["size"], actual)
                    ok = False
                else:
                    log.info("  ✓ %s: %d rows", pool, actual)

            # 2. idx gap check for names
            for pool in REQUIRED_NAME_POOLS:
                cur.execute("""
                    SELECT COUNT(*) FILTER (WHERE idx != rn) AS gaps
                    FROM (
                        SELECT idx, ROW_NUMBER() OVER (ORDER BY idx) AS rn
                        FROM names WHERE locale=%s AND kind=%s
                    ) t
                """, (locale, pool))
                gaps = cur.fetchone()["gaps"]
                if gaps > 0:
                    log.error("  idx gaps in names.%s: %d gaps found", pool, gaps)
                    ok = False
                else:
                    log.info("  ✓ names.%s idx is gap-free", pool)

            for tbl in ("streets", "cities"):
                cur.execute(f"""
                    SELECT COUNT(*) FILTER (WHERE idx != rn) AS gaps
                    FROM (
                        SELECT idx, ROW_NUMBER() OVER (ORDER BY idx) AS rn
                        FROM {tbl} WHERE locale=%s
                    ) t
                """, (locale,))
                gaps = cur.fetchone()["gaps"]
                if gaps > 0:
                    log.error("  idx gaps in %s: %d gaps found", tbl, gaps)
                    ok = False
                else:
                    log.info("  ✓ %s idx is gap-free", tbl)

            # 3. choice categories
            for cat in REQUIRED_CHOICE_CATS:
                cur.execute(
                    "SELECT COUNT(*) AS n FROM choices WHERE locale=%s AND category=%s",
                    (locale, cat)
                )
                n = cur.fetchone()["n"]
                if n == 0:
                    log.error("  Missing choices category: %s / %s", locale, cat)
                    ok = False
                else:
                    log.info("  ✓ choices.%s: %d entries", cat, n)

            # 4. cities postal sanity
            cur.execute(
                "SELECT COUNT(*) AS n FROM cities WHERE locale=%s AND postal_min > postal_max",
                (locale,)
            )
            bad = cur.fetchone()["n"]
            if bad > 0:
                log.error("  %d cities have postal_min > postal_max", bad)
                ok = False
            else:
                log.info("  ✓ city postal ranges OK")

            # 5. body_params
            for gender in REQUIRED_GENDERS:
                for attr in REQUIRED_BODY_ATTRS:
                    cur.execute(
                        "SELECT 1 FROM body_params WHERE locale=%s AND gender=%s AND attribute=%s",
                        (locale, gender, attr)
                    )
                    if not cur.fetchone():
                        log.error("  Missing body_params: %s / %s / %s", locale, gender, attr)
                        ok = False
                    else:
                        log.info("  ✓ body_params %s/%s/%s OK", locale, gender, attr)

    return ok


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        log.error("DATABASE_URL is not set.")
        sys.exit(1)

    try:
        conn = psycopg.connect(database_url, row_factory=dict_row)
    except Exception as exc:
        log.error("Connection failed: %s", exc)
        sys.exit(1)

    with conn:
        result = check(conn)
    conn.close()

    if result:
        log.info("=== All checks passed ===")
        sys.exit(0)
    else:
        log.error("=== Some checks FAILED — see above ===")
        sys.exit(1)


if __name__ == "__main__":
    main()

