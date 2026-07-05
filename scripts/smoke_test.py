#!/usr/bin/env python3
"""End-to-end smoke test for the EvolveAgent backend.

Hits the happy-path endpoint behind every major panel against a **live** backend
and prints a pass/fail table. This is the check that would have caught the
"stale backend" bug instantly (a running server on old code returns 404s for new
endpoints even though the code is correct).

Usage:
    python scripts/smoke_test.py                       # defaults to 127.0.0.1:8000
    python scripts/smoke_test.py http://127.0.0.1:8010 # check another instance
    SMOKE_BASE=http://127.0.0.1:8000 python scripts/smoke_test.py

Exit code is 0 if everything passes, 1 if anything fails — so it works in CI or
a pre-deploy gate. Stdlib only; no dependencies.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_BASE = os.environ.get("SMOKE_BASE", "http://127.0.0.1:8000")

# (area, method, path, json_body_or_None, expected_status)
CHECKS: list[tuple[str, str, str, dict | None, int]] = [
    ("core", "GET", "/health", None, 200),
    ("core", "GET", "/api/analytics", None, 200),
    ("core", "GET", "/api/governance", None, 200),
    ("core", "GET", "/api/chats", None, 200),
    ("core", "GET", "/api/notifications", None, 200),
    ("core", "GET", "/api/search?q=smoke", None, 200),
    # Phase 1 — Git Intelligence
    ("git-intel", "GET", "/api/git-intel/status", None, 200),
    ("git-intel", "GET", "/api/git-intel/repositories", None, 200),
    # Phase 2 — Agent Studio
    ("agent-studio", "GET", "/api/agent-studio/templates", None, 200),
    ("agent-studio", "GET", "/api/agent-studio/agents", None, 200),
    ("agent-studio", "GET", "/api/agent-studio/summary", None, 200),
    ("agent-studio", "POST", "/api/agent-studio/agents", {"name": "smoke-agent", "role": "smoke"}, 200),
    # Phase 4 — Voice Console
    ("voice-console", "GET", "/api/voice-console/status", None, 200),
    ("voice-console", "GET", "/api/voice-console/settings", None, 200),
    ("voice-console", "GET", "/api/voice-console/summary", None, 200),
    ("voice-console", "POST", "/api/voice-console/activity", {"kind": "speak", "workspace_id": "smoke"}, 200),
    # Phase 6 — Durable Workflows
    ("durable-workflows", "GET", "/api/durable-workflows/templates", None, 200),
    ("durable-workflows", "GET", "/api/durable-workflows/definitions", None, 200),
    ("durable-workflows", "GET", "/api/durable-workflows/runs", None, 200),
    ("durable-workflows", "GET", "/api/durable-workflows/summary", None, 200),
    ("durable-workflows", "POST", "/api/durable-workflows/runs", {"steps": [{"name": "smoke step"}]}, 200),
    # Phase 7 — Marketplace Hub
    ("marketplace-hub", "GET", "/api/marketplace-hub/listings", None, 200),
    ("marketplace-hub", "GET", "/api/marketplace-hub/summary", None, 200),
    ("marketplace-hub", "GET", "/api/marketplace-hub/installs", None, 200),
    # Master Agent
    ("master-agent", "GET", "/api/master-agent/summary", None, 200),
    ("master-agent", "GET", "/api/master-agent/capabilities", None, 200),
]


def request(base: str, method: str, path: str, body: dict | None) -> tuple[int, str]:
    url = f"{base}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, resp.read(200).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(200).decode("utf-8", "replace")
    except urllib.error.URLError as exc:
        return 0, f"CONNECTION FAILED: {exc.reason}"
    except Exception as exc:  # noqa: BLE001
        return 0, f"ERROR: {exc}"


def flow_marketplace_install(base: str) -> tuple[bool, str]:
    """GET a listing then install it — exercises the cross-service install path."""
    try:
        with urllib.request.urlopen(f"{base}/api/marketplace-hub/listings", timeout=15) as r:
            if r.status != 200:
                return False, f"list listings -> {r.status}"
            listings = json.loads(r.read().decode()).get("listings", [])
    except Exception as exc:  # noqa: BLE001
        return False, f"list listings failed: {exc}"
    if not listings:
        return False, "no listings to install"
    lid = listings[0]["listing_id"]
    status, _ = request(base, "POST", f"/api/marketplace-hub/listings/{lid}/install", {})
    return status == 200, f"install {lid[:8]} -> {status}"


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE
    print(f"\n  EvolveAgent smoke test → {base}\n" + "  " + "-" * 58)
    passed = failed = 0
    last_area = None
    for area, method, path, body, expect in CHECKS:
        if area != last_area:
            print(f"\n  [{area}]")
            last_area = area
        status, snippet = request(base, method, path, body)
        ok = status == expect
        mark = "✓" if ok else "✗"
        line = f"    {mark} {method:4} {path:44} {status}"
        if not ok:
            line += f"  (want {expect})  {snippet[:60]}"
        print(line)
        passed += ok
        failed += not ok

    # cross-service flow
    print("\n  [flows]")
    ok, detail = flow_marketplace_install(base)
    print(f"    {'✓' if ok else '✗'} marketplace publish→install   {detail}")
    passed += ok
    failed += not ok

    total = passed + failed
    print("\n  " + "-" * 58)
    print(f"  {passed}/{total} passed" + (f" · {failed} FAILED" if failed else " · all green ✅"))
    if failed:
        print("  ⚠ If everything 404s, the backend is likely running STALE code — restart it.")
    print()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
