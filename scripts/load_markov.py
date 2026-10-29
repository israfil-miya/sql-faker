#!/usr/bin/env python3
"""
load_markov.py — Build the Markov chain table from plain-text corpora.

Usage:
    python scripts/load_markov.py --locale en_US corpus/en_US.txt
    python scripts/load_markov.py --locale de_DE corpus/de_DE.txt

The text file should be plain UTF-8. Lines starting with # are skipped.
The script builds a bigram (w1, w2) → next_word frequency table
and inserts into the markov table.

The <START> sentinel marks sentence beginnings.
"""

import os
import re
import sys
import argparse
import logging
from collections import defaultdict
from pathlib import Path
import psycopg
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

SENTENCE_END = re.compile(r'[.!?]+\s*')
TOKEN        = re.compile(r"[\w'äöüÄÖÜßéèàáñç-]+,?", re.UNICODE)


def tokenize(text: str) -> list[list[str]]:
    """Split text into sentences, then words."""
    sentences = SENTENCE_END.split(text)
    result = []
    for sent in sentences:
        words = TOKEN.findall(sent)
        if words:
            words[-1] = words[-1].rstrip(',')
            result.append(words)
    return result


def build_chain(sentences: list[list[str]]) -> dict:
    """Build bigram frequency map: (w1, w2) → {next_word: count}."""
    chain = defaultdict(lambda: defaultdict(int))
    for words in sentences:
        if not words:
            continue
        # Start transitions from <START>
        if words:
            chain[('<START>', '<START>')][words[0]] += 1
        for i, word in enumerate(words):
            w1 = words[i - 1] if i > 0 else '<START>'
            w2 = word
            if i + 1 < len(words):
                chain[(w1, w2)][words[i + 1]] += 1
    return chain


def load_corpus(path: Path) -> list[list[str]]:
    text = path.read_text(encoding='utf-8')
    # Strip comments
    lines = [l for l in text.splitlines() if not l.startswith('#')]
    text = ' '.join(lines)
    # Split into sentences
    parts = SENTENCE_END.split(text)
    result = []
    for part in parts:
        words = TOKEN.findall(part)
        if words:
            words[-1] = words[-1].rstrip(',')
            result.append(words)
    return result


def main():
    parser = argparse.ArgumentParser(description='Load Markov chain corpus into DB')
    parser.add_argument('corpus', help='Path to corpus text file')
    parser.add_argument('--locale', required=True, help='Locale code (e.g. en_US)')
    parser.add_argument('--clear', action='store_true',
                        help='Clear existing markov data for this locale first')
    args = parser.parse_args()

    corpus_path = Path(args.corpus)
    if not corpus_path.exists():
        log.error("Corpus file not found: %s", corpus_path)
        sys.exit(1)

    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        log.error("DATABASE_URL not set")
        sys.exit(1)

    log.info("Loading corpus from %s ...", corpus_path)
    sentences = load_corpus(corpus_path)
    log.info("Found %d sentences", len(sentences))

    chain = build_chain(sentences)
    log.info("Chain has %d unique bigrams", len(chain))

    conn = psycopg.connect(database_url)
    with conn:
        if args.clear:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM markov WHERE locale = %s", (args.locale,))
                log.info("Cleared existing markov data for %s", args.locale)

        rows = []
        for (w1, w2), nexts in chain.items():
            for next_word, count in nexts.items():
                rows.append((args.locale, w1, w2, next_word, count))

        log.info("Inserting %d rows into markov ...", len(rows))
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO markov (locale, w1, w2, next_word, weight)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (locale, w1, w2, next_word)
                DO UPDATE SET weight = markov.weight + EXCLUDED.weight
            """, rows)

    conn.close()
    log.info("Done. Markov chain loaded for locale '%s'.", args.locale)


if __name__ == '__main__':
    main()

