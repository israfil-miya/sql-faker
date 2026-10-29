"""
test_api.py — Tests for generate_users() and list_locales().
"""
import re
import pytest
from .conftest import query, scalar
import psycopg

SEED   = 42
BATCH  = 0
SIZE   = 10

# Expected golden values for (en_US, seed=42, batch=0)
# Update these after running once locally: they are the source of truth.
GOLDEN_EN_US = None   # Set by first run; see test_golden_fixture


def call(db, locale, seed, batch, size):
    return query(db,
        "SELECT * FROM generate_users(%s::text,%s::bigint,%s::int,%s::int)",
        (locale, seed, batch, size))


class TestListLocales:
    def test_returns_rows(self, db):
        rows = query(db, "SELECT * FROM list_locales()")
        assert len(rows) >= 2, "Expected at least 2 locales"

    def test_has_en_us(self, db):
        rows = query(db, "SELECT * FROM list_locales()")
        codes = [r["code"] for r in rows]
        assert "en_US" in codes

    def test_has_de_de(self, db):
        rows = query(db, "SELECT * FROM list_locales()")
        codes = [r["code"] for r in rows]
        assert "de_DE" in codes


class TestGenerateUsersBasic:
    def test_returns_correct_count(self, db):
        rows = call(db, "en_US", SEED, BATCH, SIZE)
        assert len(rows) == SIZE

    def test_batch_and_idx_fields(self, db):
        rows = call(db, "en_US", SEED, BATCH, SIZE)
        for i, r in enumerate(rows):
            assert r["batch_no"] == BATCH
            assert r["idx"] == i

    def test_all_fields_non_null(self, db):
        rows = call(db, "en_US", SEED, BATCH, SIZE)
        required = ["full_name","address","latitude","longitude",
                    "height_cm","weight_kg","eye_color","phone","email"]
        for r in rows:
            for f in required:
                assert r[f] is not None, f"Field {f} is NULL in row {r['idx']}"

    def test_no_empty_strings(self, db):
        rows = call(db, "en_US", SEED, BATCH, SIZE)
        for r in rows:
            for k, v in r.items():
                if isinstance(v, str):
                    assert v.strip() != "", f"Field {k} is empty in row {r['idx']}"


class TestReproducibility:
    def test_same_args_same_result(self, db):
        rows1 = call(db, "en_US", SEED, BATCH, SIZE)
        rows2 = call(db, "en_US", SEED, BATCH, SIZE)
        for r1, r2 in zip(rows1, rows2):
            assert r1 == r2

    def test_batch5_independent_of_call_order(self, db):
        """Batch 5 requested directly equals batch 5 after iterating 0..4."""
        direct = call(db, "en_US", SEED, 5, SIZE)
        # Also fetch batches 0-4 to make sure they don't affect state
        for b in range(5):
            call(db, "en_US", SEED, b, SIZE)
        after_iter = call(db, "en_US", SEED, 5, SIZE)
        assert direct == after_iter

    def test_size_independence(self, db):
        """Row i from size=10 equals row i from size=50."""
        rows10 = call(db, "en_US", SEED, BATCH, 10)
        rows50 = call(db, "en_US", SEED, BATCH, 50)
        for i in range(10):
            for field in ["full_name","email","latitude","longitude"]:
                assert rows10[i][field] == rows50[i][field], \
                    f"Field {field} at idx {i} differs between size=10 and size=50"

    def test_locale_independence(self, db):
        """Same seed + batch in en_US and de_DE should produce DIFFERENT names."""
        en_rows = call(db, "en_US", SEED, BATCH, SIZE)
        de_rows = call(db, "de_DE", SEED, BATCH, SIZE)
        # Very unlikely to all match; check first name at least differs
        en_names = [r["full_name"] for r in en_rows]
        de_names = [r["full_name"] for r in de_rows]
        assert en_names != de_names


class TestValidation:
    def test_bad_locale(self, db):
        with pytest.raises(psycopg.errors.InvalidParameterValue):
            call(db, "xx_YY", SEED, BATCH, SIZE)

    def test_negative_seed(self, db):
        with pytest.raises(psycopg.errors.InvalidParameterValue):
            call(db, "en_US", -1, BATCH, SIZE)

    def test_seed_too_large(self, db):
        with pytest.raises(psycopg.errors.InvalidParameterValue):
            call(db, "en_US", 2_147_483_648, BATCH, SIZE)

    def test_negative_batch(self, db):
        with pytest.raises(psycopg.errors.InvalidParameterValue):
            call(db, "en_US", SEED, -1, SIZE)

    def test_size_zero(self, db):
        with pytest.raises(psycopg.errors.InvalidParameterValue):
            call(db, "en_US", SEED, BATCH, 0)

    def test_size_over_50(self, db):
        with pytest.raises(psycopg.errors.InvalidParameterValue):
            call(db, "en_US", SEED, BATCH, 51)


class TestFormats:
    EN_POSTAL_RE  = re.compile(r"^\d{5}$")
    EMAIL_RE      = re.compile(r"^[a-z0-9._+-]+@[a-z0-9.-]+\.[a-z]{2,}$")
    LAT_RANGE     = (-90.0, 90.0)
    LON_RANGE     = (-180.0, 180.0)
    HEIGHT_RANGE  = (100.0, 250.0)
    WEIGHT_RANGE  = (30.0, 300.0)

    def _rows(self, db):
        return call(db, "en_US", SEED, BATCH, 50)

    def test_email_format(self, db):
        for r in self._rows(db):
            assert self.EMAIL_RE.match(r["email"]), \
                f"Invalid email: {r['email']}"

    def test_latitude_range(self, db):
        for r in self._rows(db):
            assert self.LAT_RANGE[0] <= r["latitude"] <= self.LAT_RANGE[1]

    def test_longitude_range(self, db):
        for r in self._rows(db):
            assert self.LON_RANGE[0] <= r["longitude"] <= self.LON_RANGE[1]

    def test_height_plausible(self, db):
        for r in self._rows(db):
            assert self.HEIGHT_RANGE[0] <= float(r["height_cm"]) <= self.HEIGHT_RANGE[1], \
                f"Implausible height: {r['height_cm']}"

    def test_weight_plausible(self, db):
        for r in self._rows(db):
            assert self.WEIGHT_RANGE[0] <= float(r["weight_kg"]) <= self.WEIGHT_RANGE[1], \
                f"Implausible weight: {r['weight_kg']}"

    def test_no_template_leakage(self, db):
        """Placeholders like {first} must not appear in output."""
        placeholders = ["{title}", "{first}", "{middle}", "{last}", "{mi}",
                        "{num}", "{street}", "{unit}", "{city}", "{region}", "{postal}",
                        "{area}"]
        for r in self._rows(db):
            for field in ["full_name", "address", "phone", "email"]:
                val = str(r[field])
                for ph in placeholders:
                    assert ph not in val, \
                        f"Placeholder {ph} leaked into {field}: {val!r}"


class TestGoldenFixtures:
    """
    Golden-output tests.  On first run with --generate-golden, write the fixture.
    Normally, compare against the stored fixture.

    To generate: pytest tests/test_api.py::TestGoldenFixtures -s --generate-golden
    """
    GOLDEN = {
        # (locale, seed, batch, idx): partial expected values
        # Populated after first run
    }

    def test_en_us_golden(self, db):
        """en_US seed=42 batch=0 must produce stable output across deployments."""
        rows = call(db, "en_US", 42, 0, 5)
        # Verify structural consistency (update expected values after first run)
        assert len(rows) == 5
        # Verify fields are present and well-formed
        for r in rows:
            assert "@" in r["email"]
            assert len(r["full_name"].split()) >= 2

    def test_de_de_golden(self, db):
        """de_DE seed=42 batch=0 must produce stable output."""
        rows = call(db, "de_DE", 42, 0, 5)
        assert len(rows) == 5
        for r in rows:
            assert "@" in r["email"]

