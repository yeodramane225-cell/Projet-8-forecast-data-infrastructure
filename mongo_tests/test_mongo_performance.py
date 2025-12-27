from pymongo import MongoClient
import time

start = time.time()

client = MongoClient("mongodb://172.31.9.224:27017/")
db = client["weather"]
collection = db["daily"]

query_start = time.time()
result = collection.find_one({"city": "Paris", "date": "2025-01-01"})
query_end = time.time()

print("Résultat :", result)
print("Temps de connexion :", query_start - start, "sec")
print("Temps de requête :", query_end - query_start, "sec")
print("Temps total :", query_end - start, "sec")

