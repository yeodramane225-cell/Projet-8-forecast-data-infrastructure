from pymongo import MongoClient
import json
from datetime import datetime, timezone

client = MongoClient("mongodb://localhost:27017/")
db = client["weather_db"]
col = db.measurements

cursor = col.find({})

for doc in cursor:
    raw = doc.get("_airbyte_data")
    ts = doc.get("_airbyte_extracted_at")

    if not raw or not ts:
        continue

    # Parse JSON Airbyte
    try:
        data = json.loads(raw)
    except Exception:
        continue

    # Récupérer l'heure "HH:MM:SS"
    time_str = data.get("Time")
    if not time_str:
        continue

    # Convertir timestamp UNIX ms → date
    try:
        dt_base = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        date_str = dt_base.strftime("%Y-%m-%d")
    except Exception:
        continue

    # Construire datetime complet
    try:
        full_dt = datetime.fromisoformat(f"{date_str} {time_str}").replace(tzinfo=timezone.utc)
    except Exception:
        continue

    # Mise à jour MongoDB
    col.update_one(
        {"_id": doc["_id"]},
        {"$set": {"datetime": full_dt}}
    )

print("Ajout du champ datetime terminé.")

