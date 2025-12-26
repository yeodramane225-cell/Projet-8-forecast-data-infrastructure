import pandas as pd
import os

def load_local_files(path):
    files = [
        os.path.join(path, f)
        for f in os.listdir(path)
        if f.endswith((".xlsx", ".csv", ".json"))
    ]
    return files

def load_file(filepath):
    if filepath.endswith(".xlsx"):
        return pd.read_excel(filepath)
    if filepath.endswith(".csv"):
        return pd.read_csv(filepath)
    if filepath.endswith(".json"):
        return pd.read_json(filepath)
    raise ValueError(f"Format non supporté : {filepath}")
