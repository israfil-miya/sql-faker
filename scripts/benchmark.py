import os
import sys
import time
import statistics
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.environ["DATABASE_URL"]


def log(msg=""):
    print(msg, flush=True)


def benchmark_sql_engine(conn, locale="en_US", batch_size=50, num_batches=20, warmup_batches=3):
    with conn.cursor() as cur:
        for w in range(warmup_batches):
            cur.execute("SELECT * FROM generate_users(%s, 42, %s, %s)", (locale, w, batch_size))
            cur.fetchall()

        latencies = []
        for b in range(num_batches):
            t0 = time.perf_counter()
            cur.execute("SELECT * FROM generate_users(%s, 42, %s, %s)", (locale, b, batch_size))
            rows = cur.fetchall()
            t1 = time.perf_counter()
            latencies.append(t1 - t0)

    total_time = sum(latencies)
    total_users = num_batches * batch_size
    users_per_sec = total_users / total_time
    ms_per_user = (total_time / total_users) * 1000
    sorted_latencies = sorted(latencies)
    mean_batch_ms = statistics.mean(latencies) * 1000
    p50_batch_ms = sorted_latencies[int(len(latencies) * 0.50)] * 1000
    p95_batch_ms = sorted_latencies[int(len(latencies) * 0.95)] * 1000
    p99_batch_ms = sorted_latencies[int(len(latencies) * 0.99)] * 1000

    return {
        "locale": locale,
        "batch_size": batch_size,
        "num_batches": num_batches,
        "total_users": total_users,
        "total_time_s": total_time,
        "users_per_sec": users_per_sec,
        "ms_per_user": ms_per_user,
        "mean_batch_ms": mean_batch_ms,
        "p50_batch_ms": p50_batch_ms,
        "p95_batch_ms": p95_batch_ms,
        "p99_batch_ms": p99_batch_ms,
    }


def benchmark_flask_e2e(app_client, locale="en_US", batch_size=50, num_batches=20, warmup_batches=3):
    for w in range(warmup_batches):
        app_client.get(f"/?mode=users&locale={locale}&seed=42&batch={w}&size={batch_size}")

    latencies = []
    for b in range(num_batches):
        t0 = time.perf_counter()
        resp = app_client.get(f"/?mode=users&locale={locale}&seed=42&batch={b}&size={batch_size}")
        t1 = time.perf_counter()
        if resp.status_code != 200:
            raise RuntimeError(f"Request failed with status {resp.status_code}")
        latencies.append(t1 - t0)

    total_time = sum(latencies)
    total_users = num_batches * batch_size
    users_per_sec = total_users / total_time
    ms_per_user = (total_time / total_users) * 1000
    mean_batch_ms = statistics.mean(latencies) * 1000

    return {
        "locale": locale,
        "batch_size": batch_size,
        "num_batches": num_batches,
        "total_users": total_users,
        "total_time_s": total_time,
        "users_per_sec": users_per_sec,
        "ms_per_user": ms_per_user,
        "mean_batch_ms": mean_batch_ms,
    }


def benchmark_markov_text(conn, locale="en_US", words=100, num_batches=20, warmup_batches=3):
    with conn.cursor() as cur:
        for w in range(warmup_batches):
            cur.execute("SELECT generate_text(%s, 42, %s, 0, %s)", (locale, w, words))
            cur.fetchall()

        latencies = []
        for b in range(num_batches):
            t0 = time.perf_counter()
            cur.execute("SELECT generate_text(%s, 42, %s, 0, %s)", (locale, b, words))
            cur.fetchall()
            t1 = time.perf_counter()
            latencies.append(t1 - t0)

    total_time = sum(latencies)
    total_words = num_batches * words
    words_per_sec = total_words / total_time
    ms_per_call = (total_time / num_batches) * 1000

    return {
        "locale": locale,
        "words": words,
        "num_batches": num_batches,
        "total_words": total_words,
        "total_time_s": total_time,
        "words_per_sec": words_per_sec,
        "ms_per_call": ms_per_call,
    }


def main():
    log("================================================================================")
    log(" FAKE DATA GENERATOR BENCHMARK SUITE")
    log(" PostgreSQL Stored Procedures + Python Psycopg Driver")
    log("================================================================================\n")

    log("1. SQL ENGINE GENERATION BENCHMARK (Pure DB + Driver Fetch)")
    log("-" * 88)
    log(f"{'Locale':<8} | {'Batch':<6} | {'Total':<7} | {'Time (s)':<9} | {'Throughput':<15} | {'Latency/User':<14} | {'Mean Batch':<10}")
    log("-" * 88)

    configs = [
        ("en_US", 10, 20),
        ("en_US", 20, 20),
        ("en_US", 50, 20),
        ("de_DE", 10, 20),
        ("de_DE", 20, 20),
        ("de_DE", 50, 20),
    ]

    sql_results = []
    with psycopg.connect(DATABASE_URL, row_factory=dict_row, autocommit=True) as conn:
        for loc, size, count in configs:
            res = benchmark_sql_engine(conn, locale=loc, batch_size=size, num_batches=count)
            sql_results.append(res)
            log(
                f"{res['locale']:<8} | "
                f"{res['batch_size']:<6} | "
                f"{res['total_users']:<7} | "
                f"{res['total_time_s']:<9.3f} | "
                f"{res['users_per_sec']:>7.1f} users/s | "
                f"{res['ms_per_user']:>8.2f} ms/u | "
                f"{res['mean_batch_ms']:>8.2f} ms"
            )

    log("\n2. END-TO-END HTTP + JINJA BENCHMARK (Flask Request -> DB -> Rendered HTML)")
    log("-" * 88)
    log(f"{'Locale':<8} | {'Batch':<6} | {'Total':<7} | {'Time (s)':<9} | {'Throughput':<15} | {'Latency/User':<14} | {'Mean Batch':<10}")
    log("-" * 88)

    from app import app
    app_client = app.test_client()

    e2e_configs = [
        ("en_US", 10, 10),
        ("en_US", 50, 10),
        ("de_DE", 10, 10),
        ("de_DE", 50, 10),
    ]

    e2e_results = []
    for loc, size, count in e2e_configs:
        res = benchmark_flask_e2e(app_client, locale=loc, batch_size=size, num_batches=count)
        e2e_results.append(res)
        log(
            f"{res['locale']:<8} | "
            f"{res['batch_size']:<6} | "
            f"{res['total_users']:<7} | "
            f"{res['total_time_s']:<9.3f} | "
            f"{res['users_per_sec']:>7.1f} users/s | "
            f"{res['ms_per_user']:>8.2f} ms/u | "
            f"{res['mean_batch_ms']:>8.2f} ms"
        )

    log("\n3. MARKOV TEXT SYNTHESIS BENCHMARK (Bigram Chain in PostgreSQL)")
    log("-" * 88)
    log(f"{'Locale':<8} | {'Words':<6} | {'Calls':<7} | {'Time (s)':<9} | {'Throughput':<15} | {'Latency/Call':<14}")
    log("-" * 88)

    markov_configs = [
        ("en_US", 60, 10),
        ("en_US", 150, 10),
        ("de_DE", 60, 10),
        ("de_DE", 150, 10),
    ]

    with psycopg.connect(DATABASE_URL, row_factory=dict_row, autocommit=True) as conn:
        for loc, words, count in markov_configs:
            res = benchmark_markov_text(conn, locale=loc, words=words, num_batches=count)
            log(
                f"{res['locale']:<8} | "
                f"{res['words']:<6} | "
                f"{res['num_batches']:<7} | "
                f"{res['total_time_s']:<9.3f} | "
                f"{res['words_per_sec']:>7.1f} words/s | "
                f"{res['ms_per_call']:>8.2f} ms/call"
            )

    log("\n" + "=" * 88)
    log(" BENCHMARK SUMMARY")
    log("=" * 88)
    max_sql_rate = max(r["users_per_sec"] for r in sql_results)
    avg_sql_rate = sum(r["users_per_sec"] for r in sql_results) / len(sql_results)
    max_e2e_rate = max(r["users_per_sec"] for r in e2e_results)

    log(f"• Peak Database Generation Throughput: {max_sql_rate:.1f} users/second")
    log(f"• Average Database Generation Throughput: {avg_sql_rate:.1f} users/second")
    log(f"• Peak Web E2E (HTTP + Render) Throughput: {max_e2e_rate:.1f} users/second")
    log(f"• Average per-user generation cost: ~{1000/avg_sql_rate:.2f} ms per full profile")
    log("================================================================================\n")


if __name__ == "__main__":
    main()
