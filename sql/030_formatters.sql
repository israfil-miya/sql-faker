-- =============================================================================
-- 030_formatters.sql  — String-formatting functions
--
-- These functions assemble the final text fields.  They are STABLE (some read
-- tables for transliteration).  All formatting is deterministic given inputs.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- apply_translit
-- Replace multi-character sequences according to the translit table.
-- Applied in order: longer from_str first, then alphabetically.
-- Used to fold locale-specific characters to ASCII for email generation.
--
-- Algorithm: iterates over translit rows (longest match first) applying
-- regexp_replace for each mapping.  PL/pgSQL loop because SQL lacks
-- ordered sequential substitution.
--
-- Arguments:
--   p_locale  text  — locale code
--   p_input   text  — string to transliterate
--
-- Returns: text — ASCII-safe version of the input
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION apply_translit(
    p_locale text,
    p_input  text
) RETURNS text
LANGUAGE plpgsql STABLE STRICT PARALLEL SAFE AS $$
DECLARE
    v_result text := p_input;
    v_row    record;
BEGIN
    FOR v_row IN
        SELECT from_str, to_str
        FROM translit
        WHERE locale = p_locale
        ORDER BY length(from_str) DESC, from_str
    LOOP
        v_result := replace(v_result, v_row.from_str, v_row.to_str);
    END LOOP;
    RETURN v_result;
END;
$$;

-- ---------------------------------------------------------------------------
-- fmt_name
-- Format a full name by filling a template and cleaning up whitespace.
--
-- Supported template placeholders:
--   {title}  — honorific (e.g. "Mr.", "Dr.")
--   {first}  — first name
--   {mi}     — first letter of first name (middle initial)
--   {middle} — middle name
--   {last}   — last name
--
-- After substitution, sequences of multiple spaces are collapsed to one,
-- and leading/trailing spaces are trimmed.
--
-- Example templates:
--   '{first} {last}'               → 'John Smith'
--   '{title} {first} {last}'       → 'Mr. John Smith'
--   '{first} {mi}. {last}'         → 'John D. Smith'   (mi from middle name)
--   '{title} {first} {middle} {last}' → 'Dr. John David Smith'
--
-- Arguments:
--   p_title   text  — honorific or empty string
--   p_first   text  — first name
--   p_middle  text  — middle name (may be empty)
--   p_last    text  — last name
--   p_tmpl    text  — template string
--
-- Returns: text — formatted full name
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fmt_name(
    p_title  text,
    p_first  text,
    p_middle text,
    p_last   text,
    p_tmpl   text
) RETURNS text
LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE AS $$
    SELECT trim(regexp_replace(
        replace(replace(replace(replace(replace(
            p_tmpl,
            '{title}',  p_title),
            '{first}',  p_first),
            '{mi}',     left(p_middle, 1)),
            '{middle}', p_middle),
            '{last}',   p_last),
        '\s{2,}', ' ', 'g'
    ))
$$;

-- ---------------------------------------------------------------------------
-- fmt_address
-- Format a postal address from components using a locale-specific template.
--
-- Supported template placeholders:
--   {num}    — street number (integer as text)
--   {street} — street name (may include type suffix like "Ave", "Str.")
--   {unit}   — apartment/unit (may be empty)
--   {city}   — city name
--   {region} — state/Bundesland abbreviation or name
--   {postal} — postal code (zero-padded for DE)
--
-- US template examples:
--   '{num} {street}, {city}, {region} {postal}'
--   '{num} {street}, Apt {unit}, {city}, {region} {postal}'
-- DE template examples:
--   '{street} {num}, {postal} {city}'
--   '{street} {num}, {unit}. OG, {postal} {city}'
--
-- After substitution, collapses multiple spaces/commas and trims.
--
-- Arguments:
--   p_num     text  — street number
--   p_street  text  — street name + type
--   p_unit    text  — unit/apartment (may be '')
--   p_city    text  — city
--   p_region  text  — state or Bundesland
--   p_postal  text  — postal code
--   p_tmpl    text  — template string
--
-- Returns: text — formatted address
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fmt_address(
    p_num    text,
    p_street text,
    p_unit   text,
    p_city   text,
    p_region text,
    p_postal text,
    p_tmpl   text
) RETURNS text
LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE AS $$
    SELECT trim(regexp_replace(
        replace(replace(replace(replace(replace(replace(
            p_tmpl,
            '{num}',    p_num),
            '{street}', p_street),
            '{unit}',   p_unit),
            '{city}',   p_city),
            '{region}', p_region),
            '{postal}', p_postal),
        '\s{2,}', ' ', 'g'
    ))
$$;

-- ---------------------------------------------------------------------------
-- fmt_phone
-- Format a phone number by replacing '#' placeholders with random digits.
--
-- Algorithm:
--   For each '#' in the template at position k (0-based among '#' chars),
--   draw a digit using field label p_field || '#' || k.
--   The area_code is substituted for the '{area}' placeholder before digit fill.
--
-- US example template: '({area}) 555-01##'  → e.g. '(212) 555-0147'
--   The 555-01xx range is reserved for fictional use (NANP).
-- DE example template: '+49 {area} ###-####' → e.g. '+49 30 812-3456'
--
-- Arguments:
--   p_area_code  text    — digits-only area code from cities table
--   p_tmpl       text    — template with '{area}' and '#' placeholders
--   p_seed       bigint  — RNG seed
--   p_locale     text    — locale code
--   p_batch      int     — batch index
--   p_i          int     — position within batch
--   p_field      text    — field discriminator base
--
-- Returns: text — formatted phone number
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fmt_phone(
    p_area_code text,
    p_tmpl      text,
    p_seed      bigint,
    p_locale    text,
    p_batch     int,
    p_i         int,
    p_field     text
) RETURNS text
LANGUAGE plpgsql IMMUTABLE STRICT PARALLEL SAFE AS $$
DECLARE
    v_expanded text;   -- template after {area} substitution
    v_result   text := '';
    v_pos      int  := 0;  -- count of '#' replaced so far
    v_digit    text;
    v_char     text;
    v_k        int;
BEGIN
    -- Expand {area} placeholder first
    v_expanded := replace(p_tmpl, '{area}', p_area_code);

    -- Replace each '#' with a deterministic random digit
    FOR v_k IN 1..length(v_expanded) LOOP
        v_char := substr(v_expanded, v_k, 1);
        IF v_char = '#' THEN
            v_digit := (rand_int(p_seed, p_locale, p_batch, p_i,
                                 p_field || '#' || v_pos::text, 10))::text;
            v_result := v_result || v_digit;
            v_pos    := v_pos + 1;
        ELSE
            v_result := v_result || v_char;
        END IF;
    END LOOP;

    RETURN v_result;
END;
$$;

-- ---------------------------------------------------------------------------
-- fmt_email
-- Generate an email address from a person's name components.
--
-- Algorithm:
--   1. Transliterate first and last to ASCII using apply_translit.
--   2. Lowercase both.
--   3. Remove any remaining non-alphanumeric characters.
--   4. Pick a separator from choices(locale, 'email_sep') using p_field||'_sep'.
--   5. Optionally append a 1-3 digit number (pick from choices 'email_num_tmpl').
--   6. Pick a domain from choices(locale, 'email_domain') using p_field||'_dom'.
--   7. Assemble: localpart @ domain
--
-- Arguments:
--   p_locale  text    — locale code
--   p_first   text    — first name
--   p_last    text    — last name
--   p_seed    bigint  — RNG seed
--   p_batch   int     — batch index
--   p_i       int     — position within batch
--   p_field   text    — field discriminator base ('email')
--
-- Returns: text — email address (ASCII only, lowercase)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fmt_email(
    p_locale text,
    p_first  text,
    p_last   text,
    p_seed   bigint,
    p_batch  int,
    p_i      int,
    p_field  text
) RETURNS text
LANGUAGE plpgsql STABLE STRICT PARALLEL SAFE AS $$
DECLARE
    v_first   text;
    v_last    text;
    v_sep     text;
    v_num_tmpl text;
    v_num     text;
    v_domain  text;
    v_local   text;
    v_num_val int;
BEGIN
    -- Transliterate and sanitize
    v_first := lower(regexp_replace(apply_translit(p_locale, p_first), '[^a-zA-Z0-9]', '', 'g'));
    v_last  := lower(regexp_replace(apply_translit(p_locale, p_last),  '[^a-zA-Z0-9]', '', 'g'));

    -- Pick separator: '.', '_', or '' (empty)
    v_sep := pick_choice(p_locale, 'email_sep', p_seed, p_batch, p_i, p_field || '_sep');

    -- Pick number suffix template: '' (none), '##', '###', '####'
    v_num_tmpl := pick_choice(p_locale, 'email_num', p_seed, p_batch, p_i, p_field || '_num');
    IF v_num_tmpl = '' THEN
        v_num := '';
    ELSE
        -- Generate digits for the number suffix
        v_num_val := rand_int(p_seed, p_locale, p_batch, p_i, p_field || '_numval',
                              (10 ^ length(v_num_tmpl))::int);
        v_num := lpad(v_num_val::text, length(v_num_tmpl), '0');
    END IF;

    -- Pick domain
    v_domain := pick_choice(p_locale, 'email_domain', p_seed, p_batch, p_i, p_field || '_dom');

    -- Assemble local part: first + sep + last + num
    v_local := v_first || v_sep || v_last || v_num;

    -- Safety: if empty (e.g. all non-alpha), fall back to 'user' || num
    IF v_local = '' OR v_local = v_sep THEN
        v_local := 'user' || rand_int(p_seed, p_locale, p_batch, p_i, p_field || '_fb', 9999)::text;
    END IF;

    RETURN v_local || '@' || v_domain;
END;
$$;
