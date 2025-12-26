from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.weather_db

print("\n=== Contrôle du schéma MongoDB ===\n")

schema = {
    "measurements": {
        "station_id": str,
        "datetime": str,
        "temperature_c": (int, float),
        "wind_speed_kmh": (int, float)
    },
    "stations": {
        "station_id": str,
        "name": str,
        "latitude": (int, float),
        "longitude": (int, float)
    },
    "stations_infoclimat": {
        "id": str,
        "name": str,
        "latitude": (int, float),
        "longitude": (int, float)
    }
}

for col_name, fields in schema.items():
    col = db[col_name]
    print(f"Collection : {col_name}")

    for field, expected_type in fields.items():
        missing = col.count_documents({field: {"$exists": False}})
        print(f" - {field} manquant : {missing}")

    print()

