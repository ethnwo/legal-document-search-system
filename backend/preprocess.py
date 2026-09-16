import json
import re
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
raw_directory = project_root / "data" / "raw"
processed_directory = project_root / "data" / "processed"

start_volume = 905
end_volume = 935

def clean_text(text):
    if not text:
        return ""
    
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def extract_case(case_data):
    case_id = case_data.get("id")
    case_name = case_data.get("name")
    decision_date = case_data.get("decision_date")

    court_data = case_data.get("court") or {}
    court = court_data.get("name")

    jurisdiction_data = case_data.get("jurisdiction") or {}
    jurisdiction = jurisdiction_data.get("name")

    citation = None
    citations = case_data.get()