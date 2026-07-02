# EvolveAgent AI — Interview Explanation Guide

Ready-to-use explanations at multiple lengths, plus answers to the questions interviewers actually ask. Key framing to keep consistent: **it does not retrain the base LLM**; it improves orchestration, routing, prompts, workflows, memory, and evaluation; **automation is governed and approval-based.**

> **Current scale (through v44):** 44 implementation versions · 85 backend services · ~480 API routes · 48 test modules · **494 passing backend tests** · ~10,200-line React UI. The most recent work is the v41–v44 MCP arc (connector hub → execution adapter → opt-in sandboxed read-only adapter → approvals inbox). Some numbers in the answers below (e.g. "222 tests") reflect the v15 milestone at the time of writing — quote the current figures above in interviews. It is **not AGI** — a governed orchestration layer.

---

## 30-Second Explanation

EvolveAgent AI is a local-first, multi-agent AI operating system I built with FastAPI and React. Instead of one chatbot call, every request goes through a Master Orchestrator Agent that routes it to specialist agents, runs it through a governance layer, uses workspace memory for context, and scores the result with a judge and an evaluation lab. Simple Mode shows just the answer; Developer Mode exposes every layer. It works with or without API keys because of mock fallback.

---

## 1-Minute Explanation

EvolveAgent AI is a full-stack multi-agent AI operating system. The core idea is that a normal chatbot gives you one opaque answer, while this system separates the work into inspectable, governed layers. A Master Orchestrator Agent classifies each request, then routes it through specialist agents — research, logic, risk, strategy, and writing — followed by a judge agent that scores quality. Everything passes through a governance layer with a prompt-injection firewall, a secret scanner, a permission system, and an approval queue, so risky actions never run silently. It has workspace memory for project context, file and recording analysis, Mission Control for goal planning, a custom agent builder, an AI evaluation lab, and a project manager dashboard. It's built with FastAPI, React, real LLM integrations, and JSON-based storage, and it runs entirely locally with mock fallback so it always demos cleanly.

---

## 2-Minute Explanation

EvolveAgent AI is a local-first, workspace-aware multi-agent AI operating system. I built it to explore what a safe, transparent alternative to a single-call chatbot looks like.

When a request comes in — text, a file, a recording, or a Linear task — the Master Orchestrator Agent detects the task type and chooses a workflow. For text, it runs a pipeline of specialist agents: research gathers context, logic structures reasoning, risk flags assumptions, strategy recommends next steps, and writing synthesizes the answer. A judge agent then scores the workflow and each agent's contribution, and an evolution agent suggests improvements. All of this is logged.

Around that pipeline are several systems. Workspace memory gives each project its own context, with quality scoring, tiers, and local semantic retrieval — no external vector database. The governance layer enforces safety: a prompt-injection firewall and secret scanner run on every request, tools have permission levels, and edit or run actions require explicit human approval through an approval queue. There's a safe file editor and an allowlisted command runner, so there's no unrestricted shell access.

On top of that, there's Mission Control for breaking goals into task graphs, a custom agent builder with reusable templates, an AI evaluation lab that benchmarks and regression-tests the agents themselves, an AI project manager, portfolio mode for multi-workspace health, and integrations for Linear/Codex development workflows, Slack, and Notion. The EvolveAgent OS layer adds installer readiness, a plugin SDK, SLA monitoring, and a scheduler overview.

Importantly, the system self-optimizes its orchestration layer — prompts, routing, workflows, memory, and evaluation — but it never retrains the base model, and automation always requires approval. It's FastAPI and React with JSON storage, around 222 passing backend tests, and it works with or without API keys.

---

## Technical Architecture Explanation

The backend is FastAPI with thin routes that delegate to service classes. Business logic lives in services, request shapes are Pydantic models, and persistence is JSON through a single StorageService. A request hits `/api/run`, which resolves the workspace, retrieves relevant memory, classifies the task, and dispatches to the right agent workflow through a thin Kernel Service. Each specialist agent is a service that calls an LLM router; the router supports real OpenAI (and optional Anthropic/Gemini/Mistral consensus) with mock fallback. After the workflow, the judge scores the result, analytics and governance records are written, memory is updated, and a structured response goes back.

The frontend is React + Vite with a two-mode UI. Simple Mode renders only the user-facing answer; Developer Mode reads the same response object and surfaces the workflow trace, provider metadata, judge and per-agent scores, tool traces, approvals, agent jobs, and raw JSON. State is kept in App.jsx, API calls in api.js, and styling uses CSS design tokens for light/dark themes.

The whole thing is additive by design — each version (through v15.0) layered new capabilities on top without removing or refactoring existing features, which is why the test suite stayed green throughout.

---

## "What problem does it solve?"

A standard chatbot gives you one answer with no visibility into how it got there, no project memory, no safety gates, and no way to measure quality. EvolveAgent AI separates routing, context, tools, analysis, risk, judging, memory, approvals, analytics, and learning into inspectable layers. That makes the system easier to demo, debug, govern, and improve — and it makes automation safe because risky actions are gated behind human approval.

---

## "How is it different from ChatGPT?"

ChatGPT is a single conversational model. EvolveAgent AI is an orchestration system around models. It uses a Master Agent instead of one direct call, routes through specialist workflows, keeps per-workspace memory, can analyze files and recordings, plans goals into task graphs, supports reusable custom agents, requires approval for risky actions, scores quality with a judge and evaluation lab, and exposes a full Developer Mode trace. It also runs locally with mock fallback, so it doesn't depend on any single provider.

---

## "How does the agent system work?"

The Master Orchestrator Agent is the supervisor. It loads workspace context, detects the task type, and selects a workflow. For text it runs a pipeline — research → logic → risk → strategy → writing — then a judge agent scores the overall workflow and each agent individually, and an evolution agent recommends improvements. File, recording, image, goal, and automation tasks branch into this pipeline at the appropriate point. Custom agents are reusable specialists that run under the same governance and permission rules as built-in ones.

---

## "How does safety/governance work?"

Every request passes a prompt-injection firewall and a secret scanner. Tools and actions have permission levels — read-only, plan-only, approve-to-edit, approve-to-run, and blocked. Read-only actions can run immediately; edit and run actions go to an approval queue and require explicit human approval; blocked actions are denied. There's a safe file editor that validates paths and blocks `.env`, `.git`, `node_modules`, `venv`, and uploads, plus a command runner limited to an allowlist of build and test commands. There's no unrestricted shell, no destructive deletion, and no silent file edits. Every decision is written to a governance log with an audit trail.

---

## "How does learning work?"

The system self-optimizes its orchestration layer through memory, feedback, prompt versions, workflow strategy tracking, and model performance analytics. Concretely: it tracks judge scores, per-agent scores, latency, fallback usage, and human feedback per task type, then produces a learning report with strongest/weakest agents, best/worst workflows, model-routing suggestions, and user-preference patterns. Prompt changes are versioned and only activate after approval, and they can be rolled back. It does **not** fine-tune or retrain the base LLM — the model stays fixed; only the orchestration around it improves.

---

## "What were the hardest engineering challenges?"

- **Keeping it additive.** Every release layered new capabilities on top of a growing system without breaking existing features or tests. That required disciplined service boundaries and reading data shapes carefully before writing new services.
- **Making safety real, not cosmetic.** Designing a permission model and approval flow that actually gates file edits and command execution — while still being demoable — took careful threading through the governance layer.
- **Local semantic memory without a vector DB.** Building quality scoring, tiers, and a JSON-backed sparse vector-style index that retrieves relevant context cheaply and deterministically.
- **Provider abstraction with graceful fallback.** Supporting real OpenAI and optional multi-provider consensus while guaranteeing the app never crashes when keys are missing.

---

## "What would you improve next?"

- Server-Sent Events streaming for token-by-token responses.
- A production-grade vector database / embedding provider to replace the local JSON index.
- OCR for scanned PDFs and speaker diarization for recordings.
- Richer approval diff previews before applying automation.
- User accounts, team workspaces, and a deployment path.
- A real image-generation API behind the existing mock-fallback abstraction.

These are deliberately scoped as next steps — the current system is intentionally local-first and MVP-shaped, which keeps it safe, transparent, and easy to run.
