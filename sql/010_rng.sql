-- =============================================================================
-- 010_rng.sql  — Deterministic RNG layer
--
-- All functions are IMMUTABLE: they read no tables and have no side-effects.
-- Randomness comes exclusively from md5() applied to a structured key:
--   key = seed || ':' || locale || ':' || batch || ':' || i || ':' || field
-- This ensures full independence between fields (different 'field' labels)
-- and full reproducibility (identical inputs → identical outputs).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- rand_u32
-- Returns a pseudo-random unsigned 32-bit integer in [0, 2^32).
--
-- Algorithm:
--   1. Build the key string: seed:locale:batch:i:field
--   2. md5(key) → 32 hex characters
--   3. Take the first 8 hex chars → 32-bit hex number
--   4. Cast via bit(32) to bigint.  PostgreSQL bit(n)::bigint is a
--      zero-extending cast, giving the range [0, 2^32) directly.
--
-- Arguments:
--   p_seed   bigint  — caller-supplied seed (any integer)
--   p_locale text    — locale code (e.g. 'en_US')
--   p_batch  int     — batch index (≥ 0)
--   p_i      int     — position within batch (0-based)
--   p_field  text    — field discriminator (e.g. 'first_name', 'lat#1')
--
-- Returns: bigint in [0, 2^32)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION rand_u32(
    p_seed   bigint,
    p_locale text,
    p_batch  int,
    p_i      int,
    p_field  text
) RETURNS bigint
LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE AS $$
    SELECT ('x' || substr(
        md5(p_seed::text || ':' || p_locale || ':' ||
            p_batch::text || ':' || p_i::text || ':' || p_field),
        1, 8
    ))::bit(32)::bigint
$$;

-- ---------------------------------------------------------------------------
-- rand_int
-- Returns a pseudo-random integer in [0, p_n).
--
-- Algorithm: rand_u32 modulo p_n.
-- Modulo bias is negligible when p_n << 2^32 (all pool sizes are < 10^6).
--
-- Arguments: same as rand_u32 plus
--   p_n  int  — upper bound (exclusive), must be > 0
--
-- Returns: int in [0, p_n)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION rand_int(
    p_seed   bigint,
    p_locale text,
    p_batch  int,
    p_i      int,
    p_field  text,
    p_n      int
) RETURNS int
LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE AS $$
    SELECT (rand_u32(p_seed, p_locale, p_batch, p_i, p_field) % p_n)::int
$$;

-- ---------------------------------------------------------------------------
-- rand_uniform
-- Returns a pseudo-random float in (0, 1) (open interval — never 0 or 1).
--
-- Algorithm: (rand_u32 + 0.5) / 2^32
-- The +0.5 shift ensures the result is never exactly 0, which matters for
-- logarithms in Box-Muller.
--
-- Returns: float8 in (0, 1)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION rand_uniform(
    p_seed   bigint,
    p_locale text,
    p_batch  int,
    p_i      int,
    p_field  text
) RETURNS float8
LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE AS $$
    SELECT (rand_u32(p_seed, p_locale, p_batch, p_i, p_field) + 0.5) / 4294967296.0
$$;

-- ---------------------------------------------------------------------------
-- rand_normal
-- Returns a normally-distributed float with given mean and standard deviation.
--
-- Algorithm: Box-Muller transform (standard form)
--   U1 = rand_uniform(..., p_field || '#1')   — strictly in (0,1)
--   U2 = rand_uniform(..., p_field || '#2')   — strictly in (0,1)
--   Z  = sqrt(-2 * ln(U1)) * cos(2π * U2)
--   result = p_mean + p_sd * Z
--
-- The two uniform draws use distinct field labels ('#1', '#2') so they are
-- independent from each other and from every other field.
--
-- Arguments:
--   p_mean  float8  — target mean
--   p_sd    float8  — target standard deviation (> 0)
--
-- Returns: float8 (unbounded; callers should clamp to [min_val, max_val])
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION rand_normal(
    p_seed   bigint,
    p_locale text,
    p_batch  int,
    p_i      int,
    p_field  text,
    p_mean   float8,
    p_sd     float8
) RETURNS float8
LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE AS $$
    SELECT p_mean + p_sd *
        sqrt(-2.0 * ln(rand_uniform(p_seed, p_locale, p_batch, p_i, p_field || '#1'))) *
        cos(2.0 * pi() * rand_uniform(p_seed, p_locale, p_batch, p_i, p_field || '#2'))
$$;

-- ---------------------------------------------------------------------------
-- rand_sphere
-- Returns a uniformly-distributed point on the sphere as (latitude, longitude).
--
-- Naive approach (WRONG): generate lat ∈ [-90, 90] and lon ∈ [-180, 180]
-- uniformly as floats.  This clusters points near the poles because equal
-- latitude intervals cover unequal areas.
--
-- Correct approach: sin(lat) must be uniform on [-1, 1].
--   U1 = rand_uniform(... 'lat')  → sin(lat) = 2*U1 - 1
--   lat = degrees(asin(2*U1 - 1))
--   U2 = rand_uniform(... 'lon')
--   lon = 360*U2 - 180
--
-- This guarantees equal areas correspond to equal probability, i.e. a
-- constant probability density function on the sphere surface.
--
-- Returns: TABLE(lat float8, lon float8) with lat ∈ [-90,90], lon ∈ [-180,180]
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION rand_sphere(
    p_seed   bigint,
    p_locale text,
    p_batch  int,
    p_i      int,
    p_field  text
) RETURNS TABLE(lat float8, lon float8)
LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE AS $$
    SELECT
        -- Clamp to [-1,1] before asin() to guard against float8 rounding
        -- when rand_uniform() is extremely close to 0 or 1.
        degrees(asin(GREATEST(-1.0::float8, LEAST(1.0::float8,
            2.0 * rand_uniform(p_seed, p_locale, p_batch, p_i, p_field || '_lat') - 1.0
        )))),
        360.0 * rand_uniform(p_seed, p_locale, p_batch, p_i, p_field || '_lon') - 180.0
$$;

