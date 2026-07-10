# Route/Page Coverage Audit

Last checked: 2026-07-10

## Snapshot

EvolveAgent AI now has a very large backend surface and a much cleaner premium frontend shell.
The main gap is no longer "missing backend capability"; it is "make each capability easy to see,
test, and operate from the UI."

Current counts:

- Backend API route modules: 86
- Backend route decorators: 771
- Frontend pages: 12
- Frontend live API helper functions: 27

## Current Frontend Pages

- Home Dashboard
- Simple Mode Chat
- Developer Mode Console
- Code Changes
- Mission Control
- Agents
- Approvals
- Project Brain
- Tools / MCP Hub
- Governance
- Settings
- Design System

## Strongly Covered Areas

These areas have visible frontend pages and real API wiring:

- Chat routing through the Master Agent
- MCP connector planning, approval, and governed execution
- Agent Studio agent list
- Governance recent events
- System metrics and storage status
- Memory v2 add/search
- Approval decisions
- Durable workflows and workflow run details
- v150 code-change workflow status, effects, and approval flow
- Provider readiness
- GitHub read status

## Core Gap

Backend coverage is much broader than UI coverage.

Many versions and services exist as real backend routes but are not first-class pages in the
premium frontend. The UI is polished, but it is not yet a full control surface for the whole OS.

Important distinction:

- Route exists: backend can answer or store the feature.
- API helper exists: frontend code can call some endpoint.
- Page exists: user can discover and operate the feature clearly.
- Demo-ready flow exists: user can run the feature, see state, recover from errors, and understand safety.

Today, many features are at route/helper level, not demo-ready page level.

## Backend Groups With Weak or No Direct Premium Page Coverage

These are the highest-value groups to expose next:

- Research Agent
- Business Intelligence
- Meeting Intelligence
- Multi-Agent Collaboration
- Permission System
- Governance Console
- Local Data Manager
- Import Center
- Export Center
- Plugin Marketplace
- Integration Hub
- QA Center
- Release Manager
- Product Launch Console
- Agent Registry
- Event Subscriptions / Event Bus
- Git automation
- Plugin manifests
- Evolution / learning internals

Some of these may have older helper code or partial cards, but they do not yet feel like complete
premium pages in the current 12-page shell.

## Missing Core Product Pieces

### 1. Capability Directory

User needs one place to see every feature:

- Feature name
- Status: mock, local, real API, needs config, blocked
- Route group
- UI page
- Safety level
- Last verified date

This prevents confusion when a backend feature exists but the user cannot find it.

### 2. Demo Data + Reset

Need a stable demo seed/reset flow:

- Seed sample workspace
- Seed sample agents
- Seed sample workflows
- Seed sample approvals
- Seed sample governance events
- Reset demo state

This makes the app easy to show without relying on random runtime JSON.

### 3. Frontend Coverage Matrix

Add a maintained matrix:

- Backend route group
- API helper
- Page/component
- Manual test steps
- Automated test status

This should live in docs and eventually be checked by CI.

### 4. Unified Feature QA

Each major feature needs a small manual test card:

- What to click
- Expected visible result
- Expected safety behavior
- Expected log/audit event

This matters more now than adding more versions.

### 5. Product Narrative

The project needs one concise "what this is" story shown in-app:

EvolveAgent is a governed AI operating system that turns goals into plans, routes work through
specialist agents and tools, asks for approval before risky actions, verifies results, and saves
memory so future work improves.

## Recommended Next Work

### Sprint 1: Feature Control Center

Create a Developer Mode page that reads the feature registry and shows every capability with:

- status badge
- route group
- UI coverage
- safety mode
- last run
- "open related page" action

### Sprint 2: v77-v90 UI Completion

Build first-class pages or panels for the backend-only feature groups:

- Research Agent
- Business Intelligence
- Meeting Intelligence
- Collaboration
- Permissions
- Governance Console
- Data Manager
- Import Center
- Export Center
- Plugin Marketplace
- Integration Hub
- QA Center
- Release Manager
- Launch Console

### Sprint 3: Demo Seed + Manual Verification

Add one demo command/page:

- seed demo data
- run smoke checks
- show pass/fail
- export demo report

### Sprint 4: Documentation Cleanup

Update:

- README
- Project architecture
- Obsidian index
- manual test checklist
- resume/case study docs

## What Not To Do Yet

- Do not add more version numbers just to expand the roadmap.
- Do not add more backend-only services until the current service surface is visible.
- Do not remove existing backend routes.
- Do not bypass governance to make demos easier.

## Bottom Line

The core backend is ahead of the frontend.
The best next move is not another giant backend feature. It is UI coverage, demo reliability,
and verification clarity so every existing feature can be seen, tested, and trusted.
