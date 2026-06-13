#!/usr/bin/env python3
"""Rename legacy version conflicts and finish official v2.6–v15.0 roadmap in Linear."""
from __future__ import annotations

import os
import time
from pathlib import Path

import httpx

from create_official_roadmap_linear import (
    ROADMAP,
    PROJECT,
    TEAM,
    create_child,
    get_parent_uuid,
    get_project_id,
    get_team_id,
    graphql,
    load_env,
    update_state,
)

LINEAR_API_URL = "https://api.linear.app/graphql"

# Legacy issues that reused v2.6–v2.9 version numbers with different meaning.
RENAME: list[tuple[str, str]] = [
    ("EVO-8", "[Legacy shipped] v2.7 — CI, Verification & Demo Assets"),
    ("EVO-1", "[Legacy shipped] v2.8 — Linear Integration + Task Execution Bridge"),
    ("EVO-12", "[Legacy in review] v2.8 — Linear Auto-Completion Sync"),
    ("EVO-13", "[Legacy backlog] v2.9 — SSE Streaming Responses"),
]

# Align shipped v2.6 parent to official title.
UPDATE_TITLE: list[tuple[str, str]] = [
    ("EVO-9", "v2.6 — Workspace Memory + Personal AI Context"),
]


def official_title(version: str, suffix: str) -> str:
    return f"{version} — {suffix}"


def existing_by_exact_title(api_key: str, team_id: str) -> dict[str, str]:
    """Map exact official parent title -> identifier."""
    data = graphql(
        api_key,
        """
        query($teamId: String!, $first: Int!) {
          team(id: $teamId) {
            issues(first: $first, filter: { project: { name: { eq: "EvolveAgent AI Platform" } } }) {
              nodes { id identifier title }
            }
          }
        }
        """,
        {"teamId": team_id, "first": 250},
    )
    titles = {official_title(v, s): v for v, s, _, _ in ROADMAP}
    found: dict[str, str] = {}
    for issue in (data.get("team") or {}).get("issues", {}).get("nodes", []):
        title = issue.get("title") or ""
        if title in titles:
            found[titles[title]] = issue["identifier"]
    return found


def rename_issue(api_key: str, identifier: str, new_title: str) -> None:
    data = graphql(
        api_key,
        "query($id: String!) { issue(id: $id) { id title } }",
        {"id": identifier},
    )
    issue = data.get("issue")
    if not issue:
        print(f"Skip missing {identifier}")
        return
    if issue.get("title") == new_title:
        print(f"Already {identifier}: {new_title}")
        return
    graphql(
        api_key,
        "mutation($id: String!, $title: String!) { issueUpdate(id: $id, input: { title: $title }) { success } }",
        {"id": issue["id"], "title": new_title},
    )
    print(f"Renamed {identifier} -> {new_title}")
    time.sleep(1.0)


def create_parent(
    api_key: str,
    team_id: str,
    project_id: str,
    version: str,
    suffix: str,
    state: str,
) -> str:
    title = official_title(version, suffix)
    data = graphql(
        api_key,
        """
        mutation IssueCreate($input: IssueCreateInput!) {
          issueCreate(input: $input) { success issue { id identifier title } }
        }
        """,
        {
            "input": {
                "teamId": team_id,
                "projectId": project_id,
                "title": title,
                "description": f"**EvolveAgent AI Roadmap — {title}**\n\nOfficial milestone epic. See sub-issues for implementation tasks.",
                "priority": 2 if version.startswith(("v2.", "v3.", "v4.")) else 3,
            }
        },
    )
    result = data.get("issueCreate") or {}
    if not result.get("success"):
        raise RuntimeError(f"Failed parent: {title}")
    ident = result["issue"]["identifier"]
    issue_id = result["issue"]["id"]
    if state.lower() != "backlog":
        update_state(api_key, issue_id, state)
    return ident


def child_titles(api_key: str, parent: str) -> set[str]:
    data = graphql(
        api_key,
        "query($id: String!) { issue(id: $id) { children { nodes { title } } } }",
        {"id": parent},
    )
    nodes = ((data.get("issue") or {}).get("children") or {}).get("nodes", [])
    return {n.get("title", "").lower() for n in nodes}


def main() -> None:
    load_env()
    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        raise SystemExit("LINEAR_API_KEY not set")

    team_id = get_team_id(api_key)
    project_id = get_project_id(api_key, team_id)

    print("=== Step 1: Rename legacy version conflicts ===")
    for ident, title in RENAME:
        rename_issue(api_key, ident, title)

    print("\n=== Step 2: Align v2.6 official title ===")
    for ident, title in UPDATE_TITLE:
        rename_issue(api_key, ident, title)

    print("\n=== Step 3: Create missing official parents + subtasks ===")
    existing = existing_by_exact_title(api_key, team_id)
    parents_created = 0
    children_created = 0

    for version, suffix, state, subtasks in ROADMAP:
        exact = official_title(version, suffix)
        if version in existing:
            parent_ident = existing[version]
            print(f"Exists {parent_ident} {exact}")
        else:
            parent_ident = create_parent(api_key, team_id, project_id, version, suffix, state)
            existing[version] = parent_ident
            parents_created += 1
            print(f"Created {parent_ident} {exact} [{state}]")
            time.sleep(1.0)

        parent_uuid = get_parent_uuid(api_key, parent_ident)
        existing_children = child_titles(api_key, parent_ident)
        child_state = "Backlog" if state != "Done" else "Done"

        for stitle, sdesc in subtasks:
            if stitle.lower() in existing_children:
                continue
            ident = create_child(
                api_key, team_id, project_id, parent_uuid, stitle, sdesc, child_state
            )
            children_created += 1
            print(f"  + {ident} {stitle}")
            time.sleep(1.0)

    print(f"\nParents created: {parents_created}")
    print(f"Sub-issues created: {children_created}")
    print(f"Official roadmap versions: {len(ROADMAP)} (v2.6 → v15.0)")


if __name__ == "__main__":
    main()
