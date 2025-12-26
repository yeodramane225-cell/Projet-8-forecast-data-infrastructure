from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["weather_db"]
col = db.measurements

# On trie par station puis par datetime
cursor = col.find({}).sort([
    ("weather_station_id", 1),
    ("datetime", 1)
])

previous = {}  # mémorise le cumul précédent par station

for doc in cursor:
    station = doc.get("weather_station_id")
    current_cumul = doc.get("precip_mm")
    dt = doc.get("datetime")

    if station is None or current_cumul is None or dt is None:
        continue

    # Si c'est la première mesure de la station → pas de pluie instantanée
    if station not in previous:
        previous[station] = current_cumul
        hourly = 0.0
    else:
        prev_cumul = previous[station]

        # Si le cumul repart à zéro → nouveau jour
        if current_cumul < prev_cumul:
            hourly = current_cumul
        else:
            hourly = current_cumul - prev_cumul

        previous[station] = current_cumul

    # Mise à jour du document
    col.update_one(
        {"_id": doc["_id"]},
        {"$set": {"precip_mm_hourly": hourly}}
    )

# -----------------------------
# DELETE : suppression du champ _airbyte_data
# -----------------------------
result = col.update_many({}, { "$unset": { "_airbyte_data": "" } })
print(f"Champs _airbyte_data supprimés dans {result.modified_count} documents.")

print("Calcul des précipitations horaires terminé.")

