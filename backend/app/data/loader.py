import json
from pathlib import Path

def load_cases():
    data_path = Path(__file__).resolve().parents[3] / "data" / "processed" / "cases.json"
    with open(data_path, "r", encoding="utf-8") as file:
        cases = json.load(file)
        
    return cases