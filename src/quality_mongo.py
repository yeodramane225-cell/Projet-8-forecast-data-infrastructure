from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.weather_db

collections = ["measurements", "stations", "stations_infoclimat"]

print("\n=== Mesure qualité post-migration (MongoDB) ===\n")

for col_name in collections:
    col = db[col_name]
    total = col.count_documents({})
    print(f"Collection : {col_name}")
    print(f" - Total documents : {total}")

    # Champs clés à vérifier selon la collection
    if col_name == "measurements":
        fields = ["datetime", "temperature_c", "wind_speed_kmh"]
    elif col_name == "stations":
        fields = ["station_id", "name", "latitude", "longitude"]
    else:
        fields = ["id", "name", "latitude", "longitude"]

    for field in fields:
        missing = col.count_documents({field: {"$exists": False}})
        print(f"   - {field} manquant : {missing}")

    print()

