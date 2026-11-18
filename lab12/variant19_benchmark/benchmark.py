import os, csv, json, math, time, statistics, platform
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt

URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB = os.getenv("DB_NAME", "nosql_lab12_variant19")
COLL = os.getenv("COLLECTION_NAME", "tickets")
INDEX_NAME = "idx_eventId_zone"
QUERY = {"eventId": 10, "zone": "A"}
CLIENT_LEVELS = [1, 4, 8]
REPEATS = 3
REQUESTS_PER_REPEAT = 400
WARMUP_REQUESTS = 40

def percentile(values, p):
    values = sorted(values)
    if not values:
        return float("nan")
    pos = (len(values) - 1) * p / 100
    lo, hi = math.floor(pos), math.ceil(pos)
    return values[lo] + (values[hi] - values[lo]) * (pos - lo)

def one(coll):
    start = time.perf_counter()
    try:
        list(coll.find(QUERY).limit(100))
        return (time.perf_counter() - start) * 1000, True
    except Exception:
        return (time.perf_counter() - start) * 1000, False

def run_once(coll, workers):
    for _ in range(WARMUP_REQUESTS):
        one(coll)  # warm-up не включается в измерения
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda _: one(coll), range(REQUESTS_PER_REPEAT)))
    elapsed = time.perf_counter() - started
    latencies = [ms for ms, ok in results if ok]
    successes = len(latencies)
    errors = REQUESTS_PER_REPEAT - successes
    return {
        "workers": workers, "success": successes, "errors": errors,
        "attempts": REQUESTS_PER_REPEAT, "duration_sec": elapsed,
        "rps": successes / elapsed if elapsed else 0,
        "p50_ms": percentile(latencies, 50),
        "p95_ms": percentile(latencies, 95),
        "p99_ms": percentile(latencies, 99),
        "latencies_ms": [ms for ms, ok in results]
    }

def explain(coll, filename):
    result = coll.find(QUERY).limit(100).explain()
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    stats = result.get("executionStats", {})
    return {
        "winningPlan": result.get("queryPlanner", {}).get("winningPlan", {}),
        "totalDocsExamined": stats.get("totalDocsExamined"),
        "totalKeysExamined": stats.get("totalKeysExamined"),
        "executionTimeMillis": stats.get("executionTimeMillis")
    }

def main():
    client = MongoClient(URI, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")
    coll = client[DB][COLL]
    count = coll.count_documents({})
    if count < 5000:
        raise RuntimeError(f"В коллекции только {count} документов. Сначала выполните: python seed.py")

    server = client.server_info()
    meta = {
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "mongodb_version": server.get("version"),
        "python_version": platform.python_version(),
        "documents": count,
        "seed": 42,
        "query": QUERY,
        "requests_per_repeat": REQUESTS_PER_REPEAT,
        "warmup_requests": WARMUP_REQUESTS
    }
    with open("environment.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # Удаляем только индекс, который создаёт эта лабораторная работа.
    if INDEX_NAME in coll.index_information():
        coll.drop_index(INDEX_NAME)

    explain(coll, "explain_before.json")
    raw_rows = []
    for workers in CLIENT_LEVELS:
        for repeat in range(1, REPEATS + 1):
            result = run_once(coll, workers)
            raw_rows.append({k: v for k, v in result.items() if k != "latencies_ms"} |
                            {"mode": "Без индекса", "repeat": repeat})
            print("Без индекса", "клиенты:", workers, "повтор:", repeat,
                  "RPS:", round(result["rps"], 2), "P95:", round(result["p95_ms"], 3))

    coll.create_index([("eventId", 1), ("zone", 1)], name=INDEX_NAME)
    explain(coll, "explain_after.json")
    for workers in CLIENT_LEVELS:
        for repeat in range(1, REPEATS + 1):
            result = run_once(coll, workers)
            raw_rows.append({k: v for k, v in result.items() if k != "latencies_ms"} |
                            {"mode": "С индексом", "repeat": repeat})
            print("С индексом", "клиенты:", workers, "повтор:", repeat,
                  "RPS:", round(result["rps"], 2), "P95:", round(result["p95_ms"], 3))

    raw = pd.DataFrame(raw_rows)
    raw.to_csv("raw_results.csv", index=False, encoding="utf-8-sig")
    summary = (raw.groupby(["mode", "workers"])
               .agg(RPS_median=("rps", "median"),
                    P50_median_ms=("p50_ms", "median"),
                    P95_median_ms=("p95_ms", "median"),
                    P99_median_ms=("p99_ms", "median"),
                    errors_total=("errors", "sum"),
                    attempts_total=("attempts", "sum"),
                    duration_median_sec=("duration_sec", "median"))
               .reset_index())
    summary["error_rate_pct"] = summary["errors_total"] / summary["attempts_total"] * 100
    summary.to_csv("results.csv", index=False, encoding="utf-8-sig")

    # Два графика из медианных значений трёх повторов.
    for metric, ylabel, filename in [
        ("P95_median_ms", "P95, мс", "p95_by_clients.png"),
        ("RPS_median", "Throughput, запросов/с", "throughput_by_clients.png")
    ]:
        plt.figure(figsize=(8, 5))
        for mode in ["Без индекса", "С индексом"]:
            subset = summary[summary["mode"] == mode].sort_values("workers")
            plt.plot(subset["workers"], subset[metric], marker="o", label=mode)
        plt.xlabel("Количество параллельных клиентов")
        plt.ylabel(ylabel)
        plt.title(f"{ylabel} в зависимости от числа клиентов")
        plt.xticks(CLIENT_LEVELS)
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(filename, dpi=160)
        plt.close()

    stats = coll.database.command("collStats", COLL)
    with open("index_stats.json", "w", encoding="utf-8") as f:
        json.dump({
            "totalIndexSize_bytes": stats.get("totalIndexSize"),
            "indexSizes_bytes": stats.get("indexSizes", {}),
            "index_information": coll.index_information()
        }, f, ensure_ascii=False, indent=2, default=str)

    print("\\nГотово: raw_results.csv, results.csv, explain_before.json, explain_after.json")
    print("Графики: p95_by_clients.png, throughput_by_clients.png")
    client.close()

if __name__ == "__main__":
    main()
