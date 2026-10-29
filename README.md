# Fake User Generator

A web application that generates deterministic, reproducible fake user contact information.
**All data generation logic is implemented exclusively as PostgreSQL stored functions.**
Python (Flask) is used only to render HTML and read results from the database.

---

## Features

- **Two locales**: `en_US` (English/USA) and `de_DE` (German/Germany)
- **Deterministic**: identical `(locale, seed, batch, index)` always produces identical output
- **Six field groups**: full name, postal address, geolocation coordinates, physical attributes, phone number, email address
- **Large lookup pools**: ≥600 male names, ≥600 female names, ≥800 surnames, ≥600 streets, ≥120 cities per locale
- **Statistically correct**: Box-Muller normals for height/weight; sphere-uniform coordinates (not naive lat/lon uniform)
- **Optional**: Markov-chain text generation for bio fields

---

## Architecture

```
Browser ──GET ?locale=&seed=&batch=&size=──► Flask (app.py)
                                                │
                                          validates inputs
                                                │
                                    psycopg3 → PostgreSQL
                                                │
                          SELECT * FROM generate_users(locale, seed, batch, size)
                                                │
                              generate_user() for each i in [0, size)
                                    ├── rand_u32 / rand_normal / rand_sphere
                                    ├── pick_name / pick_city / pick_street / pick_choice
                                    └── fmt_name / fmt_address / fmt_phone / fmt_email
```

Python contains **zero** generation logic. All faking happens in the database.

---

## Repository Layout

```
Task6_PY/
├── app.py                    # Flask application
├── requirements.txt
├── .env.example              # Copy to .env
├── sql/
│   ├── 001_schema.sql        # Tables, composite type, constraints
│   ├── 002_data_en_US.sql    # en_US lookup data
│   ├── 003_data_de_DE.sql    # de_DE lookup data
│   ├── 010_rng.sql           # RNG layer (rand_u32, rand_uniform, rand_normal, rand_sphere)
│   ├── 020_pickers.sql       # Picker functions (pick_name, pick_city, ...)
│   ├── 030_formatters.sql    # Formatter functions (fmt_name, fmt_address, ...)
│   ├── 040_composer.sql      # generate_user — composes all fields
│   ├── 050_api.sql           # generate_users, list_locales, generate_text
│   └── 060_comments.sql      # COMMENT ON for every routine
├── scripts/
│   ├── apply_sql.py          # Idempotent SQL applicator
│   ├── check_data.py         # Data integrity verifier
│   └── load_markov.py        # Build Markov chain from corpus
├── tests/
│   ├── conftest.py           # Shared DB fixture
│   ├── test_rng.py           # RNG: reproducibility, sensitivity, normal, sphere
│   └── test_api.py           # API: reproducibility, formats, validation, golden
├── templates/
│   ├── index.html            # Main page
│   └── error.html            # Error page
└── docs/
    └── ROUTINES.md           # Comprehensive stored-function documentation
```

---

## Quick Start

### 1. Prerequisites

- PostgreSQL 14+ running locally (or connection string to hosted DB)
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

### 3. Create the database

```sql
-- In psql as superuser:
CREATE DATABASE faker_db;
CREATE USER faker WITH PASSWORD 'yourpassword';
GRANT ALL ON DATABASE faker_db TO faker;
```

### 4. Apply SQL

```bash
python scripts/apply_sql.py
```

This applies all `sql/*.sql` files in order. Safe to re-run (idempotent).

### 5. Verify data integrity

```bash
python scripts/check_data.py
```

### 6. Run the app

```bash
flask --app app run
# or
python app.py
```

Open http://localhost:5000

### 7. Run tests

```bash
pytest tests/ -v
```

---

## How It Works

### Deterministic RNG

All randomness derives from `md5(seed || ':' || locale || ':' || batch || ':' || i || ':' || field)`.

- **No `setseed()` or `random()`**: PostgreSQL's `random()` is not reproducible across calls in set-based queries.
- Each field uses a distinct label, so draws are independent.
- The `bit(32)::bigint` cast is sign-extended; adding 2³¹ shifts to unsigned [0, 2³²).

### Sphere-uniform Coordinates

Latitude must have `sin(lat)` uniformly distributed on `[-1, 1]`, not `lat` uniformly on `[-90°, 90°]`. The naive approach clusters points at the poles. The correct formula:

```
lat = degrees(asin(2*U - 1))
lon = 360*U - 180
```

This gives equal probability to equal areas on the sphere surface.

### Normal Distribution (Box-Muller)

```
Z = sqrt(-2 * ln(U₁)) * cos(2π * U₂)
result = mean + sd * Z
```

`U₁` and `U₂` are drawn at distinct field labels (`field#1`, `field#2`).

### Weighted Choice

The `choices` table assigns weights to each option. `pick_choice()` computes cumulative weights with `SUM() OVER (ORDER BY ord)`, then picks the first row where `cumulative_weight > rand_u32 % total_weight`.

---

## Adding a Locale

See [`docs/ROUTINES.md`](docs/ROUTINES.md) for the complete guide.

Brief summary:
1. Insert into `locales`
2. Insert names (first_male, first_female, last) with contiguous idx
3. Insert streets with contiguous idx
4. Insert cities with postal ranges and area codes
5. Insert all required `choices` categories
6. Insert `body_params` for male/female height/weight
7. Insert `translit` mappings for non-ASCII characters
8. Insert accurate `pool_sizes` rows
9. Run `python scripts/check_data.py`

---

## Data Sources

- US names: generated list; cross-referenced with common American given names and surnames
- German names: generated list; cross-referenced with common German names
- US cities/postal codes: based on actual USPS postal code assignments
- German cities/postal codes: based on actual Deutsche Post assignments
- US area codes: based on NANP allocations
- German area codes (Vorwahl): based on Bundesnetzagentur allocations

> **License note**: The lookup data in this project is a generated set of realistic-sounding names and place data, not derived from any copyrighted database.

---

## Deployment (Render)

1. Create a Render PostgreSQL database (free tier, note 30-day expiry)
2. Apply SQL: `DATABASE_URL=<external-url> python scripts/apply_sql.py`
3. Run golden tests against the deployed DB
4. Create a Render web service pointing to this repo
5. Set `DATABASE_URL` (internal URL) and `FLASK_SECRET_KEY` environment variables
6. Start command: `gunicorn app:app`

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `FLASK_ENV` | `development` or `production` | No |
| `FLASK_SECRET_KEY` | Flask session secret | Yes (production) |

