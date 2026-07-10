import argparse
import json
import sqlite3
from pathlib import Path


def create_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS review_analysis (
            product_id TEXT PRIMARY KEY,
            total_reviews INTEGER NOT NULL,
            pct_small REAL NOT NULL,
            pct_large REAL NOT NULL,
            pct_tts REAL NOT NULL,
            top_issues_json TEXT NOT NULL,
            analysis_mode TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )


def ingest(input_path: Path, db_path: Path) -> None:
    data = json.loads(input_path.read_text(encoding="utf-8"))

    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    create_table(conn)

    inserted = 0

    for item in data:
        product_id = item.get("product_id")

        if not product_id or product_id == "__benchmark__":
            continue

        conn.execute(
            """
            INSERT INTO review_analysis (
                product_id,
                total_reviews,
                pct_small,
                pct_large,
                pct_tts,
                top_issues_json,
                analysis_mode,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(product_id) DO UPDATE SET
                total_reviews = excluded.total_reviews,
                pct_small = excluded.pct_small,
                pct_large = excluded.pct_large,
                pct_tts = excluded.pct_tts,
                top_issues_json = excluded.top_issues_json,
                analysis_mode = excluded.analysis_mode,
                updated_at = excluded.updated_at
            """,
            (
                product_id,
                int(item.get("total_reviews", 0)),
                float(item.get("pct_small", 0)),
                float(item.get("pct_large", 0)),
                float(item.get("pct_tts", 0)),
                json.dumps(item.get("top_issues_json", [])),
                item.get("analysis_mode", "unknown"),
                item.get("updated_at", ""),
            ),
        )

        inserted += 1

    conn.commit()
    conn.close()

    print("DB ingest complete.")
    print(f"Input: {input_path}")
    print(f"Database: {db_path}")
    print(f"Rows inserted/updated: {inserted}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="data/processed/review_analysis.amd.240.json",
    )
    parser.add_argument(
        "--db",
        default="data/processed/fitos_ai_demo.sqlite",
    )
    args = parser.parse_args()

    ingest(Path(args.input), Path(args.db))
