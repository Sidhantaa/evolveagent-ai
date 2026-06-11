#!/usr/bin/env python3
"""Archive legacy Linear issues to free workspace quota for official roadmap."""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

import httpx

LINEAR_API_URL = "https://api.linear.app/graphql"
TEAM = "EvolveAgent AI"
PROJECT = "EvolveAgent AI Platform"

# Official parent titles to keep (exact match).
KEEP_PARENT_TITLES = {
    "v2.6 — Workspace Memory + Personal AI Context",
    "v3.0 — Full Agent OS Foundation",
    "v3.5 — UI/UX Professional Polish",
    "v4.0 — Real Codebase Automation Assistant",
    "v4.5 — Test + Quality Engineering Agent",
    "v5.0 — Real App Builder Mode",
    "v5.5 — Multi-Agent Debate + Simulation Mode",
    "v6.0 — Real Memory Intelligence",
    "v6.5 — Personal AI Profile Layer",
    "v7.0 — Enterprise Workflow Builder",
    "v7.5 — Voice Agent 2.0",
    "v8.0 — Recording-to-Workflow Engine",
    "v8.5 — Document Automation Studio",
    "v9.0 — Local/Private AI Mode",
    "v9.5 — Cost + Performance Optimizer",
    "v10.0 — Agent Marketplace / Skill Store 2.0",
    "v10.5 — Collaboration Mode",
    "v11.0 — Real External Integrations",
    "v11.5 — Autonomous Research Agent",
    "v12.0 — Agent Autopilot With Permission Levels",
    "v12.5 — Digital Twin Work Style Engine",
    "v13.0 — Enterprise Governance + Compliance",
    "v13.5 — AI Evaluation Lab",
    "v14.0 — Full AI Project Manager",
    "v14.5 — Portfolio Mode",
    "v15.0 — EvolveAgent OS",
}

OFFICIAL_VERSION_RE = re.compile(
    r"^v(2\.6|3\.0|3\.5|4\.0|4\.5|5\.0|5\.5|6\.0|6\.5|7\.0|7\.5|8\.0|8\.5|9\.0|9\.5|10\.0|10\.5|11\.0|11\.5|12\.0|12\.5|13\.0|13\.5|14\.0|14\.5|15\.0) — "
)


def load_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / "backend" / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def graphql(api_key: str, query: str, variables: dict | None = None) -> dict:
    response = httpx.post(
        LINEAR_API_URL,
        headers={"Authorization": api_key, "Content-Type": "application/json"},
        json={"query": query, "variables": variables or {}},
        timeout=30.0,
    )
    response.raise_for_status()
    body = response.json()
    if body.get("errors"):
        raise RuntimeError(body["errors"][0].get("message", "GraphQL error"))
    return body.get("data") or {}


def fetch_all_issues(api_key: str, team_id: str) -> list[dict]:
    issues: list[dict] = []
    cursor: str | None = None
    while True:
        data = graphql(
            api_key,
            """
            query($teamId: String!, $first: Int!, $after: String) {
              team(id: $teamId) {
                issues(first: $first, after: $after, filter: { project: { name: { eq: "EvolveAgent AI Platform" } } }) {
                  pageInfo { hasNextPage endCursor }
                  nodes { id identifier title archivedAt parent { identifier title } }
                }
              }
            }
            """,
            {"teamId": team_id, "first": 100, "after": cursor},
        )
        batch = (data.get("team") or {}).get("issues") or {}
        issues.extend(batch.get("nodes") or [])
        page = batch.get("pageInfo") or {}
        if not page.get("hasNextPage"):
            break
        cursor = page.get("endCursor")
    return issues


def should_keep(issue: dict) -> bool:
    title = issue.get("title") or ""
    if issue.get("archivedAt"):
        return True
    if title in KEEP_PARENT_TITLES:
        return True
    if OFFICIAL_VERSION_RE.match(title):
        return True
    parent = issue.get("parent") or {}
    parent_title = parent.get("title") or ""
    if parent_title in KEEP_PARENT_TITLES:
        return True
    if OFFICIAL_VERSION_RE.match(parent_title):
        return True
    return False


def archive_issue(api_key: str, issue_id: str) -> None:
    graphql(
        api_key,
        "mutation($id: String!) { issueArchive(id: $id) { success } }",
        {"id": issue_id},
    )


def main() -> None:
    load_env()
    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        raise SystemExit("LINEAR_API_KEY not set")

    team_id = next(
        t["id"]
        for t in graphql(api_key, "{ teams { nodes { id name } } }")["teams"]["nodes"]
        if t["name"] == TEAM
    )

    issues = fetch_all_issues(api_key, team_id)
    to_archive = [i for i in issues if not should_keep(i)]
    print(f"Total active issues: {len([i for i in issues if not i.get('archivedAt')])}")
    print(f"Archive candidates: {len(to_archive)}")

    archived = 0
    for issue in to_archive:
        if issue.get("archivedAt"):
            continue
        archive_issue(api_key, issue["id"])
        archived += 1
        print(f"Archived {issue['identifier']} {issue['title'][:70]}")
        time.sleep(0.4)

    print(f"\nArchived {archived} legacy issues")


if __name__ == "__main__":
    main()
