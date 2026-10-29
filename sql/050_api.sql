-- =============================================================================
-- 050_api.sql  — Public API functions
--
-- These are the entry points called by the Python application.
-- They validate all inputs and raise exceptions for invalid values.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- list_locales
-- Returns the available locales for the UI dropdown.
--
-- Returns: TABLE(code text, display_name text)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION list_locales()
RETURNS TABLE(code text, display_name text)
LANGUAGE sql STABLE PARALLEL SAFE AS $$
    SELECT code, display_name FROM locales ORDER BY display_name
$$;

-- ---------------------------------------------------------------------------
-- generate_users
-- Generate a batch of fake users. This is the main entry point for the app.
--
-- Validation (raises exception on failure):
--   - p_locale must exist in the locales table
--   - p_seed must be in [0, 2^31 - 1] (positive bigint safe for all platforms)
--   - p_batch must be in [0, 10000]
--   - p_size must be in [1, 50]
--
-- Algorithm:
--   Uses generate_series + LATERAL to call generate_user() in set-based style.
--   Each row's i corresponds to a distinct position in the RNG space.
--
-- Arguments:
--   p_locale  text    — locale code (e.g. 'en_US')
--   p_seed    bigint  — reproducibility seed
--   p_batch   int     — batch index (0-based)
--   p_size    int     — number of records to generate (default 10, max 50)
--
-- Returns: TABLE with columns:
--   batch_no   int     — the batch number (echoes p_batch)
--   idx        int     — 0-based index within batch
--   full_name  text
--   address    text
--   latitude   float8
--   longitude  float8
--   height_cm  numeric
--   weight_kg  numeric
--   eye_color  text
--   phone      text
--   email      text
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION generate_users(
    p_locale text,
    p_seed   bigint,
    p_batch  int,
    p_size   int DEFAULT 10
) RETURNS TABLE (
    batch_no  int,
    idx       int,
    full_name text,
    address   text,
    latitude  float8,
    longitude float8,
    height_cm numeric,
    weight_kg numeric,
    eye_color text,
    phone     text,
    email     text
)
LANGUAGE plpgsql STABLE PARALLEL SAFE AS $$
BEGIN
    -- Input validation
    IF NOT EXISTS (SELECT 1 FROM locales WHERE code = p_locale) THEN
        RAISE EXCEPTION 'Unknown locale: %. Use list_locales() to see available options.', p_locale
            USING ERRCODE = 'invalid_parameter_value';
    END IF;

    IF p_seed < 0 OR p_seed > 2147483647 THEN
        RAISE EXCEPTION 'Seed must be in [0, 2147483647], got: %', p_seed
            USING ERRCODE = 'invalid_parameter_value';
    END IF;

    IF p_batch < 0 OR p_batch > 10000 THEN
        RAISE EXCEPTION 'Batch must be in [0, 10000], got: %', p_batch
            USING ERRCODE = 'invalid_parameter_value';
    END IF;

    IF p_size < 1 OR p_size > 50 THEN
        RAISE EXCEPTION 'Size must be in [1, 50], got: %', p_size
            USING ERRCODE = 'invalid_parameter_value';
    END IF;

    RETURN QUERY
    SELECT
        p_batch                    AS batch_no,
        g.i                        AS idx,
        u.full_name,
        u.address,
        u.latitude,
        u.longitude,
        u.height_cm,
        u.weight_kg,
        u.eye_color,
        u.phone,
        u.email
    FROM generate_series(0, p_size - 1) AS g(i)
    CROSS JOIN LATERAL generate_user(p_locale, p_seed, p_batch, g.i) AS u;
END;
$$;

-- ---------------------------------------------------------------------------
-- generate_text  (Markov chain text generation — optional phase)
-- Generate deterministic fake text using a bigram Markov chain.
--
-- Algorithm:
--   1. Start with a seed bigram: pick the first (w1, w2) from the corpus
--      by choosing a random entry from markov WHERE w1='<START>'.
--   2. At each step k, pick next_word from markov WHERE locale=p_locale
--      AND w1=current_w1 AND w2=current_w2, weighted by weight column.
--      Use rand_u32(..., 'text#' || k) for the pick.
--   3. If no successor exists (dead end), restart from '<START>' using
--      a fresh random bigram.
--   4. Stop after p_n_words words.
--   5. Concatenate with spaces and capitalize the first letter.
--
-- Arguments:
--   p_locale   text    — locale code
--   p_seed     bigint  — RNG seed
--   p_batch    int     — batch index
--   p_i        int     — position within batch
--   p_n_words  int     — number of words to generate (suggested: 40-100)
--
-- Returns: text — a paragraph of pseudo-natural text in the locale language
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION generate_text(
    p_locale  text,
    p_seed    bigint,
    p_batch   int,
    p_i       int,
    p_n_words int DEFAULT 60
) RETURNS text
LANGUAGE plpgsql STABLE STRICT PARALLEL SAFE AS $$
DECLARE
    v_w1      text := '<START>';
    v_w2      text;
    v_next    text;
    v_words   text[] := '{}';
    v_k       int    := 0;
    v_total_w bigint;
    v_cum     bigint;
    v_r       bigint;
    v_row     record;
    v_found   bool;
    v_n       int;
BEGIN
    -- Pick initial w2 (first word after <START>, <START>)
    SELECT SUM(weight) INTO v_total_w
    FROM markov WHERE locale = p_locale AND w1 = '<START>' AND w2 = '<START>';

    IF v_total_w IS NULL OR v_total_w = 0 THEN
        RETURN '(No Markov data for locale ' || p_locale || ')';
    END IF;

    v_r := rand_u32(p_seed, p_locale, p_batch, p_i, 'text#start') % v_total_w;
    v_cum := 0;
    v_w2 := NULL;
    FOR v_row IN
        SELECT next_word, weight FROM markov
        WHERE locale = p_locale AND w1 = '<START>' AND w2 = '<START>'
        ORDER BY next_word
    LOOP
        v_cum := v_cum + v_row.weight;
        IF v_cum > v_r AND v_w2 IS NULL THEN
            v_w2 := v_row.next_word;
        END IF;
    END LOOP;

    v_w1 := '<START>';
    v_words := array_append(v_words, initcap(v_w2));
    v_k := 1;

    -- Walk the chain
    WHILE v_k < p_n_words LOOP
        -- Find successor
        SELECT SUM(weight) INTO v_total_w
        FROM markov WHERE locale = p_locale AND w1 = v_w1 AND w2 = v_w2;

        IF v_total_w IS NULL OR v_total_w = 0 THEN
            -- Dead end: finish previous sentence with a period
            v_n := array_length(v_words, 1);
            IF v_n > 0 AND v_words[v_n] !~ '[.!?]$' THEN
                v_words[v_n] := rtrim(v_words[v_n], ',;:') || '.';
            END IF;

            -- Restart next sentence from '<START>', '<START>'
            SELECT SUM(weight) INTO v_total_w
            FROM markov WHERE locale = p_locale AND w1 = '<START>' AND w2 = '<START>';
            IF v_total_w IS NULL OR v_total_w = 0 THEN EXIT; END IF;
            v_r := rand_u32(p_seed, p_locale, p_batch, p_i, 'text#rst' || v_k::text) % v_total_w;
            v_cum := 0;
            v_next := NULL;
            FOR v_row IN
                SELECT next_word, weight FROM markov
                WHERE locale = p_locale AND w1 = '<START>' AND w2 = '<START>'
                ORDER BY next_word
            LOOP
                v_cum := v_cum + v_row.weight;
                IF v_cum > v_r AND v_next IS NULL THEN v_next := v_row.next_word; END IF;
            END LOOP;
            v_w1 := '<START>';
            v_w2 := v_next;
            v_words := array_append(v_words, initcap(v_w2));
            v_k := v_k + 1;
            CONTINUE;
        END IF;

        v_r := rand_u32(p_seed, p_locale, p_batch, p_i, 'text#' || v_k::text) % v_total_w;
        v_cum := 0;
        v_next := NULL;
        FOR v_row IN
            SELECT next_word, weight FROM markov
            WHERE locale = p_locale AND w1 = v_w1 AND w2 = v_w2
            ORDER BY next_word
        LOOP
            v_cum := v_cum + v_row.weight;
            IF v_cum > v_r AND v_next IS NULL THEN v_next := v_row.next_word; END IF;
        END LOOP;

        v_w1 := v_w2;
        v_w2 := v_next;
        v_words := array_append(v_words, v_next);
        v_k := v_k + 1;
    END LOOP;

    -- Ensure proper first capital and ending period
    v_n := array_length(v_words, 1);
    IF v_n > 0 THEN
        v_words[1] := initcap(v_words[1]);
        v_words[v_n] := rtrim(v_words[v_n], ',;:.!?') || '.';
        RETURN array_to_string(v_words, ' ');
    ELSE
        RETURN '';
    END IF;
END;
$$;

