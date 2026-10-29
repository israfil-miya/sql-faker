-- =============================================================================
-- 001_schema.sql  — database schema
-- Fake-User Generator
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Extension
-- ---------------------------------------------------------------------------
-- We do NOT use pgcrypto/unaccent so the schema works on managed hosts
-- without superuser. md5() is a built-in.

-- ---------------------------------------------------------------------------
-- Drop order (reverse dependency)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS pool_sizes   CASCADE;
DROP TABLE IF EXISTS translit     CASCADE;
DROP TABLE IF EXISTS body_params  CASCADE;
DROP TABLE IF EXISTS choices      CASCADE;
DROP TABLE IF EXISTS cities       CASCADE;
DROP TABLE IF EXISTS streets      CASCADE;
DROP TABLE IF EXISTS names        CASCADE;
DROP TABLE IF EXISTS markov       CASCADE;
DROP TABLE IF EXISTS locales      CASCADE;
DROP TYPE  IF EXISTS fake_user    CASCADE;

-- ---------------------------------------------------------------------------
-- locales
-- ---------------------------------------------------------------------------
CREATE TABLE locales (
    code         text PRIMARY KEY,          -- e.g. 'en_US'
    display_name text NOT NULL,             -- shown in UI dropdown
    country_name text NOT NULL              -- used in address templates
);

-- ---------------------------------------------------------------------------
-- names  — first (male/female) and last names, per locale
-- kind: first_male | first_female | last
-- idx: 1-based contiguous integer, for modulo-pick
-- ---------------------------------------------------------------------------
CREATE TABLE names (
    locale text NOT NULL REFERENCES locales(code),
    kind   text NOT NULL CHECK (kind IN ('first_male','first_female','last')),
    idx    int  NOT NULL CHECK (idx >= 1),
    value  text NOT NULL,
    PRIMARY KEY (locale, kind, idx)
);

-- ---------------------------------------------------------------------------
-- streets  — street names per locale
-- ---------------------------------------------------------------------------
CREATE TABLE streets (
    locale text NOT NULL REFERENCES locales(code),
    idx    int  NOT NULL CHECK (idx >= 1),
    name   text NOT NULL,
    PRIMARY KEY (locale, idx)
);

-- ---------------------------------------------------------------------------
-- cities  — cities with enough metadata to make address+phone coherent
-- postal_min/max are integers; the formatter zero-pads as needed.
-- area_code is used by phone formatter.
-- ---------------------------------------------------------------------------
CREATE TABLE cities (
    locale     text NOT NULL REFERENCES locales(code),
    idx        int  NOT NULL CHECK (idx >= 1),
    city       text NOT NULL,
    region     text NOT NULL,   -- state (US) or Bundesland (DE)
    postal_min int  NOT NULL,
    postal_max int  NOT NULL,
    area_code  text NOT NULL,   -- digits only, no formatting
    PRIMARY KEY (locale, idx)
);

-- ---------------------------------------------------------------------------
-- choices  — generic weighted-pick table
-- Covers: titles, eye_colors, name_templates, address_templates,
--         phone_templates, email_domains, street_types, name_suffixes
-- weight is relative (need not sum to 1).
-- ord is the sort key used when computing cumulative weights.
-- ---------------------------------------------------------------------------
CREATE TABLE choices (
    locale   text NOT NULL REFERENCES locales(code),
    category text NOT NULL,
    ord      int  NOT NULL,
    value    text NOT NULL,
    weight   numeric NOT NULL CHECK (weight > 0),
    PRIMARY KEY (locale, category, ord)
);

-- ---------------------------------------------------------------------------
-- body_params  — normal-distribution parameters for physical attributes
-- gender: 'male' | 'female'
-- attribute: 'height_cm' | 'weight_kg' | ...
-- ---------------------------------------------------------------------------
CREATE TABLE body_params (
    locale    text    NOT NULL REFERENCES locales(code),
    gender    text    NOT NULL CHECK (gender IN ('male','female')),
    attribute text    NOT NULL,
    mean      float8  NOT NULL,
    sd        float8  NOT NULL CHECK (sd > 0),
    min_val   float8  NOT NULL,
    max_val   float8  NOT NULL,
    PRIMARY KEY (locale, gender, attribute)
);

-- ---------------------------------------------------------------------------
-- translit  — character substitutions for ASCII-safe email generation
-- from_str → to_str, applied in order of length desc then from_str asc
-- ---------------------------------------------------------------------------
CREATE TABLE translit (
    locale   text NOT NULL REFERENCES locales(code),
    from_str text NOT NULL,
    to_str   text NOT NULL,
    PRIMARY KEY (locale, from_str)
);

-- ---------------------------------------------------------------------------
-- pool_sizes  — cached count of each pool (maintained by data loader)
-- Verified by check_data.py
-- ---------------------------------------------------------------------------
CREATE TABLE pool_sizes (
    locale text NOT NULL REFERENCES locales(code),
    pool   text NOT NULL,   -- 'first_male', 'first_female', 'last', 'streets', 'cities'
    size   int  NOT NULL CHECK (size >= 1),
    PRIMARY KEY (locale, pool)
);

-- ---------------------------------------------------------------------------
-- markov  — bigram model for text generation (optional phase)
-- ---------------------------------------------------------------------------
CREATE TABLE markov (
    locale    text    NOT NULL REFERENCES locales(code),
    w1        text    NOT NULL,
    w2        text    NOT NULL,
    next_word text    NOT NULL,
    weight    int     NOT NULL DEFAULT 1 CHECK (weight > 0),
    PRIMARY KEY (locale, w1, w2, next_word)
);

-- ---------------------------------------------------------------------------
-- fake_user composite type  — output of generate_user()
-- ---------------------------------------------------------------------------
CREATE TYPE fake_user AS (
    full_name  text,
    address    text,
    latitude   float8,
    longitude  float8,
    height_cm  numeric,
    weight_kg  numeric,
    eye_color  text,
    phone      text,
    email      text
);

-- ---------------------------------------------------------------------------
-- Indexes  (covering common access patterns)
-- ---------------------------------------------------------------------------
CREATE INDEX idx_names_locale_kind ON names (locale, kind);
CREATE INDEX idx_streets_locale    ON streets (locale);
CREATE INDEX idx_cities_locale     ON cities (locale);
CREATE INDEX idx_choices_lc        ON choices (locale, category);
CREATE INDEX idx_markov_bigram     ON markov (locale, w1, w2);

