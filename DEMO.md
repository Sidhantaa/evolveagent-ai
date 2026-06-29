# EvolveAgent AI Demo Guide

Use this guide for a short portfolio, class, or interview demo of **EvolveAgent AI** — now positioned as **EvolveAgent OS**, with completed roadmap coverage through **v40.0 — EvolveAgent Operating Layer**.

> **v36–v40 demo add-ons (Developer Mode panels):** Innovation Lab (research/ideas/experiments), Simulation World (deterministic mock scenarios), Organization OS (local orgs/members/roles — no auth), Hardware Companion (device readiness — no mic/wake-word/hardware access), and the EvolveAgent Operating Layer (capability map + readiness snapshot + recommendations + final report).
>
> **Talking point:** *This is not AGI — the operating layer is a governed orchestration dashboard across existing agents, workflows, tools, memory, simulations, and dashboards. Risky actions stay behind human approval.*

> **EvolveAgent OS** is a local-first, workspace-aware multi-agent AI platform with governed automation, plugins, analytics, evaluation, and portfolio management.

## Current Demo Positioning

The core demo should present EvolveAgent AI as a governed AI operating workspace:

- **v15.0 OS platform base** — installer readiness, plugin SDK, SLA monitoring, scheduler overview, and launch summary.
- **v16.0-v17.0 agent organization** — departments, reusable agent teams, workforce templates, ratings, and permission profiles.
- **v18.0-v20.0 business intelligence** — business automation, AI chief-of-staff planning, and business simulation.
- **v21.0 multi-modal real-world agent** — visual/screenshot-style analysis and real-world input interpretation through the same governed workflow.
- **v22.0 in progress** — industry workflow modes for specialized domains.

## EvolveAgent OS Demo Add-On

In Developer Mode, open the **EvolveAgent OS** sidebar panel to show the final platform-readiness layer:

- **Installer readiness** — backend/frontend setup steps, required + optional environment variables, verification commands, and missing-config warnings (read-only; nothing is installed or executed).
- **Plugin SDK** — manifest schema, permission levels, allowed tool types, and a live manifest validator (`POST /api/os/plugin-sdk/validate`).
- **SLA monitoring** — uptime proxy score, success/fallback rate, blocked actions, failed jobs, and a reliability rating derived from local data only.
- **Scheduler overview** — queued/running/failed jobs, pending approvals, scheduler health, and bottlenecks.
- **Launch summary** — `GET /api/os/summary` combines all of the above; use the panel's "Copy launch summary" button for a one-shot platform snapshot.

Talking point: *EvolveAgent OS is local-first and governed — not fully autonomous without approval, not a self-training base model, not a hosted SaaS, and with no unrestricted shell access.*

Simple Mode stays clean and does not expose these OS internals.

## 2-Minute Demo Script

**0:00-0:15 — Introduce the project**

EvolveAgent AI is a workspace-aware multi-agent AI operating workspace with a polished Jarvis-style interface. It combines chat, voice input, files, recordings, image prompts, Mission Control goals, custom agents, Project Brain search, tool routing, approvals, analytics, learning, and Developer Mode transparency.

**0:15-0:35 — Show Simple Mode**

Run:

```text
Explain how EvolveAgent AI works.
```

Show the Jarvis-style Simple Mode: a clean voice/text-first command center, a normal assistant answer, light/dark theme toggle, and minimal controls.

**0:35-0:55 — Show Developer Mode**

Switch to Developer Mode and show:

- task type and confidence
- agents used
- provider/model metadata
- workflow trace
- judge score
- per-agent evaluation
- consensus candidates when Deep Mode is enabled
- tool trace when a tool is selected

**0:55-1:15 — Show Project Brain**

Open the Knowledge Base / Project Brain panel. Search memory, chats, files, recordings, goals, and custom agents. Show cross-session links and memory importance/pinning if data exists.

Demo prompt:

```text
Search my project knowledge for app automation decisions.
```

**1:15-1:35 — Show file or recording intelligence**

Upload a document or recording and ask:

```text
Summarize this uploaded document.
```

or:

```text
Summarize this recording and list action items.
```

Explain that the backend validates uploads, extracts or transcribes text, caps context, and routes the result through specialist agents.

**1:35-1:50 — Show safe automation and approvals**

Run:

```text
Add a small settings page to this app.
```

Show that EvolveAgent AI plans the work and asks for approval before any apply step. In Developer Mode, open the Approval Queue and Approval Audit.

**1:50-2:00 — Show Agent OS panels**

Open Developer Mode and show:

- Agent Jobs panel
- System Prompt Registry panel
- Analytics / Learning panel

Explain that the current project has grown from a polished multi-agent chat workbench into a local-first AI operating workspace with departments, agent teams, business workflows, simulation, and multi-modal analysis.

## Best Demo Prompt Order

1. `Explain how EvolveAgent AI works.`
2. `Search my project knowledge for app automation decisions.`
3. `Calculate 184 * 27.`
4. `Generate an image prompt for a futuristic AI assistant.`
5. Upload a document and ask: `Summarize this uploaded document.`
6. Upload a recording and ask: `Summarize this recording and list action items.`
7. Turn on Deep Mode and ask: `Compare the best plan for improving this project demo.`
8. `Build an AI resume analyzer app.`
9. Open Mission Control and run one task.
10. Create a custom `Resume Agent` from the template list.
11. `Add dark mode to this app.`
12. Toggle light/dark mode and resize the browser to show the responsive layout.
13. Open Developer Mode and show Approval Queue, Tool Trace, Agent Jobs, and System Prompt Registry.

## How to Explain the Master Agent

The Master Agent is the supervisor. It receives the request, loads workspace context, detects the task type, chooses a workflow, tracks execution, and returns one final response.

## How to Explain Project Brain

Project Brain is a JSON-backed knowledge layer. It searches across workspace memory, chats, files, recordings, goals, and custom agents. It can export knowledge as Markdown or JSON, link related records across sessions, and rank memories by importance, pinning, recency, and usage.

It is not a vector database yet.

## How to Explain Assistant Tools and Tool Router

Assistant Tools are small safe utilities such as calculator, password generation, system info, temperature conversion, and knowledge search. The Tool Router chooses relevant tools through the registry and records a Developer Mode Tool Trace.

Simple Mode hides tool internals. Developer Mode shows selected tools, sanitized inputs, permission level, execution status, and result summary.

## How to Explain Approval Workflow 2.0

Approval Workflow 2.0 blocks risky actions until approved. It stores approval chains, queue entries, audit records, rejection/rollback records, and optional webhook notifications.

Key safety points:

- file edits require approval
- command runs require approval
- execute-level tools require approval
- rejected work is not applied
- every decision is logged

## How to Explain Agent Jobs

Agent Jobs are persisted background-style work records. The Developer Mode panel can create a test job, start the next queued job, pause/resume/cancel jobs, send heartbeat updates, and show job health.

## How to Explain System Prompt Registry

The System Prompt Registry centralizes agent prompts and connects to prompt versioning. Prompt changes are controlled and reversible. The app does not silently retrain or rewrite the base model.

## How to Explain Simple Mode vs Developer Mode

Simple Mode is for normal users. It shows the answer, image/file/recording result if relevant, feedback, copy/regenerate/view details/delete, and a clean voice/text interface.

Developer Mode is for demos and debugging. It shows workflow trace, provider metadata, consensus, tool trace, approvals, agent jobs, system prompts, file context, recording transcripts, governance events, learning reports, and raw JSON.

## Final Interview-Style Explanation

EvolveAgent AI is a full-stack multi-agent AI operating workspace built with FastAPI and React. It routes each request through a Master Orchestrator Agent, specialist agents, judge/evolution feedback, workspace memory, governed tools, and analytics. It supports real OpenAI mode with mock fallback, Deep Mode consensus, file and recording analysis, mock image prompts, voice input, Mission Control goals, custom agents, Project Brain search, approval-gated automation planning, adaptive learning, and Developer Mode transparency. The roadmap now extends through multi-agent departments, an agent workforce marketplace, business automation, AI chief-of-staff planning, autonomous business simulation, and multi-modal real-world analysis, while keeping risky actions behind approval and governance.

## Demo Checklist

- Backend running at `http://127.0.0.1:8000`
- Frontend running at `http://127.0.0.1:5173`
- Simple Mode works
- Jarvis-style command center works
- Light/dark theme toggle works
- Onboarding walkthrough appears or can be dismissed
- Responsive sidebar works on narrow windows
- Developer Mode works
- Project Brain search/export works
- Assistant Tools work
- Tool Trace appears in Developer Mode when tools are selected
- Approval Queue and Audit appear in Developer Mode
- Agent Jobs panel appears in Developer Mode
- System Prompt Registry panel appears in Developer Mode
- File upload works
- Recording upload works
- Image Agent mock preview works
- Mission Control works
- Custom Agent Builder works
- Feedback and Analytics work
- Backend tests pass
- Frontend build passes
