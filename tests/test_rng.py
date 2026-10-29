"""
test_rng.py — Tests for the RNG layer (rand_u32, rand_int, rand_uniform,
              rand_normal, rand_sphere).
"""
import math
import pytest
from .conftest import query, scalar

LOCALE = "en_US"
SEED   = 42
BATCH  = 0
N_STAT = 10_000   # samples for statistical tests


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

class TestReproducibility:
    def test_rand_u32_same_args(self, db):
        """Identical args produce identical output."""
        r1 = scalar(db, "SELECT rand_u32(%s,%s,%s,%s,%s)", (SEED, LOCALE, BATCH, 0, 'x'))
        r2 = scalar(db, "SELECT rand_u32(%s,%s,%s,%s,%s)", (SEED, LOCALE, BATCH, 0, 'x'))
        assert r1 == r2

    def test_rand_u32_range(self, db):
        """rand_u32 is always in [0, 2^32)."""
        rows = query(db,
            "SELECT rand_u32(%s,%s,%s,g.i,'test') AS v FROM generate_series(0,99) g(i)",
            (SEED, LOCALE, BATCH))
        for r in rows:
            assert 0 <= r["v"] < 2**32, f"Out of range: {r['v']}"

    def test_rand_int_range(self, db):
        """rand_int is always in [0, n)."""
        rows = query(db,
            "SELECT rand_int(%s,%s,%s,g.i,'test',7) AS v FROM generate_series(0,999) g(i)",
            (SEED, LOCALE, BATCH))
        for r in rows:
            assert 0 <= r["v"] < 7

    def test_rand_uniform_open(self, db):
        """rand_uniform is strictly in (0, 1)."""
        rows = query(db,
            "SELECT rand_uniform(%s,%s,%s,g.i,'test') AS v FROM generate_series(0,9999) g(i)",
            (SEED, LOCALE, BATCH))
        for r in rows:
            assert 0.0 < r["v"] < 1.0, f"Not in (0,1): {r['v']}"


# ---------------------------------------------------------------------------
# Sensitivity
# ---------------------------------------------------------------------------

class TestSensitivity:
    def _get(self, db, seed, locale, batch, i, field):
        return scalar(db,
            "SELECT rand_u32(%s,%s,%s,%s,%s)",
            (seed, locale, batch, i, field))

    def test_different_seed(self, db):
        v1 = self._get(db, 1, LOCALE, 0, 0, 'f')
        v2 = self._get(db, 2, LOCALE, 0, 0, 'f')
        assert v1 != v2

    def test_different_locale(self, db):
        v1 = self._get(db, SEED, 'en_US', 0, 0, 'f')
        v2 = self._get(db, SEED, 'de_DE', 0, 0, 'f')
        assert v1 != v2

    def test_different_batch(self, db):
        v1 = self._get(db, SEED, LOCALE, 0, 0, 'f')
        v2 = self._get(db, SEED, LOCALE, 1, 0, 'f')
        assert v1 != v2

    def test_different_i(self, db):
        v1 = self._get(db, SEED, LOCALE, 0, 0, 'f')
        v2 = self._get(db, SEED, LOCALE, 0, 1, 'f')
        assert v1 != v2

    def test_different_field(self, db):
        v1 = self._get(db, SEED, LOCALE, 0, 0, 'field_a')
        v2 = self._get(db, SEED, LOCALE, 0, 0, 'field_b')
        assert v1 != v2


# ---------------------------------------------------------------------------
# Normal distribution  (Box-Muller)
# ---------------------------------------------------------------------------

class TestNormalDistribution:
    MEAN = 175.0
    SD   = 7.0
    TOL_MEAN = 4 * SD / math.sqrt(N_STAT)   # ~4-sigma tolerance on sample mean
    TOL_SD   = 0.05                           # 5% relative tolerance on sample SD

    def test_normal_mean_and_sd(self, db):
        rows = query(db, f"""
            SELECT AVG(rand_normal(%s,%s,%s,g.i,'h',{self.MEAN},{self.SD})) AS m,
                   STDDEV(rand_normal(%s,%s,%s,g.i,'h',{self.MEAN},{self.SD})) AS s
            FROM generate_series(0,{N_STAT}-1) g(i)
        """, (SEED, LOCALE, BATCH, SEED, LOCALE, BATCH))
        row = rows[0]
        assert abs(row["m"] - self.MEAN) < self.TOL_MEAN, \
            f"Mean {row['m']:.3f} differs from {self.MEAN} by more than {self.TOL_MEAN:.3f}"
        assert abs(row["s"] - self.SD) / self.SD < self.TOL_SD, \
            f"SD {row['s']:.3f} differs from {self.SD} by more than {self.TOL_SD*100:.0f}%"


# ---------------------------------------------------------------------------
# Sphere sampling
# ---------------------------------------------------------------------------

class TestSphere:
    """
    For points uniform on the sphere:
      - E[sin(lat)] = 0
      - E[sin²(lat)] = 1/3  (this is the KEY test — naive lat uniform gives 1/2)
      - E[lon] = 0
      - lat ∈ [-90, 90], lon ∈ [-180, 180]
    """
    TOL = 0.05

    def _stats(self, db):
        rows = query(db, f"""
            SELECT
                AVG(sin(radians(lat)))        AS e_sin_lat,
                AVG(sin(radians(lat))^2)      AS e_sin2_lat,
                AVG(lon)                      AS e_lon,
                MIN(lat) AS min_lat, MAX(lat) AS max_lat,
                MIN(lon) AS min_lon, MAX(lon) AS max_lon
            FROM (
                SELECT (rand_sphere(%s,%s,%s,g.i,'geo')).lat,
                       (rand_sphere(%s,%s,%s,g.i,'geo')).lon
                FROM generate_series(0,{N_STAT}-1) g(i)
            ) t
        """, (SEED, LOCALE, BATCH, SEED, LOCALE, BATCH))
        return rows[0]

    def test_e_sin_lat_near_zero(self, db):
        st = self._stats(db)
        assert abs(st["e_sin_lat"]) < self.TOL, \
            f"E[sin(lat)] = {st['e_sin_lat']:.4f}, expected ≈ 0"

    def test_e_sin2_lat_near_third(self, db):
        st = self._stats(db)
        assert abs(st["e_sin2_lat"] - 1/3) < self.TOL, \
            f"E[sin²(lat)] = {st['e_sin2_lat']:.4f}, expected ≈ 0.333 (naive uniform gives 0.5)"

    def test_e_lon_near_zero(self, db):
        st = self._stats(db)
        assert abs(st["e_lon"]) < 2.0, \
            f"E[lon] = {st['e_lon']:.4f}, expected ≈ 0"

    def test_lat_range(self, db):
        st = self._stats(db)
        assert -90.0 <= st["min_lat"] and st["max_lat"] <= 90.0

    def test_lon_range(self, db):
        st = self._stats(db)
        assert -180.0 <= st["min_lon"] and st["max_lon"] <= 180.0

    def test_naive_lat_fails_e_sin2(self, db):
        """
        Control test: naive uniform lat in [-90,90] gives E[sin²(lat)] ≈ 0.5,
        NOT 1/3.  This proves our sphere test has power to detect bad implementations.
        """
        rows = query(db, f"""
            SELECT AVG(sin(radians(lat))^2) AS e_sin2
            FROM (
                SELECT (rand_uniform(%s,%s,%s,g.i,'naive') * 180 - 90) AS lat
                FROM generate_series(0,{N_STAT}-1) g(i)
            ) t
        """, (SEED, LOCALE, BATCH))
        e_sin2 = rows[0]["e_sin2"]
        # naive gives ~0.5, so it should FAIL the 1/3 test
        assert abs(e_sin2 - 0.5) < 0.05, \
            f"Naive lat should give E[sin²] ≈ 0.5, got {e_sin2:.4f}"

