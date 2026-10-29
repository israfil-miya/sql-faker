"""
test_markov.py — Tests for Markov chain text generation (optional phase).
Skipped if the markov table is empty.
"""
import pytest
from .conftest import query, scalar


def has_markov(db):
    rows = query(db, "SELECT COUNT(*) AS n FROM markov")
    return rows[0]["n"] > 0


@pytest.fixture(scope="module")
def markov_available(db):
    if not has_markov(db):
        pytest.skip("Markov table is empty — run scripts/load_markov.py first")
    return True


class TestGenerateText:
    def test_returns_text(self, db, markov_available):
        rows = query(db,
            "SELECT generate_text('en_US', 42, 0, 0, 20) AS t")
        assert rows[0]["t"] is not None
        assert len(rows[0]["t"]) > 0

    def test_word_count_approximate(self, db, markov_available):
        """Generated text should have approximately the requested word count."""
        rows = query(db,
            "SELECT generate_text('en_US', 42, 0, 0, 30) AS t")
        text = rows[0]["t"]
        words = text.split()
        # Allow some slack for chain restarts
        assert 25 <= len(words) <= 40, f"Expected ~30 words, got {len(words)}"

    def test_reproducible(self, db, markov_available):
        rows1 = query(db, "SELECT generate_text('en_US', 42, 0, 0, 30) AS t")
        rows2 = query(db, "SELECT generate_text('en_US', 42, 0, 0, 30) AS t")
        assert rows1[0]["t"] == rows2[0]["t"]

    def test_different_seeds_different_text(self, db, markov_available):
        r1 = query(db, "SELECT generate_text('en_US', 1, 0, 0, 30) AS t")
        r2 = query(db, "SELECT generate_text('en_US', 2, 0, 0, 30) AS t")
        assert r1[0]["t"] != r2[0]["t"]

    def test_de_locale(self, db, markov_available):
        rows = query(db,
            "SELECT COUNT(*) AS n FROM markov WHERE locale = 'de_DE'")
        if rows[0]["n"] == 0:
            pytest.skip("No de_DE Markov data")
        rows = query(db,
            "SELECT generate_text('de_DE', 42, 0, 0, 20) AS t")
        assert rows[0]["t"] is not None

    def test_starts_with_capital(self, db, markov_available):
        rows = query(db, "SELECT generate_text('en_US', 42, 0, 0, 30) AS t")
        text = rows[0]["t"]
        assert text[0].isupper(), f"Text should start with capital: {text!r}"

    def test_ends_with_period(self, db, markov_available):
        rows = query(db, "SELECT generate_text('en_US', 42, 0, 0, 30) AS t")
        text = rows[0]["t"]
        assert text.endswith("."), f"Text should end with period: {text!r}"

