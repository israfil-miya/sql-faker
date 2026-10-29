"""
conftest.py — shared pytest fixtures for database tests.
"""
import os
import pytest
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="session")
def db():
    """Session-scoped database connection with autocommit.
    Using autocommit means each statement runs in its own implicit transaction.
    A failed statement does NOT leave the connection in an aborted state,
    so subsequent tests are not affected.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set — skipping DB tests")
    conn = psycopg.connect(url, row_factory=dict_row, autocommit=True)
    yield conn
    conn.close()


def query(conn, sql, params=()):
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def scalar(conn, sql, params=()):
    rows = query(conn, sql, params)
    return rows[0][list(rows[0].keys())[0]] if rows else None

