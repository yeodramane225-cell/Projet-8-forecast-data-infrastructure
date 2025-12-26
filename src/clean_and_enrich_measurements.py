from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27017/")
db = client["weather_db"]
col = db.measurements

cursor = col.find({})

for doc in cursor:
    raw = doc.get("_airbyte_data")
    if not raw:
        continue

    # _airbyte_data est une chaîne JSON → on la parse
    try:
        data = json.loads(raw)
    except Exception:
        continue

    update = {}

    # Temperature "56.8 °F" → °C
    if "Temperature" in data:
        try:
            temp_f = float(data["Temperature"].replace("°F", "").strip())
            update["temperature_c"] = (temp_f - 32) * 5/9
        except:
            pass

    # Humidity "87 %" → 87
    if "Humidity" in data:
        try:
            update["humidity"] = float(data["Humidity"].replace("%", "").strip())
        except:
            pass

    # Pressure "29.48 in" → hPa
    if "Pressure" in data:
        try:
            pressure_in = float(data["Pressure"].replace("in", "").strip())
            update["pressure_hpa"] = pressure_in * 33.8639
        except:
            pass

    # Wind direction
    if "Wind" in data:
        update["wind_direction"] = data["Wind"]

    # Wind speed "8.2 mph" → km/h
    if "Speed" in data:
        try:
            update["wind_speed_kmh"] = float(data["Speed"].replace("mph", "").strip()) * 1.60934
        except:
            pass

    # Precipitation "0.00 in" → mm
    if "Precip. Accum." in data:
        try:
            prec_in = float(data["Precip. Accum."].replace("in", "").strip())
            update["precip_mm"] = prec_in * 25.4
        except:
            pass

    # Mise à jour du document
    if update:
        col.update_one({"_id": doc["_id"]}, {"$set": update})

print("Nettoyage terminé.")

