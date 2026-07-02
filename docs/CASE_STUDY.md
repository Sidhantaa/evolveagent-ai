# EvolveAgent AI: Building a Local-First Multi-Agent AI Operating System

A portfolio case study of EvolveAgent AI — what it is, why it was built, how it works, and what was learned.

> **Current state (through v44 + v44.5 consolidation):** the project has grown well beyond the v15 milestone described in the narrative below. It now spans **44 implementation versions**, **85 backend services**, **~480 API routes**, **48 test modules**, and **494 passing backend tests**, with a ~10,200-line React UI — including the v41–v44 MCP arc (connector hub → execution adapter → read-only adapter → approvals inbox). Historical figures in the prose below (e.g. "222 tests", "v15.0") reflect the milestone at the time of writing. See [`PORTFOLIO_PACK.md`](PORTFOLIO_PACK.md) and [`../VERSIONS.md`](../VERSIONS.md) for the current picture.

---

## 1. Overview

EvolveAgent AI is a local-first, workspace-aware multi-agent AI operating system built with FastAPI, React, real LLM integrations, JSON-based storage, and governed automation. It replaces the single opaque chatbot call with an inspectable, governed pipeline: a Master Orchestrator Agent routes each request through specialist agents, a safety layer, workspace memory, and an evaluation engine, then returns one scored answer. Simple Mode keeps the experience clean for end users; Developer Mode exposes every layer for demos and debugging. The system reached v15.0 with a fully passing backend test suite (222 tests) and a green frontend build.

---

## 2. Problem

A standard chatbot returns one answer with no visibility into how it was produced, no persistent project memory, no safety gates around actions it could take, and no built-in way to measure answer quality. For anyone trying to use an AI assistant for real work — analyzing documents, planning projects, or assisting with development — those gaps make the tool hard to trust, hard to debug, and risky to let act on a codebase.

---

## 3. Motivation

I wanted to understand what a *safe, transparent* AI assistant looks like when you treat it as a system rather than a single model. The goals were: make every decision inspectable, give the assistant durable per-project memory, gate any risky action behind explicit human approval, measure quality continuously, and keep the whole thing local-first so it runs without cloud dependencies or paid keys. The constraint of "additive only — never rebuild" was deliberate: it forced clean architecture and kept the system shippable at every step.

---

## 4. Architecture

The backend is FastAPI with thin routes that delegate to service classes; business logic lives in services, request shapes are Pydantic models, and persistence is JSON through a single StorageService. The frontend is React + Vite with a two-mode UI driven by the same response object.

High-level flow:

```
User / File / Recording / Linear / Workspace Input
        ↓
Master Orchestrator Agent
        ↓
Specialist Agents + Tools + Governance
        ↓
LLM / File / Recording / Automation Workflow
        ↓
Judge + Evaluation + Memory + Analytics
        ↓
Final Answer / Project Update / Export / Report
```

Detailed Mermaid diagrams (system, agent workflow, governance, Linear/Codex, memory, and evaluation flows) are in [`ARCHITECTURE.md`](./ARCHITECTURE.md).

---

## 5. Core Features

- ChatGPT-style workspace with Simple Mode and Developer Mode
- Master-Agent orchestration over specialist agents
- Real LLM providers (OpenAI + optional Anthropic/Gemini/Mistral consensus) with mock fallback
- File and document analysis; recording intelligence with transcription
- Image Agent (mock, with real-provider fallback path)
- Workspace memory with quality scoring, tiers, and local semantic retrieval
- Mission Control goal planning and task graphs
- Custom Agent Builder and Agent Skill Store
- Security/governance: prompt-injection firewall, secret scanner, permission system, approval workflow
- Safe file editor and allowlisted command runner
- Linear/Codex development workflow, Slack notifications, Notion export
- AI Evaluation Lab, AI Project Manager, Portfolio Mode
- EvolveAgent OS platform layer (installer readiness, plugin SDK, SLA monitoring, scheduler overview)

---

## 6. Multi-Agent Workflow

The Master Orchestrator Agent classifies each request and selects a workflow. For text, specialist agents run in a pipeline: **research** gathers context, **logic** structures reasoning, **risk** flags assumptions, **strategy** recommends next steps, and **writing** synthesizes the final answer. A **judge** agent then scores the overall workflow and each agent's contribution, and an **evolution** agent recommends improvements. File, recording, image, goal, and automation tasks branch into this pipeline at the right point. Custom agents are reusable specialists that operate under the same governance and permission rules as built-in agents.

---

## 7. Security and Governance

Safety is a first-class layer, not an afterthought. Every request passes a prompt-injection firewall and a secret scanner. Tools and actions carry permission levels — `read_only`, `plan_only`, `approve_to_edit`, `approve_to_run`, `blocked`. Read-only actions run immediately; edit/run actions go to an approval queue and require explicit human approval; blocked actions are denied. A safe file editor validates paths and blocks `.env`, `.git`, `node_modules`, `venv`, and uploads. The command runner is limited to an allowlist (`npm run build`, `npm test`, `npm run lint`, `pytest`, `python -m pytest`). There is no unrestricted shell, no destructive deletion, and no silent file editing. Every decision is written to a governance log with an audit trail.

---

## 8. Workspace Memory and Mission Control

Workspace memory scopes context per project. Before each run, a small capped set of high-value memories is retrieved with local semantic-style scoring; new results are quality-scored, tiered (hot/warm/archived), indexed in a JSON-backed sparse vector-style index, and periodically consolidated — all without an external vector database. Mission Control turns larger objectives into plans: the Goal Planner Agent generates phases, a task graph, dependencies, risk level, and a next-best-task recommendation, and each task can be run through the standard workflow with progress tracked end to end. Goal mode never silently executes code — automation still goes through approval.

---

## 9. Linear/Codex Automation

An optional, server-side Linear/Codex workflow connects the assistant to real development. When a Linear issue moves to In Progress, the backend can create a `linear/evo-*` branch, write a handoff file under `docs/linear-handoffs/`, and trigger a guarded Codex worker job. The job runs the test suite and frontend build, then posts a success or failure comment back to Linear. Keys live in `backend/.env` and are never exposed to the frontend; full autonomous mode is disabled by default, and verification gates every completion.

---

## 10. AI Evaluation Lab

The Evaluation Lab measures the agents themselves. It runs benchmarks, A/B tests, and regression checks, feeding results back into analytics and the Adaptive Learning Engine. The learning layer self-optimizes the orchestration — prompt versions, workflow strategy, model routing, and user preferences — and proposed prompt changes are approval-gated and reversible. The base LLM is never retrained; only the orchestration around it improves.

---

## 11. Project Manager and Portfolio Mode

The AI Project Manager surfaces project risks and status reports, giving a structured view of where work stands. Portfolio Mode rolls multiple workspaces into a single health view, aggregating regression health and status across projects — useful for demoing the system as a platform rather than a single workspace.

---

## 12. Technical Stack

- **Backend:** Python, FastAPI, Pydantic, Uvicorn, OpenAI SDK, pypdf, python-docx, JSON storage
- **Frontend:** React, Vite, JavaScript, CSS design tokens, react-markdown, remark-gfm, lucide-react
- **Testing:** Pytest (222 passing backend tests), Vite build verification
- **Workflow:** Git branch-per-issue, Linear/Codex automation, Slack/Notion integrations

---

## 13. Challenges

- **Additive-only delivery.** Every release layered new capabilities without breaking existing features or tests, which demanded disciplined service boundaries and careful inspection of existing data shapes.
- **Real, enforceable safety.** Building a permission model and approval flow that genuinely gate file edits and command execution while staying demoable.
- **Local semantic memory.** Implementing quality scoring, tiers, and a JSON-backed sparse vector-style index that retrieves relevant context cheaply and deterministically, with no vector database.
- **Provider abstraction with graceful fallback.** Supporting real OpenAI and optional multi-provider consensus while guaranteeing the app never crashes when keys are missing.

---

## 14. Results

EvolveAgent AI reached v15.0 as a coherent, local-first multi-agent platform: a Master-Agent orchestration core, a real safety/governance layer, workspace memory, file/recording intelligence, Mission Control, custom agents, an evaluation lab, project and portfolio dashboards, and an EvolveAgent OS platform-readiness layer — with 222 passing backend tests and a green frontend build. The two-mode UI makes it both clean for end users and fully transparent for technical review, and mock fallback keeps it demoable anywhere.

---

## 15. Limitations

- No authentication, cloud database, or deployment setup (intentionally local-first/MVP)
- No production vector database or RAG search — local JSON index only
- No OCR for scanned PDFs; no speaker diarization; no full video understanding
- No real image-generation API enabled by default (mock with fallback path)
- JSON storage is for MVP/demo scale, not distributed workloads
- Agent Jobs are local persisted records, not distributed workers

---

## 16. Future Roadmap After v15

- Server-Sent Events streaming for token-by-token responses
- Production-grade vector database / embedding provider behind the existing memory abstraction
- OCR and scanned-PDF support; speaker diarization for recordings
- Richer approval diff previews before applying automation
- User accounts, team workspaces, and a deployment path
- Real image-generation API behind the current mock-fallback abstraction
- Expanded model-routing policies and cost tracking

---

*EvolveAgent AI is a decision-support and productivity system. It does not provide legal, medical, financial, or professional advice, and human review is required before acting on its outputs.*

---

## v41 — MCP Connector Hub

The EvolveAgent MCP Connector Hub prepares and governs tool connections through local connector records, dry checks, approval boundaries, and audit logs. It introduces a local connector registry (GitHub, Linear, Filesystem, Git, Context7, Playwright, Slack, Notion, Desktop Commander) with per-connector risk levels and modes (read-only vs approval-required vs disabled), env-key readiness checks that report only whether keys are set (true/false), governance logging of every stateful action, and an action-planning flow that enforces approval and risk rules. There is no real MCP execution by default, no secrets exposed, no unrestricted shell, and no full desktop control; high-risk connectors stay approval-required or disabled by default. This keeps EvolveAgent ready to adopt MCP tooling while staying local-first, permission-aware, and governed.

---

## v42 — MCP Execution Adapter

Where v41 prepared and governed tool connections, v42 adds the execution loop that keeps them safe in practice. A request → approve → run → record flow reuses the v41 planning rules to validate each request, auto-approves only read-only low-risk actions, and holds everything else for explicit human approval. Approved requests run through a mock executor: execution is always simulated, so there is no real MCP server, network call, shell command, or device action, and no secrets are used. Run-time re-validation blocks any request whose connector has since been disabled, and every step is governance-logged. This demonstrates a realistic, auditable path toward live tool execution while staying local-first, approval-gated, and mock-by-default.

---

## v43 — MCP Read-Only Adapter

v41 registered connectors, v42 added the approve/run loop, and v43 makes the run actually do something — safely. The MCP Read-Only Adapter is the project's first real tool execution: an opt-in, sandboxed, read-only path for a small allow-list of git and filesystem actions. It uses the standard library only (no shell, network, writes, or secrets), never returns file contents, and is sandboxed to the repo root with traversal and denylist protection. Real execution requires an explicit env opt-in on top of connector-enabled and human approval; otherwise it falls back to the v42 mock. This demonstrates a realistic, auditable path from planning to live tool execution while staying inside the platform's safety contract.

---

## v44 — MCP Approvals Inbox

With a real execution path in place (v43), the natural governance need is a single place to review what is waiting on a human. The MCP Approvals Inbox aggregates all pending MCP execution requests into one prioritized queue — enriched with connector name, risk level, and age, and sorted so high-risk and oldest items surface first. Approving or rejecting delegates to the governed execution service, so the inbox never bypasses the existing controls; it simply makes triage fast and auditable. It demonstrates a common real-world governance pattern (an approvals queue) built on top of the existing governed primitives rather than around them.

---

## v45 — MCP Policy Engine

After building a real (but sandboxed) execution path and an approvals inbox, the next governance need is declarative control over what may even be attempted. The MCP Policy Engine lets an operator write deny rules — by connector, action, or risk level, with wildcards and carve-outs — that are evaluated before connector planning. It is deliberately tighten-only: there is no allow effect, so a policy can only add a block, never grant new access. This is a common real-world guardrail pattern (deny-by-policy) layered on top of the existing governed primitives without changing default behavior.

---

## v46 — MCP Audit & Replay

Governance is only as good as its audit trail. v46 aggregates the whole MCP surface — connector events, executions, and MCP governance — into one read-only timeline with export, and adds a dry replay that shows how a past request would be evaluated under todays connectors and policies without executing anything. Combined with the v45.1 UI pass (tabbed MCP Hub), the MCP arc now reads as a coherent, inspectable governance story from registration through audit.

---

## v47 — Secret Reference Registry

Managing integrations means tracking secrets without ever touching them. The Secret Reference Registry catalogs which env keys each connector needs, whether they are set, and when they should be rotated — recording only the key name and a readiness boolean. It demonstrates a security-conscious pattern: know your secret surface and rotation posture while guaranteeing values are never stored, logged, or returned. It extends the MCP arc from planning and execution into operational hygiene, all within the local-first, governed contract.

---

## v48 — Unified Approvals Center

Approvals were scattered across subsystems, so v48 unifies them. It aggregates every pending approval — MCP executions and business-operator items today — into one prioritized queue and routes each decision back to the service that owns it. This is the classic inbox pattern generalized across a platform, built on top of existing governed primitives without adding any new execution authority.

---

## v49 — Health & Readiness Monitor

As the platform grew, a single readiness view became valuable. The Health & Readiness Monitor scores governance, approvals backlog, secret readiness, connectors, and policy posture into one dashboard with actionable recommendations — entirely read-only, derived from existing local state. It demonstrates observability layered on top of the governed primitives without introducing any new authority.

---

## v50 — Cost & Usage Ledger

Cost visibility matters even in a mock-first system. The Cost & Usage Ledger records usage estimates per capability and workspace, tracks budgets, and warns as usage approaches or exceeds them — all as estimates, with no billing or payment. It extends the early v11 cost-control work into a first-class, governed ledger.

---

## v51 — Local Retrieval Layer

Grounding answers in your own documents usually implies an external vector database. v51 shows it can stay local-first: it chunks documents, scores keyword overlap, and returns cited passages entirely on the local machine — no external service, no network. It extends the early memory-intelligence work into a lightweight, governed retrieval layer consistent with the platforms local-first contract.
