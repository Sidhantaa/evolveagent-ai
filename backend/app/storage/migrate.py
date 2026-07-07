"""JSON -> Postgres migration (v100).

Copies every JSON collection under ``data_dir`` into the Postgres ``documents``
table. **Idempotent**: each collection is replaced wholesale (``write_list``), so
re-running produces the same result. Supports a dry-run (report only) and a
verify pass (compare per-collection counts JSON vs Postgres).

The JSON files remain the source of truth until you've verified and flipped
``STORAGE_BACKEND=postgres`` — this tool never deletes JSON.
"""

from __future__ import annotations

import os
from typing import Any

from app.storage.json_backend import JsonBackend


def collections(data_dir: str) -> list[str]:
    if not os.path.isdir(data_dir):
        return []
    return sorted(f for f in os.listdir(data_dir) if f.endswith(".json"))


def migrate_json_to_postgres(
    data_dir: str,
    database_url: str | None = None,
    *,
    dry_run: bool = False,
    verify: bool = False,
) -> dict[str, Any]:
    """Return a report: per-collection results + totals.

    - ``dry_run``: read JSON only, report counts, write nothing.
    - ``verify``: compare JSON vs Postgres counts (no writes).
    - otherwise: replace each Postgres collection with the JSON contents.
    """
    js = JsonBackend(data_dir)
    pg = None
    if not dry_run:
        if not database_url:
            raise ValueError("database_url is required unless dry_run=True")
        from app.storage.postgres_backend import PostgresBackend
        pg = PostgresBackend(database_url)

    rows: list[dict[str, Any]] = []
    ok = True
    for c in collections(data_dir):
        items = js.read_list(c)
        n = len(items)
        if dry_run:
            rows.append({"collection": c, "json": n})
        elif verify:
            pg_n = len(pg.read_list(c))  # type: ignore[union-attr]
            match = pg_n == n
            ok = ok and match
            rows.append({"collection": c, "json": n, "postgres": pg_n, "match": match})
        else:
            pg.write_list(c, items)  # type: ignore[union-attr]  # idempotent replace
            rows.append({"collection": c, "migrated": n})

    mode = "dry_run" if dry_run else "verify" if verify else "migrate"
    return {
        "mode": mode,
        "data_dir": data_dir,
        "collections": len(rows),
        "total_documents": sum(r.get("json", r.get("migrated", 0)) for r in rows),
        "all_match": ok if verify else None,
        "rows": rows,
    }
