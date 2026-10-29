-- =============================================================================
-- 060_comments.sql  — COMMENT ON for all routines and tables
-- These appear in psql \df+ and \d+ output.
-- =============================================================================

-- Tables
COMMENT ON TABLE locales     IS 'Available locales for the fake user generator.';
COMMENT ON TABLE names       IS 'First and last name pools per locale. kind: first_male | first_female | last. idx is 1-based and contiguous.';
COMMENT ON TABLE streets     IS 'Street base name pool per locale. idx is 1-based and contiguous.';
COMMENT ON TABLE cities      IS 'City pool per locale with postal code range and phone area code for coherent address+phone generation.';
COMMENT ON TABLE choices     IS 'Generic weighted-choice table. Covers titles, templates, eye colors, phone/email patterns. Adding a category requires no DDL.';
COMMENT ON TABLE body_params IS 'Normal distribution parameters (mean, sd, clamp range) for physical attributes by locale and gender.';
COMMENT ON TABLE translit    IS 'Character substitution map for folding locale-specific chars to ASCII for email generation.';
COMMENT ON TABLE pool_sizes  IS 'Cached pool sizes used by pickers to compute idx = rand % size + 1. Must match actual table counts.';
COMMENT ON TABLE markov      IS 'Bigram Markov chain weights for deterministic natural-language text generation.';

-- RNG layer
COMMENT ON FUNCTION rand_u32(bigint, text, int, int, text) IS
'Returns a pseudo-random unsigned 32-bit integer in [0, 2^32).
Algorithm: md5(seed:locale:batch:i:field) → first 8 hex chars → bit(32)::bigint.
The bit(32)→bigint cast in PostgreSQL is zero-extending, giving [0, 2^32) directly.
IMMUTABLE: no table reads, pure hash function.';

COMMENT ON FUNCTION rand_int(bigint, text, int, int, text, int) IS
'Returns a pseudo-random integer in [0, n).
Algorithm: rand_u32 mod n. Modulo bias negligible for n << 2^32.
IMMUTABLE.';

COMMENT ON FUNCTION rand_uniform(bigint, text, int, int, text) IS
'Returns a pseudo-random float in the open interval (0, 1).
Algorithm: (rand_u32 + 0.5) / 2^32. The +0.5 prevents exactly 0, safe for ln().
IMMUTABLE.';

COMMENT ON FUNCTION rand_normal(bigint, text, int, int, text, float8, float8) IS
'Returns a normally distributed float with given mean and standard deviation.
Algorithm: Box-Muller transform using two independent uniforms at labels field#1, field#2.
Z = sqrt(-2 ln U1) * cos(2π U2), result = mean + sd * Z.
IMMUTABLE. Callers should clamp to [min_val, max_val].';

COMMENT ON FUNCTION rand_sphere(bigint, text, int, int, text) IS
'Returns a point (lat, lon) uniformly distributed on the sphere.
Algorithm: sin(lat) is uniform on [-1,1], so lat = degrees(asin(2*U1-1)).
lon = 360*U2 - 180. Naive uniform lat gives E[sin²(lat)]=0.5; correct gives 1/3.
IMMUTABLE.';

-- Pickers
COMMENT ON FUNCTION pick_name(text, text, bigint, int, int, text) IS
'Picks a name from the names table using rand_u32 mod pool_size + 1.
STABLE (reads tables). p_kind: first_male | first_female | last.';

COMMENT ON FUNCTION pick_city(text, bigint, int, int, text) IS
'Picks a city row (city, region, postal_min, postal_max, area_code) from the cities table.
STABLE.';

COMMENT ON FUNCTION pick_street(text, bigint, int, int, text) IS
'Picks a street base name from the streets table. STABLE.';

COMMENT ON FUNCTION pick_choice(text, text, bigint, int, int, text) IS
'Weighted roulette-wheel selection from the choices table.
Algorithm: computes cumulative weights with a window function; picks first row
where cum_weight > rand_u32 % total_weight. STABLE.';

-- Formatters
COMMENT ON FUNCTION apply_translit(text, text) IS
'Replaces characters in p_input using the translit table for the given locale.
Applied longest-match-first. Used to fold names to ASCII for email generation.
STABLE (reads translit table).';

COMMENT ON FUNCTION fmt_name(text, text, text, text, text) IS
'Fills a name template with title, first, middle, last components.
Supported placeholders: {title} {first} {mi} {middle} {last}.
Collapses multiple spaces. IMMUTABLE.';

COMMENT ON FUNCTION fmt_address(text, text, text, text, text, text, text) IS
'Fills an address template with num, street, unit, city, region, postal.
Supports US and DE templates. Collapses multiple spaces. IMMUTABLE.';

COMMENT ON FUNCTION fmt_phone(text, text, bigint, text, int, int, text) IS
'Replaces # placeholders with random digits and {area} with the area code.
US templates use 555-01xx (NANP fictional range). IMMUTABLE.';

COMMENT ON FUNCTION fmt_email(text, text, text, bigint, int, int, text) IS
'Generates an email: transliterates name to ASCII, lowercases, applies separator
and optional numeric suffix from choices tables, picks domain from choices.
STABLE (reads translit and choices).';

-- Composer
COMMENT ON FUNCTION generate_user(text, bigint, int, int) IS
'Generates one complete fake_user record. Calls all pickers and formatters.
Each field uses a distinct p_field label for independence. STABLE.
Determinism: output is a pure function of (locale, seed, batch, i).';

-- API
COMMENT ON FUNCTION list_locales() IS
'Returns (code, display_name) for all available locales. Use for UI dropdowns. STABLE.';

COMMENT ON FUNCTION generate_users(text, bigint, int, int) IS
'Main entry point for the application. Validates all inputs (raises SQLSTATE 22023
on failure) then calls generate_user() for each index in [0, size).
Uses generate_series + LATERAL for set-based evaluation. STABLE.';

COMMENT ON FUNCTION generate_text(text, bigint, int, int, int) IS
'Generates deterministic pseudo-natural text using a bigram Markov chain.
Starts from <START> sentinel, walks chain using weighted picks at each step.
Dead ends restart from <START>. Returns p_n_words words joined as a paragraph. STABLE.';

