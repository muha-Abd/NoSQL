"""Создание воспроизводимого набора синтетических билетов (вариант 19)."""
import os
import random
import time
from pymongo import MongoClient

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "nosql_lab12_variant19")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "tickets")
SEED = 42
DOCUMENTS = 5000

def main():
    random.seed(SEED)
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")
    coll = client[DB_NAME][COLLECTION_NAME]

    # Удаляется только учебная коллекция, созданная для этой лабораторной.
    coll.drop()
    zones = ["A", "B", "C", "D", "VIP"]
    rows = []
    for i in range(DOCUMENTS):
        rows.append({
            "ticketId": i + 1,
            "eventId": random.randint(1, 50),
            "zone": random.choice(zones),
            "title": f"Event {random.randint(1, 50)}",
            "seat": random.randint(1, 500),
            "price": random.randint(1000, 25000),
            "customerId": random.randint(1, 3000)
        })

    started = time.perf_counter()
    coll.insert_many(rows)
    insert_seconds = time.perf_counter() - started
    print(f"Документов: {coll.count_documents({})}")
    print(f"Seed: {SEED}")
    print(f"Время вставки без составного индекса: {insert_seconds:.6f} сек.")
    print(f"MongoDB version: {client.server_info().get('version')}")
    client.close()

if __name__ == "__main__":
    main()
