#!/usr/bin/env python3
"""Create official EvolveAgent roadmap v2.6–v15.0 in Linear with subtasks."""
from __future__ import annotations

import os
import time
from pathlib import Path

import httpx

LINEAR_API_URL = "https://api.linear.app/graphql"
TEAM = "EvolveAgent AI"
PROJECT = "EvolveAgent AI Platform"

# (version label, title suffix, state, subtasks[(title, desc)])
ROADMAP: list[tuple[str, str, str, list[tuple[str, str]]]] = [
    (
        "v2.6",
        "Workspace Memory + Personal AI Context",
        "Done",
        [
            ("Workspace switcher UI", "Create, switch, archive workspaces"),
            ("Workspace-scoped data", "Chats, files, goals, agents per workspace"),
            ("Workspace memory timeline", "Add, search, filter, edit, delete memory"),
            ("Memory retrieval before runs", "Inject capped relevant context into agents"),
            ("Custom Agent Builder", "Reusable specialist agents + templates"),
            ("Default workspace fallback", "Legacy requests use default workspace"),
        ],
    ),
    (
        "v2.7",
        "Knowledge Base + Searchable Project Brain",
        "Backlog",
        [
            ("Full-text workspace search", "Search chats, memory, files, goals in one query"),
            ("Knowledge base panel UI", "Browse and organize project knowledge"),
            ("Cross-session knowledge links", "Connect related facts and decisions"),
            ("Memory importance ranking", "Surface high-value context first"),
            ("Project brain export", "Export workspace knowledge as markdown/json"),
        ],
    ),
    (
        "v2.8",
        "Real Tool Router + Plugin System",
        "Backlog",
        [
            ("Tool registry service", "Register tools with schemas and permissions"),
            ("Plugin API contract", "Load external tools safely at runtime"),
            ("Tool Router agent integration", "Master Agent selects tools dynamically"),
            ("Plugin permission levels", "Governance per plugin action"),
            ("Developer Mode tool trace", "Show which tools ran and results"),
        ],
    ),
    (
        "v2.9",
        "Human Approval Workflow 2.0",
        "Backlog",
        [
            ("Multi-step approval chains", "Require approval before risky actions"),
            ("Approval queue UI", "Pending approvals dashboard in Mission Control"),
            ("Approval audit trail", "Who approved what and when"),
            ("Reject and rollback flow", "Undo planned changes on rejection"),
            ("Notification hooks", "Optional alerts for pending approvals"),
        ],
    ),
    (
        "v3.0",
        "Full Agent OS Foundation",
        "Backlog",
        [
            ("Agent scheduler", "Queue and run agent jobs asynchronously"),
            ("Agent lifecycle manager", "Start, pause, resume, cancel runs"),
            ("System prompt registry", "Central store for agent prompts"),
            ("OS kernel service", "Core orchestration layer abstraction"),
            ("Agent health monitoring", "Detect stuck/failed agent runs"),
        ],
    ),
    (
        "v3.5",
        "UI/UX Professional Polish",
        "Backlog",
        [
            ("Design system tokens", "Consistent colors, spacing, typography"),
            ("Responsive mobile layout", "Usable on tablet and phone"),
            ("Accessibility pass", "Keyboard nav, ARIA, contrast fixes"),
            ("Dark/light theme toggle", "User-selectable theme"),
            ("Onboarding walkthrough", "First-run guide for new users"),
        ],
    ),
    (
        "v4.0",
        "Real Codebase Automation Assistant",
        "In Progress",
        [
            ("Linear integration bridge", "Sync issues, branches, governed commits"),
            ("Git automation service", "Safe branch, commit, optional push"),
            ("Safe file editor apply", "Approval-gated file patches"),
            ("Repo-aware project scanner", "Understand structure before edits"),
            ("Allowlisted test/build runner", "pytest and npm run build only"),
        ],
    ),
    (
        "v4.5",
        "Test + Quality Engineering Agent",
        "Backlog",
        [
            ("Test generation agent", "Suggest tests for changed code"),
            ("Coverage report integration", "Parse and display coverage"),
            ("Flaky test detection", "Flag unstable tests in CI history"),
            ("Quality gate before merge", "Block if tests fail"),
            ("Regression summary comments", "Post test results to Linear/GitHub"),
        ],
    ),
    (
        "v5.0",
        "Real App Builder Mode",
        "Backlog",
        [
            ("App scaffold from prompt", "Generate frontend + backend skeleton"),
            ("Stack template library", "FastAPI+React, Next.js, etc."),
            ("Guided build wizard", "Step-by-step app creation flow"),
            ("Preview deploy stub", "Local preview of generated app"),
            ("App builder governance", "No unsafe scaffolds or secrets"),
        ],
    ),
    (
        "v5.5",
        "Multi-Agent Debate + Simulation Mode",
        "Backlog",
        [
            ("Agent debate UI", "Show agents arguing different approaches"),
            ("Simulation sandbox", "Run what-if without side effects"),
            ("Consensus after debate", "Judge picks winner from debate"),
            ("Simulation audit log", "Record simulated decisions"),
            ("Developer Mode debate trace", "Full debate transcript"),
        ],
    ),
    (
        "v6.0",
        "Real Memory Intelligence",
        "Backlog",
        [
            ("Vector memory store", "Embeddings for workspace memory"),
            ("Semantic memory retrieval", "Find relevant memory by meaning"),
            ("Memory consolidation job", "Merge duplicate/overlapping memories"),
            ("Long-term memory tiers", "Hot vs archived memory"),
            ("Memory quality scoring", "Decay low-value stale memories"),
        ],
    ),
    (
        "v6.5",
        "Personal AI Profile Layer",
        "Backlog",
        [
            ("User profile model", "Communication style, tone, format prefs"),
            ("Profile-aware prompting", "Inject profile into agent system prompts"),
            ("Learn from feedback", "Update profile from helpful/not helpful"),
            ("Profile export/import", "Portable user preferences"),
            ("Multi-profile support", "Work vs personal AI profiles"),
        ],
    ),
    (
        "v7.0",
        "Enterprise Workflow Builder",
        "Backlog",
        [
            ("Visual workflow editor", "Drag-and-drop agent DAG builder"),
            ("Workflow template library", "Reusable enterprise workflows"),
            ("Workflow version control", "Track changes to workflows"),
            ("Workflow execution engine", "Run multi-step DAGs with governance"),
            ("Workflow analytics", "Success rate and latency per workflow"),
        ],
    ),
    (
        "v7.5",
        "Voice Agent 2.0",
        "Backlog",
        [
            ("Full voice conversation mode", "Speak and hear responses"),
            ("Text-to-speech output", "Read agent answers aloud"),
            ("Voice command shortcuts", "Beyond single-shot transcription"),
            ("Voice session history", "Store voice transcripts in chats"),
            ("Push-to-talk and continuous modes", "Flexible voice UX"),
        ],
    ),
    (
        "v8.0",
        "Recording-to-Workflow Engine",
        "Backlog",
        [
            ("Meeting → goal auto-create", "Recording spawns Mission Control goal"),
            ("Action item → subtask sync", "Extract tasks from recordings"),
            ("Recording triggers workflow", "Start agent run from recording"),
            ("Calendar/meeting metadata", "Title, attendees, duration"),
            ("Recording workflow templates", "Standup, lecture, interview modes"),
        ],
    ),
    (
        "v8.5",
        "Document Automation Studio",
        "Backlog",
        [
            ("Batch document processing", "Run same prompt on many files"),
            ("Document templates", "Resume, report, bid templates"),
            ("Mail-merge style generation", "Fill templates from CSV/data"),
            ("Document workflow approval", "Review before export/send"),
            ("Export to PDF/DOCX", "Generate formatted outputs"),
        ],
    ),
    (
        "v9.0",
        "Local/Private AI Mode",
        "Backlog",
        [
            ("Ollama/local model support", "Run models without cloud API"),
            ("Offline mode toggle", "Work without network for local models"),
            ("Data residency controls", "Keep prompts/files local"),
            ("Local model router", "Fallback chain for local providers"),
            ("Private mode indicator UI", "Show when data stays on device"),
        ],
    ),
    (
        "v9.5",
        "Cost + Performance Optimizer",
        "Backlog",
        [
            ("Token usage tracking", "Per-run input/output token counts"),
            ("Cost estimates per model", "Show $ estimate per run"),
            ("Budget limits per workspace", "Cap spend automatically"),
            ("Latency-aware routing", "Pick faster model when acceptable"),
            ("Optimizer recommendations", "Suggest cheaper equivalent models"),
        ],
    ),
    (
        "v10.0",
        "Agent Marketplace / Skill Store 2.0",
        "Backlog",
        [
            ("Publish custom agents", "Share agents to marketplace"),
            ("Install community agents", "One-click agent install"),
            ("Agent ratings and reviews", "Community quality signals"),
            ("Verified agent badges", "Governance-reviewed agents"),
            ("Agent versioning in store", "Update installed agents safely"),
        ],
    ),
    (
        "v10.5",
        "Collaboration Mode",
        "Backlog",
        [
            ("Shared workspaces", "Multiple users per project"),
            ("Run comments and mentions", "Discuss agent outputs inline"),
            ("Presence indicators", "See who is active in workspace"),
            ("Shared Mission Control", "Team goal visibility"),
            ("Role-based workspace access", "Viewer vs editor roles"),
        ],
    ),
    (
        "v11.0",
        "Real External Integrations",
        "Backlog",
        [
            ("Linear bi-directional sync", "Issues, status, comments (extend v4.0)"),
            ("GitHub PR integration", "Link runs to PRs and checks"),
            ("Slack notifications", "Post run results to channels"),
            ("Notion export sync", "Push summaries to Notion pages"),
            ("Integration settings UI", "Connect/disconnect services safely"),
        ],
    ),
    (
        "v11.5",
        "Autonomous Research Agent",
        "Backlog",
        [
            ("Governed web research", "Fetch sources with approval"),
            ("Citation tracking", "Link claims to sources"),
            ("Research report generator", "Structured multi-section reports"),
            ("Source credibility scoring", "Judge agent rates sources"),
            ("Research session memory", "Persist research across runs"),
        ],
    ),
    (
        "v12.0",
        "Agent Autopilot With Permission Levels",
        "Backlog",
        [
            ("Supervised autopilot mode", "Run subtasks with tiered permissions"),
            ("Permission tier config", "Read-only vs edit vs deploy levels"),
            ("Autopilot kill switch", "Instant stop all autonomous actions"),
            ("Autopilot action log", "Every autonomous step recorded"),
            ("Human checkpoint gates", "Require confirm at critical steps"),
        ],
    ),
    (
        "v12.5",
        "Digital Twin Work Style Engine",
        "Backlog",
        [
            ("Work style inference", "Learn how user writes and decides"),
            ("Twin response mode", "Answers in user's voice/style"),
            ("Decision pattern memory", "Recall past choices on similar tasks"),
            ("Twin calibration UI", "User adjusts twin behavior"),
            ("Privacy controls for twin data", "Export/delete twin profile"),
        ],
    ),
    (
        "v13.0",
        "Enterprise Governance + Compliance",
        "Backlog",
        [
            ("Extended audit logs", "Immutable governance event store"),
            ("Data retention policies", "Auto-delete old runs per policy"),
            ("Compliance report export", "SOC2-style activity reports"),
            ("PII detection and redaction", "Scan inputs/outputs for PII"),
            ("Enterprise admin console", "Org-wide policy management"),
        ],
    ),
    (
        "v13.5",
        "AI Evaluation Lab",
        "Backlog",
        [
            ("Benchmark test suites", "Standard eval sets per task type"),
            ("A/B agent comparison", "Compare two prompt/agent configs"),
            ("Eval dashboard", "Charts for score trends over time"),
            ("Regression detection", "Alert when scores drop"),
            ("Export eval results", "CSV/JSON for portfolio demos"),
        ],
    ),
    (
        "v14.0",
        "Full AI Project Manager",
        "Backlog",
        [
            ("Timeline and milestones", "Gantt-style goal timeline"),
            ("Resource allocation view", "Agent/time budget per goal"),
            ("Risk register", "Track blockers and mitigations"),
            ("Stakeholder status reports", "Auto weekly project summaries"),
            ("Linear/Mission Control unified view", "Single project manager dashboard"),
        ],
    ),
    (
        "v14.5",
        "Portfolio Mode",
        "Backlog",
        [
            ("Multi-project dashboard", "All workspaces at a glance"),
            ("Cross-project analytics", "Compare progress across projects"),
            ("Portfolio health score", "Aggregate risk and completion"),
            ("Executive summary view", "High-level KPIs for demos"),
            ("Portfolio export", "Resume/interview portfolio bundle"),
        ],
    ),
    (
        "v15.0",
        "EvolveAgent OS",
        "Backlog",
        [
            ("Unified platform installer", "Single command local/cloud setup"),
            ("Plugin ecosystem SDK", "Third-party extension framework"),
            ("Production SLA monitoring", "Uptime and error budgets"),
            ("OS-level agent scheduler", "Background jobs across all modules"),
            ("EvolveAgent OS branding launch", "v15 GA release checklist"),
        ],
    ),
]


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


def graphql(api_key: str, query: str, variables: dict | None = None, retries: int = 8) -> dict:
    last_error: Exception | None = None
    for attempt in range(retries):
        response = httpx.post(
            LINEAR_API_URL,
            headers={"Authorization": api_key, "Content-Type": "application/json"},
            json={"query": query, "variables": variables or {}},
            timeout=30.0,
        )
        response.raise_for_status()
        body = response.json()
        if body.get("errors"):
            message = body["errors"][0].get("message", "GraphQL error")
            if "usage limit exceeded" in message.lower() and attempt < retries - 1:
                wait = min(60, 2 ** attempt * 5)
                print(f"  rate limited, waiting {wait}s...")
                time.sleep(wait)
                last_error = RuntimeError(message)
                continue
            raise RuntimeError(message)
        return body.get("data") or {}
    raise last_error or RuntimeError("GraphQL request failed")


def get_team_id(api_key: str) -> str:
    data = graphql(api_key, "{ teams { nodes { id name } } }")
    for team in data.get("teams", {}).get("nodes", []):
        if team.get("name") == TEAM:
            return team["id"]
    raise RuntimeError(f"Team not found: {TEAM}")


def get_project_id(api_key: str, team_id: str) -> str:
    data = graphql(
        api_key,
        "query($teamId: String!) { team(id: $teamId) { projects { nodes { id name } } } }",
        {"teamId": team_id},
    )
    for project in (data.get("team") or {}).get("projects", {}).get("nodes", []):
        if project.get("name") == PROJECT:
            return project["id"]
    raise RuntimeError(f"Project not found: {PROJECT}")


def existing_roadmap_parents(api_key: str, team_id: str) -> dict[str, str]:
    """Map version label -> issue identifier when exact official parent title exists."""
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
    official_titles = {f"{version} — {suffix}": version for version, suffix, _, _ in ROADMAP}
    found: dict[str, str] = {}
    for issue in (data.get("team") or {}).get("issues", {}).get("nodes", []):
        title = issue.get("title") or ""
        version = official_titles.get(title)
        if version:
            found[version] = issue["identifier"]
    return found


def update_state(api_key: str, issue_id: str, state_name: str) -> None:
    issue_data = graphql(
        api_key,
        "query($id: String!) { issue(id: $id) { id team { states { nodes { id name } } } } }",
        {"id": issue_id},
    )
    issue = issue_data.get("issue") or {}
    states = (issue.get("team") or {}).get("states", {}).get("nodes", [])
    target = next((s for s in states if s.get("name", "").lower() == state_name.lower()), None)
    if not target:
        return
    graphql(
        api_key,
        "mutation($id: String!, $stateId: String!) { issueUpdate(id: $id, input: { stateId: $stateId }) { success } }",
        {"id": issue["id"], "stateId": target["id"]},
    )


def create_parent(
    api_key: str,
    team_id: str,
    project_id: str,
    version: str,
    suffix: str,
    state: str,
) -> str:
    title = f"{version} — {suffix}"
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


def get_parent_uuid(api_key: str, identifier: str) -> str:
    data = graphql(api_key, "query($id: String!) { issue(id: $id) { id } }", {"id": identifier})
    issue = data.get("issue")
    if not issue:
        raise RuntimeError(f"Not found: {identifier}")
    return issue["id"]


def child_titles(api_key: str, parent: str) -> set[str]:
    data = graphql(
        api_key,
        "query($id: String!) { issue(id: $id) { children { nodes { title } } } }",
        {"id": parent},
    )
    nodes = ((data.get("issue") or {}).get("children") or {}).get("nodes", [])
    return {n.get("title", "").lower() for n in nodes}


def create_child(
    api_key: str,
    team_id: str,
    project_id: str,
    parent_uuid: str,
    title: str,
    description: str,
    state: str,
) -> str:
    data = graphql(
        api_key,
        """
        mutation IssueCreate($input: IssueCreateInput!) {
          issueCreate(input: $input) { success issue { identifier id } }
        }
        """,
        {
            "input": {
                "teamId": team_id,
                "projectId": project_id,
                "parentId": parent_uuid,
                "title": title,
                "description": description,
            }
        },
    )
    result = data.get("issueCreate") or {}
    if not result.get("success"):
        raise RuntimeError(f"Failed child: {title}")
    ident = result["issue"]["identifier"]
    if state.lower() not in {"backlog", ""}:
        update_state(api_key, result["issue"]["id"], state)
    return ident


def main() -> None:
    load_env()
    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        raise SystemExit("LINEAR_API_KEY not set")

    team_id = get_team_id(api_key)
    project_id = get_project_id(api_key, team_id)
    existing = existing_roadmap_parents(api_key, team_id)

    parents_created = 0
    children_created = 0

    for version, suffix, state, subtasks in ROADMAP:
        title_key = version
        if title_key in existing:
            parent_ident = existing[title_key]
            print(f"Exists {parent_ident} {version} — {suffix}")
        else:
            parent_ident = create_parent(api_key, team_id, project_id, version, suffix, state)
            existing[title_key] = parent_ident
            parents_created += 1
            print(f"Created {parent_ident} {version} — {suffix} [{state}]")
            time.sleep(0.3)

        parent_uuid = get_parent_uuid(api_key, parent_ident)
        existing_children = child_titles(api_key, parent_ident)
        child_state = state if state == "Done" else "Backlog"
        if state == "In Progress":
            child_state = "Backlog"

        for stitle, sdesc in subtasks:
            if stitle.lower() in existing_children:
                continue
            ident = create_child(
                api_key, team_id, project_id, parent_uuid, stitle, sdesc, child_state
            )
            children_created += 1
            print(f"  + {ident} {stitle}")
            time.sleep(0.5)

    print(f"\nParents created: {parents_created}")
    print(f"Sub-issues created: {children_created}")
    print(f"Roadmap versions: {len(ROADMAP)} (v2.6 → v15.0)")


if __name__ == "__main__":
    main()
