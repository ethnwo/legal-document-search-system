import json
import re
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
raw_dir = root_dir / "data" / "raw"
processed_dir = root_dir / "data" / "processed"

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
    citations = case_data.get("citations") or []
    for citation_data in citations:
        if citation_data.get("type") == "official":
            citation = citation_data.get("cite")
            break

    casebody = case_data.get("casebody") or {}
    opinions = casebody.get("opinions") or []
    opinion_texts = []
    for opinion in opinions:
        text = opinion.get("text")
        if text:
            opinion_texts.append(text)

    full_text = clean_text("\n\n".join(opinion_texts))

    return {
        "case_id": case_id,
        "case_name": case_name,
        "decision_date": decision_date,
        "court": court,
        "jurisdiction": jurisdiction,
        "citation": citation,
        "text": full_text,
    }

def main():
    processed_dir.mkdir(parents=True, exist_ok=True)

    cases = []
    case_ids = set()

    total_files = 0
    skipped_files = 0
    duplicate_cases = 0

    print(f"Reading volumes {start_volume} to {end_volume}...\n")

    for volume_number in range(start_volume, end_volume + 1):
        json_dir = raw_dir / str(volume_number) / "json"
        if not json_dir.exists():
            print(f"! Volume {volume_number}: json folder not found")
            continue
        json_files = sorted(json_dir.glob("*.json"))
        print(
            f"Volume {volume_number}: "
            f"{len(json_files)} JSON files"
        )

        for json_file in json_files:
            total_files += 1
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    case_data = json.load(f)
                case = extract_case(case_data)

                if case["case_id"] is None:
                    skipped_files += 1
                    continue

                if case["case_id"] in case_ids:
                    duplicate_cases += 1
                    continue

                if not case["text"]:
                    skipped_files += 1
                    continue

                case_ids.add(case["case_id"])
                cases.append(case)

            except (json.JSONDecodeError, OSError) as e:
                print(f"! Could not process {json_file}: {e}")
                skipped_files += 1

    output_file = processed_dir / "cases.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 50)
    print("Preprocessing Complete")
    print("=" * 50)
    print(f"JSON files found:       {total_files}")
    print(f"Processed cases:        {len(cases)}")
    print(f"Skipped files:          {skipped_files}")
    print(f"Duplicate cases:        {duplicate_cases}")
    print(f"Output:                 {output_file}")
    print("=" * 50)

if __name__ == "__main__":
    main()