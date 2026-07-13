# EvolveAgent AI — Portfolio Pack

A concise, accurate reference for presenting EvolveAgent AI in a portfolio, resume, GitHub profile, interview, or demo.

## One-Line Pitch

EvolveAgent AI is a local-first, governance-first AI operating system that turns goals into planned, approved, verified work across agents, memory, tools, workflows, and audit logs.

## 30-Second Explanation

EvolveAgent is not a new foundation model. It is the operating layer around models like OpenAI, Claude, Gemini, Mistral, and local models. A normal chatbot answers one prompt; EvolveAgent tries to understand the larger goal, load workspace memory, choose agents and tools, ask for approval when actions are risky, verify the result, and remember what happened for the next run.

## 1-Minute Explanation

EvolveAgent AI is a full-stack AI command center built with FastAPI and React. A user request enters through chat, voice, files, workflows, or Developer Mode. EVA / Master Agent classifies the task, retrieves relevant workspace memory, selects specialist agents or tools, runs governance checks, creates approval gates for risky actions, verifies the result where possible, and stores memory, analytics, cost, and audit history.

The product is deliberately local-first and safety-first. It supports real providers and integrations only when configured, but keeps mock/local fallback so the app can run anywhere. Developer Mode exposes routing decisions, provider metadata, Memory v2 details, tool traces, storage status, approvals, governance logs, worker status, and code-change state.

## Current Platform Snapshot

| Area | Current State |
|---|---|
| Platform direction | EvolveAgent OS / v200 Command Center |
| Current foundation | v220 Compute Fabric |
| Backend | FastAPI with 143 service modules, 87 split route modules, roughly 790 API route handlers |
| Frontend | React + Vite premium UI with Simple Mode and Developer Mode |
| Storage | `StorageService` with JSON fallback, PostgreSQL/JSONB support, pgvector-ready Memory v2, optional Redis |
| Safety model | Governance logs, approval gates, permission profiles, prompt-injection checks, secret scanning |
| Recent emphasis | Cost tracking, code-change workflows, worker lifecycle, Compute Fabric readiness |

## Architecture Summary

```text
User
  -> React UI
  -> FastAPI API
  -> EVA / Master Agent
  -> Workspace Brain + Memory v2
  -> Specialist Agents / Custom Agents
  -> Tool Router + MCP Hub
  -> Governance + Approvals
  -> Durable Workflows / Safe Services
  -> Verification
  -> Storage + Memory + Analytics + Audit Logs
```

## Core Product Areas

### EVA / Master Agent

EVA is the top-level router. It decides whether a request is chat, research, code work, document analysis, workflow planning, tool usage, memory retrieval, or a higher-level operating-system task.

### Workspace Brain + Memory v2

The memory layer stores project facts, user preferences, decisions, task results, workflow history, and knowledge context. Memory v2 supports pgvector-ready semantic recall with keyword fallback.

### Mission Control

Mission Control turns large goals into phases, subtasks, dependencies, priorities, blockers, and next-best-task recommendations.

### Agent Registry

Agents are reusable specialists with roles, prompts, tools, permissions, versions, and performance history. The platform supports built-in agents, custom agents, departments, agent teams, and marketplace-style skill packs.

### Tool + MCP Hub

The tool layer plans connector usage for systems like GitHub, Linear, filesystem, Git, Slack, Notion, and other MCP-style tools. Connectors are governed by policies, approvals, risk levels, audit logs, and read-only or mock-safe defaults.

### Governance + Approvals

Governance checks prompt injection, secret exposure, permission rules, approval requirements, blocked actions, and audit logging. Risky actions such as editing files, pushing code, sending external messages, deleting data, or running commands must go through approval gates.

### Autonomous Software Team

The code-change pipeline is approval-gated. It can propose changes, surface diffs, wait for approval, write files through safe services, run checks, push branches, and prepare PR state. The design goal is verified work, not blind autonomy.

### Compute Fabric

The v220 foundation introduces worker registration and opt-in compute adapters such as a Kaggle GPU worker. This is the beginning of a distributed execution layer where approved jobs can be routed to workers with lifecycle tracking and analytics.

## What Makes It Different

- **Not just chat:** it manages goals, agents, tools, approvals, verification, memory, and outcomes.
- **Governance-first:** stateful/risky actions are logged, permission-checked, and approval-gated.
- **Local-first:** it can run in mock/local mode without API keys and stores runtime data locally by default.
- **Model-independent:** it is designed to route across OpenAI, Claude, Gemini, Mistral, local models, and future providers.
- **Inspectable:** Developer Mode exposes traces, metadata, memory, approvals, tool activity, storage, workers, and cost state.
- **Outcome-focused:** the product aims to prove work was completed through checks, reports, and audit history.

## Demo Flow

1. Start in **Simple Mode** and ask: "Explain how EvolveAgent works."
2. Switch to **Developer Mode** to inspect routing, agents, memory, and governance metadata.
3. Open **Project Brain** and add/search a memory item.
4. Open **Mission Control** and create: "Build an AI resume analyzer."
5. Open **Approvals** to show how risky actions are held before execution.
6. Open **Code Changes** to inspect the approval-gated software-team workflow.
7. Open **Command Center** to show platform coverage and readiness.
8. Open storage/worker/status panels to show the v200/v220 foundation.

## Resume Bullet

> Built **EvolveAgent AI**, a full-stack AI operating system with FastAPI + React, 143 backend service modules, 87 split route modules, workspace memory, governed MCP-style tool execution, approval-gated code workflows, usage/cost tracking, and a premium Simple/Developer Mode UI.

## Case Study Summary

**Problem:** Most AI tools answer a prompt but do not reliably manage long-running work, approvals, memory, tools, verification, and audit history.

**Solution:** EvolveAgent AI wraps models with an operating layer: EVA routes work, Workspace Brain retrieves context, agents and tools execute through governed services, approvals gate risky actions, verification checks results, and memory/analytics record what happened.

**Result:** A portfolio-grade AI platform demonstrating full-stack engineering, AI orchestration, safety design, backend architecture, frontend product UX, and incremental delivery through protected GitHub workflows.

## Safety Statement

EvolveAgent is designed to be useful without giving AI unchecked power.

- No unrestricted shell execution
- No silent file edits
- No destructive file deletion
- No secret values shown in UI, logs, or API responses
- Risky actions require approval
- External sending/posting/payment/deployment is blocked or approval-gated
- Runtime data is excluded from Git
- The system does not self-train a base model
- The product is not AGI

## Portfolio Talking Points

- I built the project as an operating layer around AI models, not a single-model chatbot.
- I used a consistent backend pattern: route -> service -> storage -> governance.
- I preserved local/mock fallback so the project remains demoable without live provider keys.
- I added governance as a first-class product feature, not an afterthought.
- I separated Simple Mode from Developer Mode so non-technical users get a clean UI while technical reviewers can inspect the system.
- I evolved the project through many small, test-backed versions instead of one risky rewrite.

## Recommended Screenshots

- Home Dashboard / Command Center
- Simple Mode chat response
- Developer Mode trace panel
- Project Brain memory search
- Mission Control goal/task graph
- Approvals queue
- Governance logs
- Code Changes approval/diff panel
- Tool / MCP Hub
- Storage or Memory v2 status
- Worker / Compute Fabric status

## Known Limitations

- Real provider calls require configuration; mock/local mode is the safe default.
- Many external integrations are planning, read-only, or approval-gated by design.
- Production auth and multi-tenant enterprise controls are not the current focus.
- Compute Fabric is a foundation, not a full distributed supercomputing platform yet.
- The system is an AI operating layer, not a foundation model or AGI.

## Future Direction

The long-term direction is to keep strengthening the foundation:

- deeper Memory v2 and Workspace Brain
- stronger model-independent routing
- durable workflows and retries
- richer agent registry and evaluation
- real integrations under governance
- broader Compute Fabric worker support
- better frontend coverage and manual demo polish

The positioning remains:

> Claude, OpenAI, Gemini, and local models are intelligence engines. EvolveAgent is the control plane that gives those models memory, tools, governance, workflows, verification, and long-running project context.
