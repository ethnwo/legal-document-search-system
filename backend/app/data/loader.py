
import json
import os
from pathlib import Path


def load_cases():
    project_root = Path(__file__).resolve().parents[3]

    data_path = Path(
        os.getenv(
            "CASES_PATH",
            str(project_root / "data" / "processed" / "cases.json")
        )
    )

    with open(data_path, "r", encoding="utf-8") as file:
        cases = json.load(file)

    return cases
