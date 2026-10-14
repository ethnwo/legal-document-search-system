import json
from pathlib import Path

def load_cases():
    data_path = Path("/var/data/data/processed/cases.json")
    with open(data_path, "r", encoding="utf-8") as file:
        cases = json.load(file)
        
    return cases