# EvolveAgent AI — Demo Video Script (5–7 minutes)

A scene-by-scene script with narration and suggested prompts. Target length: **5–7 minutes**. Before recording, run the backend at `http://127.0.0.1:8000` and the frontend at `http://127.0.0.1:5173`, and keep mock mode on (`LLM_MODE=mock`) for clean, cost-free captures.

> Do **not** attempt to show all 44 versions individually — pick the beats below and let the architecture tell the story.

---

## 1. Opening — what EvolveAgent AI is (≈30s)

**On screen:** Simple Mode home.

> "This is EvolveAgent AI — a local-first, workspace-aware multi-agent AI operating system built with FastAPI and React. Instead of one opaque chatbot call, every request is routed through a Master Agent to a team of specialist agents, wrapped in a governance layer, workspace memory, and a two-mode UI. It runs entirely on your machine with JSON storage, and works with or without API keys thanks to mock fallback."

## 2. Architecture — Master Agent + services + governance (≈45s)

**On screen:** Developer Mode; run `Explain how EvolveAgent AI works.`

> "Under the hood the flow is simple and consistent. A request hits `/api/run`; the Master Agent detects the task type and picks sub-agents — research, logic, risk, strategy, writing — and a judge step reconciles them. Every feature in the system follows one pattern: a thin route calls a service, the service stores state as local JSON, and every stateful action is recorded by a governance layer. That single pattern is why 44 versions of features coexist without breaking each other."

## 3. Simple Mode vs Developer Mode (≈40s)

**On screen:** Toggle between the two modes on the same answer.

> "There are two lenses on the same engine. Simple Mode is a clean console for end users. Developer Mode exposes the workflow trace, the agents used, tool calls, approvals, memory, and governance events — full transparency for technical review, without changing what the system actually does."

## 4. Governance / safety example (≈45s)

**On screen:** Developer Mode → governance panel; trigger an approval-gated action.

> "Safety is built in, not bolted on. Risky actions are planned, not executed — they become approval-gated steps, and every decision is logged with its risk level and reason. There's no unrestricted shell, no real sending or payments without approval, no production auth, and no device or hardware control. The platform is explicit that it is *not AGI* — it's a governed orchestration layer."

## 5. Memory, project & portfolio dashboards (≈50s)

**On screen:** Memory panel → Project Manager → Portfolio Mode.

> "Workspace memory is scored, tiered, and retrieved locally — no external vector database. On top of that sit operating layers: an AI Project Manager for tasks and goals, and Portfolio Mode to roll multiple projects into one view. These are the 'OS' surfaces that make it more than a chat window."

## 6. MCP Hub (≈60s)

**On screen:** Developer Mode → MCP Hub panel.

> "The newest work is a four-version MCP arc. The MCP Hub is a local registry of tool connectors — GitHub, Linear, Filesystem, Playwright, and more — each with a risk level and mode. Status checks are dry and only report whether required keys are *set*, never their values. From there, an execution adapter runs actions through a governed request-approve-run loop, mock by default. A read-only adapter can do real, opt-in, sandboxed reads — like listing a directory or the current git branch — with no shell, no network, and no secrets. And an approvals inbox aggregates everything waiting on a human, high-risk first."

## 7. Operating Layer (≈40s)

**On screen:** Developer Mode → EvolveAgent Operating Layer.

> "The Operating Layer is the capstone dashboard: it maps the platform's capabilities across every subsystem, generates a readiness snapshot and cross-system recommendations, and surfaces the safety boundaries — one governed view of the whole system."

## 8. Why it's different from a chatbot (≈30s)

**On screen:** Split of Developer Mode panels.

> "So why is this different from a chatbot? It's multi-agent, not single-shot. It's governed and auditable, not opaque. It's local-first, not hosted. And it's planning-first — real, risky actions are simulated or approval-gated by default. It's an operating system for agents, not a wrapper over one model call."

## 9. Closing (≈20s)

**On screen:** Simple Mode home.

> "EvolveAgent AI: local-first, governed, planning-first — 44 versions, 85 services, and nearly 500 passing tests, all on your machine. Not AGI — a governed orchestration layer across agents, workflows, tools, memory, simulations, and dashboards."

---

### Prompt reference
- `Explain how EvolveAgent AI works.`
- `Search my project knowledge for app automation decisions.`
- `Build an AI resume analyzer app.`

### Capture notes
- Keep a consistent browser width; hide secrets; never show `.env` or private data.
- See `screenshots/README.md` for the prioritized shot list and `docs/DEMO_DATA_CHECKLIST.md` for demo-ready data.
