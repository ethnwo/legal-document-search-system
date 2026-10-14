import sqlite3
from pathlib import Path

DEFAULT_SOURCE = "Original dataset"

def get_database_path():
    return Path("/var/data/appdata/metadata.db")

class MetadataStore:
    def __init__(self):
        self.database_path = get_database_path()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self):
        with self.connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY,
                    case_name TEXT,
                    decision_date TEXT,
                    court TEXT,
                    jurisdiction TEXT,
                    citation TEXT,
                    source TEXT
                )
            """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_cases_decision_date
                ON cases(decision_date)
            """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_cases_court
                ON cases(court)
            """)

    def import_cases(self, cases):
        with self.connect() as connection:
            for case in cases:
                case_id = case.get("case_id")

                if case_id is None:
                    continue

                connection.execute("""
                    INSERT INTO cases (
                        case_id,
                        case_name,
                        decision_date,
                        court,
                        jurisdiction,
                        citation,
                        source
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)

                    ON CONFLICT(case_id) DO UPDATE SET
                        case_name = COALESCE(
                            excluded.case_name,
                            cases.case_name
                        ),
                        decision_date = COALESCE(
                            excluded.decision_date,
                            cases.decision_date
                        ),
                        court = COALESCE(
                            excluded.court,
                            cases.court
                        ),
                        jurisdiction = COALESCE(
                            excluded.jurisdiction,
                            cases.jurisdiction
                        ),
                        citation = COALESCE(
                            excluded.citation,
                            cases.citation
                        ),
                        source = COALESCE(
                            excluded.source,
                            cases.source
                        )
                """, (
                    str(case_id),
                    case.get("case_name"),
                    case.get("decision_date"),
                    case.get("court"),
                    case.get("jurisdiction"),
                    case.get("citation"),
                    case.get("source") or DEFAULT_SOURCE
                ))

    def get_many(self, case_ids):
        case_ids = list(dict.fromkeys(
            str(case_id)
            for case_id in case_ids
            if case_id is not None
        ))

        if not case_ids:
            return {}

        placeholders = ", ".join("?" for _ in case_ids)

        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM cases
                WHERE case_id IN ({placeholders})
                """,
                case_ids
            ).fetchall()

            return {
                row["case_id"]: dict(row)
                for row in rows
            }

    def get_filtered_case_ids(self, court=None, jurisdiction=None, start_date=None, end_date=None):
        conditions = []
        parameters = []

        if court:
            conditions.append("court = ?")
            parameters.append(court)

        if jurisdiction:
            conditions.append("jurisdiction = ?")
            parameters.append(jurisdiction)

        if start_date:
            conditions.append("decision_date >= ?")
            parameters.append(start_date)

        if end_date:
            conditions.append("decision_date <= ?")
            parameters.append(end_date)

        sql= "SELECT case_id FROM cases"

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        with self.connect() as connection:
            rows = connection.execute(
                sql,
                parameters
            ).fetchall()

        return {
            row["case_id"]
            for row in rows
        }


    def get_filter_options(self):
        """Return distinct court and jurisdiction values for the UI."""
        with self.connect() as connection:
            courts = connection.execute("""
                SELECT DISTINCT court
                FROM cases
                WHERE court IS NOT NULL AND TRIM(court) != ''
                ORDER BY court
            """).fetchall()

            jurisdictions = connection.execute("""
                SELECT DISTINCT jurisdiction
                FROM cases
                WHERE jurisdiction IS NOT NULL
                  AND TRIM(jurisdiction) != ''
                ORDER BY jurisdiction
            """).fetchall()

        return {
            "courts": [row["court"] for row in courts],
            "jurisdictions": [
                row["jurisdiction"] for row in jurisdictions
            ]
        }

