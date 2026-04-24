"""
Migration: normalize analysis_outputs → analysis_module_outputs.

Run once before deploying the new code:

    python scripts/migrate_analysis_outputs.py

What this does:
1. Creates the new analysis_module_outputs table (idempotent via CREATE IF NOT EXISTS).
2. Reads every row from the legacy analysis_outputs table.
3. Inserts one analysis_module_outputs row per non-NULL JSON column.
4. Renames the legacy table to analysis_outputs_legacy (preserves data, does not drop).

Safe to re-run: step 3 uses INSERT ... ON CONFLICT DO NOTHING so duplicate runs
are harmless. The rename in step 4 is skipped if the legacy table was already renamed.
"""
import sys
import os

# Allow running from the project root without installing the package.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config import settings


MODULES = ["legal", "risk", "valuation", "final"]

CREATE_MODULE_OUTPUTS = """
CREATE TABLE IF NOT EXISTS analysis_module_outputs (
    id           SERIAL PRIMARY KEY,
    analysis_id  INTEGER NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    module_name  VARCHAR(50) NOT NULL,
    output_json  JSONB,
    status       VARCHAR(20) NOT NULL DEFAULT 'completed',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_analysis_module UNIQUE (analysis_id, module_name)
);

CREATE INDEX IF NOT EXISTS idx_module_outputs_analysis_id
    ON analysis_module_outputs (analysis_id);
"""

INSERT_MODULE = """
INSERT INTO analysis_module_outputs (analysis_id, module_name, output_json, status, created_at)
VALUES (:analysis_id, :module_name, :output_json, 'completed', NOW())
ON CONFLICT (analysis_id, module_name) DO NOTHING;
"""

CHECK_LEGACY_EXISTS = """
SELECT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'analysis_outputs'
);
"""

RENAME_LEGACY = """
ALTER TABLE analysis_outputs RENAME TO analysis_outputs_legacy;
"""


def run(database_url: str) -> None:
    engine = create_engine(database_url)

    with engine.begin() as conn:
        print("Step 1: creating analysis_module_outputs table (idempotent)...")
        conn.execute(text(CREATE_MODULE_OUTPUTS))
        print("  done.")

        legacy_exists = conn.execute(text(CHECK_LEGACY_EXISTS)).scalar()
        if not legacy_exists:
            print("Step 2: legacy table analysis_outputs not found — skipping data copy.")
        else:
            print("Step 2: copying legacy rows into analysis_module_outputs...")
            rows = conn.execute(
                text("SELECT analysis_id, legal_json, risk_json, valuation_json, final_json FROM analysis_outputs")
            ).fetchall()
            print(f"  found {len(rows)} legacy rows.")

            inserted = 0
            for row in rows:
                analysis_id = row[0]
                for idx, module_name in enumerate(MODULES):
                    payload = row[idx + 1]
                    if payload is None:
                        continue
                    import json
                    conn.execute(
                        text(INSERT_MODULE),
                        {
                            "analysis_id": analysis_id,
                            "module_name": module_name,
                            "output_json": json.dumps(payload) if not isinstance(payload, str) else payload,
                        },
                    )
                    inserted += 1

            print(f"  inserted {inserted} module output rows.")

            print("Step 3: renaming analysis_outputs → analysis_outputs_legacy...")
            conn.execute(text(RENAME_LEGACY))
            print("  done. Legacy data preserved in analysis_outputs_legacy.")

    print("Migration complete.")


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
    print(f"Connecting to: {db_url.split('@')[-1]}")  # log host only, not credentials
    run(db_url)
