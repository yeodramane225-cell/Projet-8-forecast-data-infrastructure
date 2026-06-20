Weather Data Pipeline
Airbyte → S3 → Transformation Python → MongoDB → Docker

Ce projet met en place un pipeline complet d’ingestion, transformation, nettoyage et migration de données météorologiques issues de Weather Underground et InfoClimat, avec stockage final dans MongoDB.
La dernière partie du projet consiste à conteneuriser l’ensemble du pipeline avec Docker.

Sommaire
Objectifs du projet

Architecture globale

Partie 1 — Airbyte & Transformation Python

Ingestion Airbyte

Structure du projet

Transformation Python

Tests d’intégrité

Logigramme ETL

Partie 2 — Migration MongoDB

Schéma des collections

Migration & CRUD

Qualité post‑migration

Réplication MongoDB

Partie 3 — Conteneurisation Docker

Dockerfile

docker-compose.yml

Exécution du pipeline

Vérification dans MongoDB

Environnement & Requirements

Conclusion

Objectifs du projet
Ingestion automatisée de données météo (Excel + JSON) via Airbyte

Stockage intermédiaire dans S3

Transformation Python :

extraction des données métier depuis _airbyte_data

nettoyage, normalisation, enrichissement

conversion d’unités (°F → °C, mph → km/h, inHg → hPa)

Génération de fichiers propres au format JSONL

Migration dans MongoDB

Contrôle qualité avant et après migration

Mise en place d’un replica set MongoDB

Conteneurisation complète du pipeline avec Docker

Documentation professionnelle du pipeline

Architecture globale
Code
Weather Underground / InfoClimat
                │
                ▼
            Airbyte
                │
                ▼
               S3
                │
                ▼
        Python (transform.py)
                │
                ▼
        JSONL transformés
                │
                ▼
            MongoDB
                │
                ▼
     Contrôle qualité + CRUD
Partie 1 — Airbyte & Transformation Python
Ingestion via Airbyte
Airbyte est utilisé pour :

se connecter aux fichiers Excel Weather Underground

se connecter aux données JSON InfoClimat

charger les données dans un bucket S3

produire des fichiers CSV/JSONL standardisés

Les données métier sont encapsulées dans :

Code
_airbyte_data
Structure du projet
Code
forecast_2_0/
├── data/
│   ├── raw/
│   │   ├── WU_Ichtegem.csv
│   │   ├── WU_LaMadeleine.csv
│   │   ├── InfoClimat_Stations.jsonl
│   │   └── raw.zip
│   ├── Weather+Underground-*.xlsx
├── src/
│   ├── transform.py
│   ├── quality.py
│   ├── load_to_mongo.py
│   ├── utils.py
│   └── config.py
├── requirements.txt
└── README.md
Les fichiers transformés sont générés dans :

Code
src/output/
Transformation Python
Le script transform.py réalise :

extraction des données métier depuis _airbyte_data

normalisation des colonnes

enrichissement avec les métadonnées des stations

conversion des unités

génération des collections logiques :

measurements.jsonl

stations.jsonl

stations_infoclimat.jsonl

Tests d’intégrité
Le script quality.py vérifie :

présence des colonnes attendues

types de données

valeurs manquantes

doublons

cohérence des formats

Logigramme ETL
Code
          [Début]
              |
              v
  [Collecte des données Airbyte → S3]
              |
              v
 [Extraction des fichiers bruts (CSV/JSONL)]
              |
              v
 [Transformation Python : nettoyage, normalisation,
         enrichissement des données]
              |
              v
   [Contrôle du schéma et qualité des données]
              |
              v
 [Génération des fichiers transformés (JSONL)]
              |
              v
     [Chargement des données dans MongoDB]
              |
              v
   [Mesure qualité post-migration MongoDB]
              |
              v
             [Fin]
Partie 2 — Migration MongoDB
Schéma des collections
measurements
datetime

temperature_c

wind_speed_kmh

humidity

pressure_hpa

station_id

station_key

latitude / longitude

stations
station_id

name

latitude

longitude

elevation

matériel / logiciel

stations_infoclimat
id

name

latitude

longitude

Migration des données
Le script load_to_mongo.py :

lit les fichiers JSONL transformés

nettoie les champs

insère les documents dans MongoDB

supprime les champs techniques Airbyte

Opérations CRUD
Les scripts Python permettent :

Create : insertion des documents

Read : requêtes, agrégations, filtres

Update : enrichissement, conversions

Delete : suppression des champs inutiles

Qualité post‑migration
Le script quality_mongo.py vérifie :

nombre total de documents

taux de valeurs manquantes

cohérence des types

conformité du schéma

Réplication MongoDB
Un replica set local a été mis en place :

nom : rs0

initialisation via rs.initiate()

vérification via rs.status()

Objectifs :

illustrer les bonnes pratiques

assurer une tolérance aux pannes

démontrer la réplication MongoDB

Partie 3 — Conteneurisation Docker
Objectifs
Conteneuriser le pipeline Python

Déployer MongoDB dans un conteneur dédié

Automatiser l’exécution complète via docker-compose

Garantir la reproductibilité du pipeline

Dockerfile (conteneur pipeline Python)
Situé dans src/Dockerfile :

dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "transform.py"]
docker-compose.yml (orchestration complète)
Situé à la racine :

yaml
version: "3.9"

services:
  mongodb:
    image: mongo:6
    container_name: weather_mongo
    restart: always
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  pipeline:
    build: ./src
    container_name: weather_pipeline
    depends_on:
      - mongodb
    volumes:
      - ./src/output:/app/output
      - ./data/raw:/app/data/raw
    command: >
      sh -c "python3 transform.py && python3 load_to_mongo.py"

volumes:
  mongo_data:
Exécution du pipeline Docker
Depuis la racine du projet :

Code
docker-compose up --build
Le pipeline effectue automatiquement :

transformation des données

génération des fichiers JSONL

insertion dans MongoDB

Vérification dans MongoDB
Code
docker exec -it weather_mongo mongosh
use weather_db
db.stations.count()
db.measurements.count()
db.stations_infoclimat.count()
Résultats obtenus :

stations : 2

measurements : 3807

stations_infoclimat : 4

Environnement & Requirements
Dépendances principales :

pandas

openpyxl

pymongo

boto3

python-dotenv

Conclusion
Ce projet couvre l’ensemble du cycle de vie d’un pipeline de données :

ingestion et standardisation via Airbyte

transformation et enrichissement via Python

migration et modélisation dans MongoDB

contrôle qualité avant et après migration

mise en place d’un replica set

conteneurisation complète avec Docker

Il constitue une base professionnelle, réutilisable et extensible pour l’exploitation de données météo dans un environnement NoSQL.
