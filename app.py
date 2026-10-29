import os
import sys
import logging
from pathlib import Path
from typing import Optional
from flask import Flask, render_template, request, url_for, g
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

from constants.users import (
    DEFAULT_SIZE,
    MIN_SIZE,
    MAX_SIZE,
    DEFAULT_BATCH,
    MIN_BATCH,
    MAX_BATCH,
    DEFAULT_SEED,
    MIN_SEED,
    MAX_SEED,
)
from constants.text import (
    DEFAULT_WORDS,
    MIN_WORDS,
    MAX_WORDS,
)
from constants import DEFAULT_MODE, ALLOWED_MODES

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ["DATABASE_URL"]


def get_db() -> psycopg.Connection:
    if "db" not in g:
        g.db = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql: str, params: tuple = ()) -> list[dict]:
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def parse_int(value: str, default: int, min_val: int, max_val: int) -> tuple[int, Optional[str]]:
    try:
        n = int(value)
        if not (min_val <= n <= max_val):
            return default, f"Must be between {min_val} and {max_val} (got {n})"
        return n, None
    except (TypeError, ValueError):
        return default, f"Must be a valid integer (got {value!r})"


@app.route("/healthz")
def healthz():
    try:
        query("SELECT 1")
        return {"status": "ok"}, 200
    except Exception as exc:
        logger.error("Health check failed: %s", exc)
        return {"status": "error", "detail": str(exc)}, 503


@app.route("/")
def index():
    errors: dict[str, str] = {}

    try:
        locales = query("SELECT code, display_name FROM list_locales()")
    except Exception as exc:
        logger.exception("Failed to load locales")
        return render_template("error.html", message="Database error loading locales. Is the schema applied?"), 500

    if not locales:
        return render_template("error.html", message="No locales found. Run scripts/apply_sql.py first."), 500

    default_locale = locales[0]["code"]

    mode = request.args.get("mode", DEFAULT_MODE)
    if mode not in ALLOWED_MODES:
        mode = DEFAULT_MODE

    locale = request.args.get("locale", default_locale)
    if not any(l["code"] == locale for l in locales):
        errors["locale"] = f"Unknown locale: {locale!r}"
        locale = default_locale

    raw_seed = request.args.get("seed", str(DEFAULT_SEED))
    raw_batch = request.args.get("batch", str(DEFAULT_BATCH))
    raw_size = request.args.get("size", str(DEFAULT_SIZE))
    raw_words = request.args.get("words", str(DEFAULT_WORDS))

    seed, e = parse_int(raw_seed, DEFAULT_SEED, MIN_SEED, MAX_SEED)
    if e:
        errors["seed"] = e

    batch, e = parse_int(raw_batch, DEFAULT_BATCH, MIN_BATCH, MAX_BATCH)
    if e:
        errors["batch"] = e

    size, e = parse_int(raw_size, DEFAULT_SIZE, MIN_SIZE, MAX_SIZE)
    if e:
        errors["size"] = e

    words, e = parse_int(raw_words, DEFAULT_WORDS, MIN_WORDS, MAX_WORDS)
    if e:
        errors["words"] = e

    users = []
    generated_text = None
    db_error = None

    if not errors:
        if mode == "users":
            try:
                users = query(
                    "SELECT * FROM generate_users(%s::text, %s::bigint, %s::int, %s::int)",
                    (locale, seed, batch, size),
                )
            except psycopg.errors.InvalidParameterValue as exc:
                db_error = str(exc).split("\n")[0]
                logger.warning("generate_users validation error: %s", exc)
            except Exception as exc:
                logger.exception("generate_users failed")
                db_error = "Unexpected database error. Check server logs."
        elif mode == "text":
            try:
                rows = query(
                    "SELECT generate_text(%s::text, %s::bigint, %s::int, 0, %s::int) AS txt",
                    (locale, seed, batch, words),
                )
                if rows and rows[0]["txt"]:
                    generated_text = rows[0]["txt"]
                else:
                    db_error = f"No Markov bigram data found for locale '{locale}'. Load corpus first."
            except psycopg.errors.InvalidParameterValue as exc:
                db_error = str(exc).split("\n")[0]
                logger.warning("generate_text validation error: %s", exc)
            except Exception as exc:
                logger.exception("generate_text failed")
                db_error = "Unexpected database error. Check server logs."

    prev_batch = max(0, batch - 1) if batch > 0 else None
    next_batch = batch + 1 if batch < MAX_BATCH else None

    def nav_url(b):
        return url_for("index", mode=mode, locale=locale, seed=seed, batch=b, size=size, words=words)

    return render_template(
        "index.html",
        mode=mode,
        locales=locales,
        locale=locale,
        seed=seed,
        batch=batch,
        size=size,
        words=words,
        users=users,
        generated_text=generated_text,
        errors=errors,
        db_error=db_error,
        prev_url=nav_url(prev_batch) if prev_batch is not None else None,
        next_url=nav_url(next_batch) if next_batch is not None else None,
    )


@app.route("/docs")
def docs():
    doc_file = BASE_DIR / "docs" / "ROUTINES.md"
    content = doc_file.read_text(encoding="utf-8") if doc_file.exists() else "# Documentation not found"
    return render_template("docs.html", content=content)


@app.errorhandler(404)
def not_found(exc):
    return render_template("error.html", message="Page not found."), 404


@app.errorhandler(500)
def server_error(exc):
    logger.exception("Unhandled error")
    return render_template("error.html", message="Internal server error. Check server logs."), 500


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_ENV") == "development")
