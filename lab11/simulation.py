"""
Лабораторная работа №11. Вариант 03 — Такси.
Симуляция стратегий шардирования для 12 000 поездок и 30 000 запросов.
Требуется Python 3.10+. Используются только стандартные библиотеки.
"""
import random
import hashlib
from collections import Counter

SEED = 42
N = 12_000
Q = 30_000
SHARDS = 3
DRIVERS = 2_000
CITIES = 5

random.seed(SEED)

# Синтетические документы поездок такси.
rows = [
    {
        "driverId": i % DRIVERS,
        "cityId": i % CITIES,
        "tripId": i
    }
    for i in range(N)
]

def stable_hash(value):
    """Стабильный учебный хеш; не является алгоритмом MongoDB."""
    digest = hashlib.sha256(str(value).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")

# Кандидат A: низкокардинальный ключ cityId.
def by_city(row):
    return row["cityId"] % SHARDS

# Кандидат B: хешированный ключ driverId.
def by_hashed_driver(row):
    return stable_hash(row["driverId"]) % SHARDS

# Кандидат C: диапазонный последовательный ключ tripId.
def by_trip_range(row):
    return min(row["tripId"] // (N // SHARDS), SHARDS - 1)

def make_requests(dataset):
    uniform = random.choices(dataset, k=Q)
    city_zero = [row for row in dataset if row["cityId"] == 0]
    hot = [
        random.choice(city_zero) if random.random() < 0.60
        else random.choice(dataset)
        for _ in range(Q)
    ]
    return uniform, hot

def metrics(assign, dataset, requests):
    doc_counts = Counter(assign(row) for row in dataset)
    query_counts = Counter(assign(row) for row in requests)
    docs = [doc_counts[i] for i in range(SHARDS)]
    queries = [query_counts[i] for i in range(SHARDS)]
    mean_docs = sum(docs) / SHARDS
    mean_queries = sum(queries) / SHARDS
    return {
        "docs": docs,
        "queries": queries,
        "doc_pct": [x / len(dataset) * 100 for x in docs],
        "query_pct": [x / len(requests) * 100 for x in queries],
        "doc_max_mean": max(docs) / mean_docs,
        "query_max_mean": max(queries) / mean_queries,
        "query_max_min": max(queries) / min(queries) if min(queries) else float("inf")
    }

def show_result(name, result):
    print(f"\n{name}")
    print("  Документы по шардам:", result["docs"])
    print("  Запросы по шардам:  ", result["queries"])
    print("  Доли запросов, %:   ", [round(x, 2) for x in result["query_pct"]])
    print("  Max/mean запросов:  ", round(result["query_max_mean"], 2))
    print("  Max/min запросов:   ", round(result["query_max_min"], 2))

def run_baseline():
    uniform, hot = make_requests(rows)
    candidates = [
        ("cityId / ranged (A)", by_city),
        ("driverId / hashed (B)", by_hashed_driver),
        ("tripId / ranged (C)", by_trip_range),
    ]
    results = {}
    for name, assign in candidates:
        for mode, requests in (("uniform", uniform), ("hot", hot)):
            result = metrics(assign, rows, requests)
            results[(name, mode)] = result
            show_result(f"{name} — {mode}", result)
    return results

def run_skewed_city_experiment():
    # Ровно 80% записей относятся к cityId=0, остальные 20% — к городам 1–4.
    skewed = []
    for i in range(N):
        city_id = 0 if i % 5 != 4 else 1 + (i % 4)
        skewed.append({
            "driverId": i % DRIVERS,
            "cityId": city_id,
            "tripId": i
        })
    uniform, hot = make_requests(skewed)
    print("\nЭКСПЕРИМЕНТ: 80% документов в одном городе (cityId=0)")
    for name, assign in (
        ("cityId / ranged (A)", by_city),
        ("driverId / hashed (B)", by_hashed_driver),
        ("tripId / ranged (C)", by_trip_range),
    ):
        for mode, requests in (("uniform", uniform), ("hot", hot)):
            result = metrics(assign, skewed, requests)
            show_result(f"{name} — {mode}", result)

if __name__ == "__main__":
    print(f"seed={SEED}, documents={N}, queries={Q}, shards={SHARDS}")
    run_baseline()
    run_skewed_city_experiment()
