import os
import json
import pandas as pd

# Dossier des données brutes (CSV WU + JSONL InfoClimat)
# Dans Docker, /app = dossier src/
RAW_DIR = "/app/data/raw"

# ---------------------------------------------------------
# 1. Métadonnées stations (énoncé du projet)
# ---------------------------------------------------------

STATIONS_METADATA = {
    "WU_Ichtegem": {
        "weather_station_id": "IICHTE19",
        "station_name": "WeerstationBS",
        "latitude": 51.092,
        "longitude": 2.999,
        "elevation": 15,
        "city": "Ichtegem",
        "state": "-/-",
        "hardware": "other",
        "software": "EasyWeatherV1.6.6",
    },
    "WU_LaMadeleine": {
        "weather_station_id": "ILAMAD25",
        "station_name": "La Madeleine",
        "latitude": 50.659,
        "longitude": 3.07,
        "elevation": 23,
        "city": "La Madeleine",
        "state": "-/-",
        "hardware": "other",
        "software": "EasyWeatherPro_V5.1.6",
    },
}

# ---------------------------------------------------------
# 2. Chargement des CSV Weather Underground
# ---------------------------------------------------------

def load_weather_csv(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    base = os.path.basename(csv_path)
    station_key = base.replace(".csv", "")

    meta = STATIONS_METADATA.get(station_key, {})
    if not meta:
        print(f"Aucune métadonnée trouvée pour {station_key}, seulement station_key ajouté.")
        df["station_key"] = station_key
    else:
        for k, v in meta.items():
            df[k] = v
        df["station_key"] = station_key

    return df

# ---------------------------------------------------------
# 3. Chargement du JSONL InfoClimat
# ---------------------------------------------------------

def load_infoclimat_stations(jsonl_path: str) -> pd.DataFrame:
    records = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    df = pd.DataFrame(records)

    if "_airbyte_data" not in df.columns:
        print("Pas de colonne _airbyte_data, JSONL non-Airbyte, on renvoie brut.")
        return df

    df = pd.json_normalize(df["_airbyte_data"])
    return df

# ---------------------------------------------------------
# 4. Tests d’intégrité simples
# ---------------------------------------------------------

def basic_integrity_report(name: str, df: pd.DataFrame) -> None:
    print(f"\n Rapport d'intégrité pour {name}")
    print(f"→ Nombre de lignes : {len(df)}")
    print("→ Colonnes :", list(df.columns))
    print("→ Types :")
    print(df.dtypes)
    print("→ Valeurs manquantes par colonne :")
    print(df.isna().sum())

# ---------------------------------------------------------
# 5. Normalisation colonnes pour MongoDB
# ---------------------------------------------------------

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
    )
    return df

# ---------------------------------------------------------
# 6. Préparation des collections pour MongoDB
# ---------------------------------------------------------

def build_stations_collection() -> list[dict]:
    docs = []
    for key, meta in STATIONS_METADATA.items():
        doc = {"station_key": key, **meta}
        docs.append(doc)
    return docs


def build_measurements_collection(weather_df: pd.DataFrame) -> list[dict]:
    df = normalize_columns(weather_df)
    docs = []

    for _, row in df.iterrows():

        # 1) Parser le JSON brut Airbyte
        try:
            data = json.loads(row["_airbyte_data"])
        except Exception:
            continue

        # 2) Extraire les champs bruts
        temp_f = data.get("Temperature")
        wind_mph = data.get("Speed")
        humidity_raw = data.get("Humidity")
        pressure_in = data.get("Pressure")
        time_raw = data.get("Time")

        # 3) Nettoyage et conversions

        # Température °F → °C
        temp_c = None
        if isinstance(temp_f, str):
            try:
                value = float(
                    temp_f.replace("°F", "")
                    .replace("Â", "")
                    .replace("\u00b0F", "")
                    .strip()
                )
                temp_c = round((value - 32) * 5 / 9, 2)
            except Exception:
                pass

        # Vent mph → km/h
        wind_speed_kmh = None
        if isinstance(wind_mph, str):
            try:
                value = float(
                    wind_mph.replace("mph", "")
                    .replace("Â", "")
                    .strip()
                )
                wind_speed_kmh = round(value * 1.60934, 2)
            except Exception:
                pass

        # Humidité "87 %"/"87 %" → 87
        humidity = None
        if isinstance(humidity_raw, str):
            try:
                humidity = int(
                    humidity_raw.replace("%", "")
                    .replace("\u00a0", "")
                    .strip()
                )
            except Exception:
                pass

        # Pression "29.47 in" → hPa
        pressure_hpa = None
        if isinstance(pressure_in, str):
            try:
                value = float(
                    pressure_in.replace("in", "")
                    .replace("\u00a0", "")
                    .strip()
                )
                pressure_hpa = round(value * 33.8639, 2)
            except Exception:
                pass

        # 4) Construire le document final
        doc = {
            "datetime": time_raw,
            "temperature_c": temp_c,
            "wind_speed_kmh": wind_speed_kmh,
            "humidity": humidity,
            "pressure_hpa": pressure_hpa,
            "station_id": row.get("weather_station_id"),
            "station_key": row.get("station_key"),
            "latitude": row.get("latitude"),
            "longitude": row.get("longitude"),
        }

        docs.append(doc)

    return docs


def build_infoclimat_collection(infoclimat_df: pd.DataFrame) -> list[dict]:
    df = normalize_columns(infoclimat_df)
    return df.to_dict("records")

# ---------------------------------------------------------
# 7. Détection des fichiers dans data/raw
# ---------------------------------------------------------

def detect_files():
    files = os.listdir(RAW_DIR)
    csv_files = [f for f in files if f.endswith(".csv")]
    jsonl_files = [f for f in files if f.endswith(".jsonl")]
    return csv_files, jsonl_files

# ---------------------------------------------------------
# 8. Main pipeline
# ---------------------------------------------------------

def main():
    print("Détection des fichiers dans data/raw…")
    csv_files, jsonl_files = detect_files()

    print(f"→ CSV trouvés : {csv_files}")
    print(f"→ JSONL trouvés : {jsonl_files}")

    # 1) Charger et concaténer les mesures météo
    print("\n Chargement des mesures météo (WU)…")
    weather_dfs = []
    for csv in csv_files:
        path = os.path.join(RAW_DIR, csv)
        df = load_weather_csv(path)
        weather_dfs.append(df)
        print(f"→ {csv} : {len(df)} lignes")

    if weather_dfs:
        weather_df = pd.concat(weather_dfs, ignore_index=True)
    else:
        raise FileNotFoundError("Aucun CSV trouvé pour les mesures météo.")

    basic_integrity_report("mesures WU (brut)", weather_df)

    # 2) Charger InfoClimat
    infoclimat_df = None
    if jsonl_files:
        print("\n Chargement des métadonnées InfoClimat (JSONL)…")
        jsonl_path = os.path.join(RAW_DIR, jsonl_files[0])
        infoclimat_df = load_infoclimat_stations(jsonl_path)
        basic_integrity_report("stations InfoClimat (extrait)", infoclimat_df)
    else:
        print("\n Aucun JSONL InfoClimat trouvé, la collection 'stations_infoclimat' sera vide.")

    # 3) Construire les collections
    print("\n Construction des collections MongoDB…")

    stations_docs = build_stations_collection()
    measurements_docs = build_measurements_collection(weather_df)
    infoclimat_docs = build_infoclimat_collection(infoclimat_df) if infoclimat_df is not None else []

    print(f"→ stations : {len(stations_docs)} documents")
    print(f"→ measurements : {len(measurements_docs)} documents")
    print(f"→ stations_infoclimat : {len(infoclimat_docs)} documents")

    print("\n Exemple document 'stations' :")
    if stations_docs:
        print(stations_docs[0])

    print("\n Exemple document 'measurements' :")
    if measurements_docs:
        print(measurements_docs[0])

    if infoclimat_docs:
        print("\n Exemple document 'stations_infoclimat' :")
        print(infoclimat_docs[0])

    # ---------------------------------------------------------
    # 9. Export JSONL pour load_to_mongo.py
    # ---------------------------------------------------------

    OUTPUT_DIR = "/app/output"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    def write_jsonl(path, docs):
        with open(path, "w", encoding="utf-8") as f:
            for d in docs:
                f.write(json.dumps(d) + "\n")

    print("\n Export des fichiers transformés…")

    write_jsonl(os.path.join(OUTPUT_DIR, "stations.jsonl"), stations_docs)
    write_jsonl(os.path.join(OUTPUT_DIR, "measurements.jsonl"), measurements_docs)
    write_jsonl(os.path.join(OUTPUT_DIR, "stations_infoclimat.jsonl"), infoclimat_docs)

    print("→ Export terminé.")

if __name__ == "__main__":
    main()

