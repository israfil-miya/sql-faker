-- =============================================================================
-- 040_composer.sql  — generate_user: composes all fields for one record
--
-- This is the core function that ties all layers together.
-- It calls RNG → Pickers → Formatters and returns a fake_user composite.
--
-- Each field uses a distinct p_field label so draws are fully independent.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- generate_user
-- Generate a single fake user record deterministically.
--
-- Determinism guarantee:
--   The output is a pure function of (p_locale, p_seed, p_batch, p_i).
--   Changing any one argument changes the output; identical arguments always
--   produce identical output regardless of call order.
--
-- Field generation field labels:
--   'gender'     — pick male/female (0=male, 1=female)
--   'title'      — pick honorific from choices
--   'first'      — pick first name
--   'middle'     — pick middle name
--   'last'       — pick last name
--   'name_tmpl'  — pick name template from choices
--   'city'       — pick city (returns city, region, postal range, area_code)
--   'street'     — pick street name
--   'street_type'— pick street type suffix from choices
--   'house_num'  — house number in [1, 9999]
--   'unit'       — optional unit number
--   'addr_tmpl'  — pick address template from choices
--   'geo'        — sphere point (internally uses 'geo_lat', 'geo_lon')
--   'height'     — Box-Muller normal (internally uses 'height#1', 'height#2')
--   'weight'     — Box-Muller normal (internally uses 'weight#1', 'weight#2')
--   'eye'        — pick eye color from choices
--   'phone_tmpl' — pick phone template from choices
--   'phone'      — fill phone template digits
--   'email'      — email components (internally uses 'email_sep', etc.)
--
-- Arguments:
--   p_locale  text    — locale code (must exist in locales table)
--   p_seed    bigint  — caller seed
--   p_batch   int     — batch index (≥ 0)
--   p_i       int     — record index within batch (0-based)
--
-- Returns: fake_user composite type
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION generate_user(
    p_locale text,
    p_seed   bigint,
    p_batch  int,
    p_i      int
) RETURNS fake_user
LANGUAGE plpgsql STABLE STRICT PARALLEL SAFE AS $$
DECLARE
    -- Gender
    v_gender_idx  int;
    v_gender      text;
    v_first_kind  text;
    v_title_cat   text;

    -- Name components
    v_title       text;
    v_first       text;
    v_middle      text;
    v_last        text;
    v_name_tmpl   text;
    v_full_name   text;

    -- Address components
    v_city_row    record;
    v_street_name text;
    v_street_type text;
    v_street      text;
    v_house_num   int;
    v_unit_raw    int;
    v_unit        text;
    v_postal      text;
    v_postal_range int;
    v_addr_tmpl   text;
    v_address     text;

    -- Geolocation
    v_geo         record;

    -- Physical attributes
    v_bp_h        record;
    v_bp_w        record;
    v_height      float8;
    v_weight      float8;
    v_eye_color   text;

    -- Phone
    v_phone_tmpl  text;
    v_phone       text;

    -- Email
    v_email       text;

    -- Result
    v_result      fake_user;
BEGIN
    -- -------------------------------------------------------------------------
    -- Gender: 0 → male, 1 → female (equal probability)
    -- -------------------------------------------------------------------------
    v_gender_idx := rand_int(p_seed, p_locale, p_batch, p_i, 'gender', 2);
    v_gender     := CASE v_gender_idx WHEN 0 THEN 'male' ELSE 'female' END;
    v_first_kind := CASE v_gender_idx WHEN 0 THEN 'first_male' ELSE 'first_female' END;
    v_title_cat  := CASE v_gender_idx WHEN 0 THEN 'title_male' ELSE 'title_female' END;

    -- -------------------------------------------------------------------------
    -- Name components
    -- -------------------------------------------------------------------------
    v_title    := pick_choice(p_locale, v_title_cat,   p_seed, p_batch, p_i, 'title');
    v_first    := pick_name(p_locale, v_first_kind,    p_seed, p_batch, p_i, 'first');
    v_middle   := pick_name(p_locale, v_first_kind,    p_seed, p_batch, p_i, 'middle');
    v_last     := pick_name(p_locale, 'last',          p_seed, p_batch, p_i, 'last');
    v_name_tmpl := pick_choice(p_locale, 'name_template', p_seed, p_batch, p_i, 'name_tmpl');
    v_full_name := fmt_name(v_title, v_first, v_middle, v_last, v_name_tmpl);

    -- -------------------------------------------------------------------------
    -- Address
    -- -------------------------------------------------------------------------
    SELECT * INTO v_city_row FROM pick_city(p_locale, p_seed, p_batch, p_i, 'city');

    v_street_name := pick_street(p_locale, p_seed, p_batch, p_i, 'street');
    v_street_type := pick_choice(p_locale, 'street_type', p_seed, p_batch, p_i, 'street_type');
    v_street      := v_street_name || ' ' || v_street_type;

    v_house_num := rand_int(p_seed, p_locale, p_batch, p_i, 'house_num', 9999) + 1;

    -- Unit: ~30% chance of having one (unit raw 0..9 → 0..2 = has unit)
    v_unit_raw := rand_int(p_seed, p_locale, p_batch, p_i, 'unit_flag', 10);
    IF v_unit_raw < 3 THEN
        v_unit := (rand_int(p_seed, p_locale, p_batch, p_i, 'unit_num', 999) + 1)::text;
    ELSE
        v_unit := '';
    END IF;

    -- Postal code from range
    v_postal_range := v_city_row.postal_max - v_city_row.postal_min + 1;
    v_postal := lpad(
        (v_city_row.postal_min + rand_int(p_seed, p_locale, p_batch, p_i, 'postal', v_postal_range))::text,
        5, '0'
    );

    v_addr_tmpl := pick_choice(p_locale, 'addr_template', p_seed, p_batch, p_i, 'addr_tmpl');
    v_address := fmt_address(
        v_house_num::text,
        v_street,
        v_unit,
        v_city_row.city,
        v_city_row.region,
        v_postal,
        v_addr_tmpl
    );

    -- -------------------------------------------------------------------------
    -- Geolocation  (uniform on sphere)
    -- -------------------------------------------------------------------------
    SELECT * INTO v_geo FROM rand_sphere(p_seed, p_locale, p_batch, p_i, 'geo');

    -- -------------------------------------------------------------------------
    -- Physical attributes
    -- -------------------------------------------------------------------------
    SELECT * INTO v_bp_h FROM body_params
    WHERE locale = p_locale AND gender = v_gender AND attribute = 'height_cm';

    SELECT * INTO v_bp_w FROM body_params
    WHERE locale = p_locale AND gender = v_gender AND attribute = 'weight_kg';

    v_height := GREATEST(v_bp_h.min_val, LEAST(v_bp_h.max_val,
        rand_normal(p_seed, p_locale, p_batch, p_i, 'height', v_bp_h.mean, v_bp_h.sd)
    ));

    v_weight := GREATEST(v_bp_w.min_val, LEAST(v_bp_w.max_val,
        rand_normal(p_seed, p_locale, p_batch, p_i, 'weight', v_bp_w.mean, v_bp_w.sd)
    ));

    v_eye_color := pick_choice(p_locale, 'eye_color', p_seed, p_batch, p_i, 'eye');

    -- -------------------------------------------------------------------------
    -- Phone
    -- -------------------------------------------------------------------------
    v_phone_tmpl := pick_choice(p_locale, 'phone_template', p_seed, p_batch, p_i, 'phone_tmpl');
    v_phone := fmt_phone(
        v_city_row.area_code,
        v_phone_tmpl,
        p_seed, p_locale, p_batch, p_i, 'phone'
    );

    -- -------------------------------------------------------------------------
    -- Email
    -- -------------------------------------------------------------------------
    v_email := fmt_email(p_locale, v_first, v_last, p_seed, p_batch, p_i, 'email');

    -- -------------------------------------------------------------------------
    -- Assemble result
    -- -------------------------------------------------------------------------
    v_result.full_name  := v_full_name;
    v_result.address    := v_address;
    v_result.latitude   := round(v_geo.lat::numeric, 6);
    v_result.longitude  := round(v_geo.lon::numeric, 6);
    v_result.height_cm  := round(v_height::numeric, 1);
    v_result.weight_kg  := round(v_weight::numeric, 1);
    v_result.eye_color  := v_eye_color;
    v_result.phone      := v_phone;
    v_result.email      := v_email;

    RETURN v_result;
END;
$$;

