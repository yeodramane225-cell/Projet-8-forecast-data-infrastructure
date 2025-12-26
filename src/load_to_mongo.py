import json
from pymongo import MongoClient

# -----------------------------
# CONFIG
# -----------------------------
# Dans Docker, le service MongoDB s'appelle "mongodb"
MONGO_URI = "mongodb://mongodb:27017/"
DB_NAME = "weather_db"

# Fichiers produits par transform.py (dans /app/output/)
STATIONS_FILE = "/app/output/stations.jsonl"
MEASUREMENTS_FILE = "/app/output/measurements.jsonl"
INFOCLIMAT_FILE = "/app/output/stations_infoclimat.jsonl"

# -----------------------------
# FONCTIONS UTILES
# -----------------------------
def load_jsonl(path):
    """Charge un fichier JSONL et retourne une liste de dict."""
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    return data

# -----------------------------
# MAIN
# -----------------------------
def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # -----------------------------
    # 1) Chargement des données
    # -----------------------------
    raw_stations = load_jsonl(STATIONS_FILE)
    measurements = load_jsonl(MEASUREMENTS_FILE)
    raw_infoclimat = load_jsonl(INFOCLIMAT_FILE)

    # -----------------------------
    # 2) Correction du mapping WU
    # -----------------------------
    stations = []
    for s in raw_stations:
        stations.append({
            "station_id": s["weather_station_id"],
            "name": s["station_name"],
            "latitude": s["latitude"],
            "longitude": s["longitude"]
        })

    # -----------------------------
    # 3) Extraction des stations InfoClimat
    # -----------------------------
    infoclimat = []
    for block in raw_infoclimat:
        for st in block.get("stations", []):
            infoclimat.append({
                "id": st["id"],
                "name": st["name"],
                "latitude": st["latitude"],
                "longitude": st["longitude"]
            })

    # -----------------------------
    # 4) Insertion dans MongoDB
    # -----------------------------
    db.stations.delete_many({})
    db.measurements.delete_many({})
    db.stations_infoclimat.delete_many({})

    result_stations = db.stations.insert_many(stations)
    result_measurements = db.measurements.insert_many(measurements)
    result_infoclimat = db.stations_infoclimat.insert_many(infoclimat)

    # -----------------------------
    # 5) Résumé clair
    # -----------------------------
    print("=== Résumé de l'insertion ===")
    print(f"Stations WU insérées : {len(result_stations.inserted_ids)}")
    print(f"Mesures insérées : {len(result_measurements.inserted_ids)}")
    print(f"Stations InfoClimat insérées : {len(result_infoclimat.inserted_ids)}")
    print("\nInsertion terminée avec succès.")

if __name__ == "__main__":
    main()

