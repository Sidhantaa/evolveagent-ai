# EvolveAgent AI — Portfolio Pack

A single reference for presenting EvolveAgent AI in a portfolio, résumé, or interview.

---

## 1. One-line pitch

EvolveAgent AI is a local-first, workspace-aware multi-agent AI operating system built with FastAPI + React, featuring governed automation, JSON persistence, workspace memory, agent orchestration, project/business/personal operating layers, MCP connector planning, and Developer Mode observability.

## 2. 30-second explanation

EvolveAgent AI takes a user request, routes it through a **Master Agent** to a team of specialized sub-agents (research, logic, risk, strategy, writing, judge), and returns an auditable, governed result. Every stateful action is logged by a governance layer, all data is stored locally as JSON, and real provider calls are opt-in with a mock fallback. On top of that core it layers 44 versions of capabilities — memory, tools, project/business/personal "operating systems," and an MCP tool-connection layer — all behind a two-mode UI: a clean **Simple Mode** for users and a detailed **Developer Mode** for inspection.

## 3. 1-minute explanation

Most AI apps are a thin wrapper over one model call. EvolveAgent AI is instead built like an **operating system for agents**. A request enters through `/api/run`; the Master Agent detects the task type and selects sub-agents; they run (with a judge/consensus step) and produce a final output. Around that core, every feature follows one strict pattern — a thin route delegates to a service, which persists to local JSON via `StorageService` and logs every stateful action to `GovernanceService`, and surfaces a Developer-Mode panel.

The platform grew across 44 versions: an Agent-OS foundation (tools, plugins, approvals, jobs), memory intelligence (locally scored/tiered/retrieved), real-API control (opt-in with mock fallback), then "operating layers" for projects, business, and personal life, an agent organization/marketplace, simulation and innovation labs, an executive board, and most recently a four-version **MCP arc**: register tool connectors → govern their execution → add a real (but sandboxed, read-only, opt-in) execution path → a unified approvals inbox.

The whole thing is deliberately **safe by construction**: local-first, mock/planning-first, permission-aware, and governance-logged. It does not add production auth, payments, unrestricted shell, real device/hardware control, or model self-training — and it is explicit that it is *not AGI*.

## 4. Technical architecture summary

```
User → /api/run → Master Agent (task detection, sub-agent selection)
       → sub-agents (real LLM opt-in, mock fallback) → judge/consensus → output

Every feature:  thin route → service → StorageService (local JSON)
                            → GovernanceService (logs every stateful action)
                            → Simple Mode / Developer Mode UI
```

- **Backend:** Python 3 / FastAPI / Pydantic / Uvicorn — 85 services, ~480 routes.
- **Frontend:** React + Vite (single-file `App.jsx`, ~10,200 lines), two-mode UI.
- **Storage:** local JSON via `StorageService` (no external database).
- **Governance:** `GovernanceService` records agent, action, risk, approved/blocked, reason.
- **Providers:** OpenAI / Anthropic, opt-in with mock fallback everywhere.
- **Tests:** 48 test modules, 494 passing backend tests; green frontend build.

## 5. What makes it different from ChatGPT

- **Multi-agent, not single-shot** — a Master Agent orchestrates specialized sub-agents with a judge/consensus step.
- **Governed & auditable** — every stateful action is logged; risky actions are approval-gated.
- **Local-first** — all data is local JSON; no hosted account or external DB required.
- **Planning-first** — risky/real actions are drafted or simulated by default; real execution is opt-in and bounded.
- **Two modes** — clean for end users, fully transparent for technical review.
- **Operating layers** — project, business, and personal "OS" surfaces, plus an MCP tool-connection layer — not just chat.

## 6. Main feature categories

- **Core:** multi-agent orchestration, workspace memory, tools/plugins, approvals, jobs, evaluation.
- **Project/Portfolio:** AI project manager, portfolio dashboards, self-healing checks.
- **Business:** business automation, advanced business operator, simulator, executive board, compliance intelligence.
- **Personal:** chief of staff, life OS, digital twin, avatar (settings only), device operator (planning only).
- **Organization:** multi-agent departments, agent marketplace, multi-user organization OS (local records).
- **Research/Simulation:** innovation lab, simulation world.
- **MCP arc:** connector hub, execution adapter, read-only adapter, approvals inbox.
- **Operating layer:** a governed cross-system orchestration dashboard.

## 7. Safety / governance summary

Local-first · mock/planning-first · permission-aware · governance-logged · additive. **Not present by design:** unrestricted shell, destructive autonomous file operations, real sending/payment without approval, production auth, real phone/hardware control, microphone recording / wake-word listening, base-model self-training. Real capabilities are opt-in with mock fallback; secrets are never exposed to the frontend, logs, or API responses.

> **This is not AGI. It is a governed orchestration layer across existing agents, workflows, tools, memory, simulations, and dashboards.**

## 8. Scale metrics

| Metric | Value |
|---|---|
| Implementation versions | 44 (+ v44.5 consolidation) |
| Backend services | 85 |
| API routes | ~480 |
| Backend test modules | 48 |
| Passing backend tests | 494 |
| React UI | single-file `App.jsx`, ~10,200 lines |

## 9. Résumé bullet

> Designed and built **EvolveAgent AI**, a local-first multi-agent AI operating system (FastAPI + React) spanning **44 iterative versions**, **85 services**, **~480 API routes**, and **494 passing tests** — with a governed architecture (per-action audit logging, approval gates, opt-in real providers with mock fallback) and a four-version MCP tool-connection layer that safely advances from planning to sandboxed, read-only execution.

## 10. Interview talking points

- **Why multi-agent?** Separation of concerns + a judge/consensus step improves reliability over a single call.
- **Governance by construction** — one pattern (route → service → storage → governance) applied across 44 versions kept the suite green throughout.
- **Safety trade-offs** — planning/mock-first, opt-in real capability with mock fallback, hard boundaries (no shell/auth/payments/hardware). The MCP arc shows judgment: real execution is introduced only as sandboxed, read-only, opt-in, approval-gated.
- **Additive versioning** — each version layered on top without breaking API contracts, which is why 44 versions coexist.
- **Honest scoping** — explicitly *not AGI*; a governed orchestration layer.

## 11. Demo flow (5–7 min)

1. What it is (multi-agent OS, local-first, governed).
2. Architecture: Master Agent → sub-agents → governance.
3. Simple Mode vs Developer Mode.
4. A governance/safety example (approval-gated action).
5. Memory / project / portfolio dashboards.
6. MCP Hub (connectors, execution, read-only adapter, approvals inbox).
7. Operating Layer dashboard.
8. Why it's different from a chatbot.
9. Close: local-first, governed, planning-first, *not AGI*.

(See `docs/DEMO_VIDEO_SCRIPT.md` for the full script and `screenshots/README.md` for the capture list.)

## 12. Known limitations

- Real provider calls require configuration; default behavior is mock so it runs anywhere.
- MCP execution is mock by default; the only real path (v43) is opt-in, sandboxed, and read-only.
- Organization/team features are local records — no production authentication.
- Personal device/app operators are planning/mock only — no real device or app control.
- Single-file React UI is large; a component split is future work.

## 13. Future roadmap (v45–v55)

| Ver | Name | Theme |
|---|---|---|
| v45 | MCP Policy Engine | Declarative allow/deny policies before planning |
| v46 | MCP Audit & Replay | Unified audit timeline + read-only replay/export |
| v47 | Secret Reference Registry | Key-reference readiness + rotation (never values) |
| v48 | Unified Approvals Center | Generalize the inbox across all approval sources |
| v49 | Health & Readiness Monitor | Aggregate dry-checks into a scored dashboard |
| v50 | Cost & Usage Ledger | Usage estimates + per-workspace budgets |
| v51 | Local Retrieval Layer | Local chunking/retrieval grounding (no external DB) |
| v52 | Evaluation Harness 2.0 | Repeatable scorecards + regression tracking |
| v53 | Playbook Library | Saved, governed multi-step plans (mock/planning) |
| v54 | (folded into this v44.5 pass) | Portfolio/demo consolidation |
| v55 | Operating Layer 2.0 | Refresh the capability map across v41–v54 |

**Recommended next step:** v45 — MCP Policy Engine, after this portfolio pass.
