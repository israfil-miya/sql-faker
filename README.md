# Fake User Generator

A web application that generates deterministic, reproducible fake user contact information.
All data generation logic is implemented exclusively as PostgreSQL stored functions.
Python and Flask serve only to render HTML and read results from the database.

---

## Features

- Two locales: `en_US` (English/USA) and `de_DE` (German/Germany)
- Deterministic: identical `(locale, seed, batch, index)` always produces identical output
- Six field groups: full name, postal address, geolocation coordinates, physical attributes, phone number, email address
- Large lookup pools: at least 600 male names, 600 female names, 800 surnames, 600 streets, 120 cities per locale
- Correct distributions: Box-Muller normals for height and weight, sphere-uniform coordinates
- Markov text generator: bigram natural language text generation in the requested locale

---

## Architecture

```
Browser -> GET ?locale=&seed=&batch=&size= -> Flask (app.py)
                                                |
                                          validates inputs
                                                |
                                    psycopg3 -> PostgreSQL
                                                |
                          SELECT * FROM generate_users(locale, seed, batch, size)
                                                |
                               generate_user() for each row i
                                    |-- rand_u32 / rand_normal / rand_sphere
                                    |-- pick_name / pick_city / pick_street / pick_choice
                                    \-- fmt_name / fmt_address / fmt_phone / fmt_email
```

Python contains zero generation logic. All faking happens in the database.

---

## Repository Layout

```
Task6_PY/
|-- app.py                    # Flask application
|-- requirements.txt
|-- .env.example              # Environment template
|-- constants/                # Topic-wise configuration limits
|   |-- users.py
|   \-- text.py
|-- static/                   # Static CSS and JS assets
|   |-- css/style.css
|   \-- js/main.js
|-- sql/
|   |-- 001_schema.sql        # Tables, composite type, constraints
|   |-- 002_data_en_US.sql    # en_US lookup data
|   |-- 003_data_de_DE.sql    # de_DE lookup data
|   |-- 010_rng.sql           # RNG layer (rand_u32, rand_uniform, rand_normal, rand_sphere)
|   |-- 020_pickers.sql       # Picker functions (pick_name, pick_city, ...)
|   |-- 030_formatters.sql    # Formatter functions (fmt_name, fmt_address, ...)
|   |-- 040_composer.sql      # generate_user: composes all fields
|   |-- 050_api.sql           # generate_users, list_locales, generate_text
|   \-- 060_comments.sql      # COMMENT ON statements
|-- scripts/
|   |-- apply_sql.py          # Idempotent SQL applicator
|   |-- check_data.py         # Data integrity verifier
|   |-- benchmark.py          # Performance benchmark runner
|   \-- load_markov.py        # Build Markov chain from corpus
|-- tests/
|   |-- conftest.py           # Shared DB fixture
|   |-- test_rng.py           # RNG tests
|   |-- test_api.py           # API tests
|   \-- test_markov.py        # Markov text tests
|-- templates/
|   |-- index.html            # Main toolbar and container page
|   |-- users_view.html       # Users table view component
|   |-- text_view.html        # Markov text preview component
|   |-- docs.html             # Stored procedures documentation viewer
|   \-- error.html            # Error page
\-- docs/
    \-- ROUTINES.md           # Stored procedure documentation
```

---

## Quick Start

### 1. Prerequisites

- PostgreSQL 14+ running locally or hosted
- Python 3.11+

### 2. Setup

```bash
cd Task6_PY

# Install Python dependencies
pip install -r requirements.txt

# Configure database
cp .env.example .env
# Edit .env and set DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### 3. Create Database

```sql
CREATE DATABASE faker_db
CREATE USER faker WITH PASSWORD 'db_password'
GRANT ALL ON DATABASE faker_db TO faker
```

### 4. Apply SQL

```bash
python scripts/apply_sql.py
```

This applies all `sql/*.sql` files in order. Safe to re-run.

### 5. Verify Data Integrity

```bash
python scripts/check_data.py
```

### 6. Run Application

```bash
python app.py
```

Open http://localhost:5000

### 7. Run Tests

```bash
python -m pytest tests/ -v
```

---

## How It Works

### Deterministic RNG

Randomness derives from an MD5 hash of `(seed, locale, batch, index, field)`.

- No `setseed()` or `random()`: PostgreSQL `random()` is not reproducible across calls in set-based queries.
- Each field uses a distinct label, ensuring draws are independent.
- The 32-bit integer is mapped uniformly to `[0, 2^32 - 1]`.

### Sphere-Uniform Coordinates

Latitude has `sin(lat)` uniformly distributed on `[-1, 1]` rather than `lat` uniformly on `[-90, 90]`. A naive approach clusters points at the poles. The used formula:

```
lat = degrees(asin(2*U - 1))
lon = 360*U - 180
```

This distributes points evenly across the surface area of the globe.

### Normal Distribution (Box-Muller)

Heights and weights follow Gaussian distributions:

```
Z = sqrt(-2 * ln(U1)) * cos(2 * pi * U2)
result = mean + sd * Z
```

`U1` and `U2` are drawn at distinct field labels (`field#1`, `field#2`).

### Weighted Choice

The `choices` table assigns weights to options. `pick_choice()` computes cumulative weights with `SUM() OVER (ORDER BY ord)` and selects the option matching a random threshold.

---

## Adding a Locale

See [`docs/ROUTINES.md`](docs/ROUTINES.md) for full details.

Brief summary:
1. Insert into `locales`
2. Insert names (first_male, first_female, last) with contiguous indices
3. Insert streets with contiguous indices
4. Insert cities with postal ranges and area codes
5. Insert required `choices` categories
6. Insert `body_params` for male and female height and weight
7. Insert `translit` mappings for non-ASCII characters
8. Insert accurate `pool_sizes` rows
9. Run `python scripts/check_data.py`

---

## Deployment (Render)

1. Create a Render PostgreSQL database
2. Apply SQL: `DATABASE_URL=<external-url> python scripts/apply_sql.py`
3. Create a Render web service pointing to the repository
4. Set `DATABASE_URL` (internal URL) and `FLASK_SECRET_KEY` environment variables
5. Start command: `gunicorn app:app`

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `FLASK_ENV` | `development` or `production` | No |
| `FLASK_SECRET_KEY` | Flask session secret | Yes in production |
