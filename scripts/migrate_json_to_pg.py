#!/usr/bin/env python3
"""CLI: migrate JSON collections into the Postgres documents table.

    # preview what would migrate (no DB needed):
    python scripts/migrate_json_to_pg.py --dry-run

    # migrate (reads DATABASE_URL, or pass --database-url):
    DATABASE_URL=postgresql+psycopg://u:p@localhost:5432/db python scripts/migrate_json_to_pg.py

    # verify counts match afterwards:
    python scripts/migrate_json_to_pg.py --verify

Idempotent and non-destructive to JSON (each collection is replaced in Postgres;
the JSON files are never touched). See app/storage/migrate.py for the logic.
"""

from __future__ import annotations

import argparse
import os
import sys

# Make the backend package importable when run from the repo root.
_BACKEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend")
sys.path.insert(0, _BACKEND)

from app.config import DATA_DIR  # noqa: E402
from app.storage.migrate import migrate_json_to_postgres  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Migrate JSON collections into Postgres.")
    p.add_argument("--data-dir", default=DATA_DIR, help="JSON data directory (default: backend/app/data)")
    p.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="Postgres URL (or set DATABASE_URL)")
    p.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    p.add_argument("--verify", action="store_true", help="compare JSON vs Postgres counts")
    args = p.parse_args()

    report = migrate_json_to_postgres(
        args.data_dir, args.database_url, dry_run=args.dry_run, verify=args.verify
    )

    print(f"\n  migrate ({report['mode']}) — {report['data_dir']}")
    print("  " + "-" * 58)
    for r in report["rows"]:
        c = r["collection"]
        if report["mode"] == "verify":
            mark = "✓" if r["match"] else "✗"
            print(f"    {mark} {c:44} json={r['json']:<6} pg={r['postgres']}")
        else:
            n = r.get("json", r.get("migrated", 0))
            print(f"    • {c:44} {n}")
    print("  " + "-" * 58)
    print(f"  {report['collections']} collections · {report['total_documents']} documents")
    if report["mode"] == "verify":
        print("  " + ("✅ all counts match" if report["all_match"] else "❌ MISMATCH — do not flip STORAGE_BACKEND yet"))
        return 0 if report["all_match"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
