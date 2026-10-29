-- =============================================================================
-- 020_pickers.sql  — Table-reading picker functions
--
-- All functions are STABLE: they read tables but produce the same result
-- within a single transaction.  They must NOT be IMMUTABLE because a data
-- reload could change pool contents.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- pick_name
-- Pick a single name value from the names table.
--
-- Algorithm:
--   1. Look up pool size from pool_sizes (e.g. pool = 'first_male').
--   2. Compute 1-based idx = rand_int(...) % size + 1.
--   3. Return names.value WHERE locale = p_locale AND kind = p_kind AND idx = computed_idx.
--
-- Arguments:
--   p_locale  text    — locale code
--   p_kind    text    — 'first_male', 'first_female', or 'last'
--   p_seed    bigint  — RNG seed
--   p_batch   int     — batch index
--   p_i       int     — position within batch
--   p_field   text    — field discriminator (e.g. 'first_name')
--
-- Returns: text — the picked name value
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION pick_name(
    p_locale text,
    p_kind   text,
    p_seed   bigint,
    p_batch  int,
    p_i      int,
    p_field  text
) RETURNS text
LANGUAGE sql STABLE STRICT PARALLEL SAFE AS $$
    SELECT n.value
    FROM pool_sizes ps
    JOIN names n ON n.locale = p_locale
                 AND n.kind  = p_kind
                 AND n.idx   = (rand_u32(p_seed, p_locale, p_batch, p_i, p_field) % ps.size + 1)::int
    WHERE ps.locale = p_locale AND ps.pool = p_kind
    LIMIT 1
$$;

-- ---------------------------------------------------------------------------
-- pick_city
-- Pick a city row from the cities table.
--
-- Returns: TABLE(city text, region text, postal_min int, postal_max int, area_code text)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION pick_city(
    p_locale text,
    p_seed   bigint,
    p_batch  int,
    p_i      int,
    p_field  text
) RETURNS TABLE(city text, region text, postal_min int, postal_max int, area_code text)
LANGUAGE sql STABLE STRICT PARALLEL SAFE AS $$
    SELECT c.city, c.region, c.postal_min, c.postal_max, c.area_code
    FROM pool_sizes ps
    JOIN cities c ON c.locale = p_locale
                  AND c.idx   = (rand_u32(p_seed, p_locale, p_batch, p_i, p_field) % ps.size + 1)::int
    WHERE ps.locale = p_locale AND ps.pool = 'cities'
    LIMIT 1
$$;

-- ---------------------------------------------------------------------------
-- pick_street
-- Pick a street name from the streets table.
--
-- Returns: text
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION pick_street(
    p_locale text,
    p_seed   bigint,
    p_batch  int,
    p_i      int,
    p_field  text
) RETURNS text
LANGUAGE sql STABLE STRICT PARALLEL SAFE AS $$
    SELECT s.name
    FROM pool_sizes ps
    JOIN streets s ON s.locale = p_locale
                   AND s.idx   = (rand_u32(p_seed, p_locale, p_batch, p_i, p_field) % ps.size + 1)::int
    WHERE ps.locale = p_locale AND ps.pool = 'streets'
    LIMIT 1
$$;

-- ---------------------------------------------------------------------------
-- pick_choice
-- Weighted random pick from the choices table for a given (locale, category).
--
-- Algorithm (cumulative-weight method):
--   1. Assign each row a cumulative weight = SUM(weight) OVER (ORDER BY ord).
--   2. total = SUM(weight) across the category.
--   3. r = rand_u32(...) % total  (integer in [0, total)).
--   4. Return the value of the first row whose cumulative weight > r.
--
-- This is equivalent to roulette-wheel selection. Using integer weights avoids
-- floating-point rounding. The modulo bias is negligible because total << 2^32.
--
-- Arguments:
--   p_locale    text    — locale code
--   p_category  text    — category name (e.g. 'eye_color', 'title_male')
--   p_seed      bigint  — RNG seed
--   p_batch     int     — batch index
--   p_i         int     — position within batch
--   p_field     text    — field discriminator
--
-- Returns: text — the picked value
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION pick_choice(
    p_locale    text,
    p_category  text,
    p_seed      bigint,
    p_batch     int,
    p_i         int,
    p_field     text
) RETURNS text
LANGUAGE sql STABLE STRICT PARALLEL SAFE AS $$
    WITH weighted AS (
        SELECT
            value,
            SUM(weight::bigint) OVER (ORDER BY ord ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_w,
            SUM(weight::bigint) OVER ()                                                               AS total_w
        FROM choices
        WHERE locale = p_locale AND category = p_category
    )
    SELECT value
    FROM weighted
    WHERE cum_w > rand_u32(p_seed, p_locale, p_batch, p_i, p_field) % total_w
    ORDER BY cum_w
    LIMIT 1
$$;

