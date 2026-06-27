# EvolveAgent AI — Resume Bullets

Accurate, portfolio-ready wording for resumes, LinkedIn, and applications. Pick the version that fits the space you have.

---

## One-Line Project Description

EvolveAgent AI — a local-first, workspace-aware multi-agent AI operating system built with FastAPI, React, real LLM integrations, JSON-based storage, and governed automation.

---

## Short Resume Bullet

Built EvolveAgent AI, a full-stack multi-agent AI operating system (FastAPI + React) with Master-Agent orchestration, governed automation, workspace memory, and an AI evaluation lab.

---

## Long Resume Bullet (Primary)

Built EvolveAgent AI, a local-first multi-agent AI operating system using FastAPI, React, OpenAI, and JSON-based storage, featuring master-agent orchestration, workspace memory, file and recording intelligence, Mission Control goal planning, custom agent builder, governed automation, Linear/Codex task workflows, Slack/Notion integrations, AI Evaluation Lab, AI Project Manager dashboards, Portfolio Mode, and Developer Mode observability.

---

## Detailed Bullets (8–12)

- Architected a multi-agent orchestration system around a Master Orchestrator Agent that classifies requests, routes them through specialist agents (research, logic, risk, strategy, writing, judge, evolution), and returns a single evaluated answer.
- Implemented real LLM provider integrations (OpenAI, plus optional Anthropic/Gemini/Mistral consensus) with automatic mock fallback, keeping the app fully demoable with or without API keys.
- Built a governance and safety layer with a prompt-injection firewall, secret scanner, permission system, approval queue, safe file editor, and an allowlisted command runner — no unrestricted shell execution and no silent file edits.
- Designed workspace memory with quality scoring, hot/warm/archived tiers, a local JSON-backed sparse vector index, semantic-style retrieval, and consolidation jobs — no external vector database.
- Added file and recording intelligence: validated uploads, text extraction for PDF/DOCX/CSV/code, and mock/OpenAI transcription producing summaries, action items, and decisions.
- Created Mission Control for goal planning, generating phases, task graphs, dependencies, risk levels, and next-best-task recommendations, with runnable subtasks tracked end to end.
- Built a Custom Agent Builder and Agent Skill Store with reusable, governed specialist agents created from templates that operate under the same permission and governance rules as built-in agents.
- Implemented an Adaptive Learning Engine that self-optimizes the orchestration layer via prompt versioning, workflow-strategy memory, model-performance tracking, and user-feedback signals — without retraining the base model.
- Developed an AI Evaluation Lab with benchmarks, A/B tests, and regression detection, plus an AI Project Manager and Portfolio Mode for multi-workspace risk and health reporting.
- Integrated an optional Linear/Codex development workflow that branches issues, writes handoff files, runs guarded worker jobs, and gates completion on test + build verification, with keys kept server-side.
- Added Slack notifications and Notion export integrations for governed, opt-in external reporting.
- Shipped an EvolveAgent OS platform layer (installer readiness, plugin SDK with manifest validation, SLA monitoring, and a scheduler overview) exposed through Simple Mode (clean) and Developer Mode (full observability).

---

## Technical Skills Demonstrated

- **Backend:** Python, FastAPI, Pydantic, Uvicorn, REST API design, JSON-based persistence, service-oriented architecture
- **Frontend:** React, Vite, JavaScript, CSS design tokens, accessibility, responsive UI
- **AI / LLM:** Multi-agent orchestration, LLM provider integration, prompt versioning, consensus/judging, evaluation and benchmarking, transcription, document analysis
- **Safety / Governance:** Prompt-injection defense, secret scanning, permission models, approval workflows, audit logging
- **Tooling / Workflow:** Pytest, Git branch-per-issue, Linear/Codex automation, Slack/Notion integrations
- **Engineering practices:** Test-backed development (222 passing backend tests), additive/non-breaking feature layering, incremental release management

---

## Interview-Friendly Achievement Summary

I designed and built EvolveAgent AI, a local-first multi-agent AI operating system that turns a single chatbot call into an inspectable, governed pipeline. A Master Orchestrator Agent routes each request through specialist agents, a governance layer, workspace memory, and an evaluation engine, then returns one scored answer. The project spans a FastAPI backend with 222 passing tests, a React frontend with Simple and Developer modes, real LLM integrations with mock fallback, file/recording intelligence, Mission Control goal planning, a governed automation layer, an AI Evaluation Lab, and an EvolveAgent OS platform-readiness layer — all delivered incrementally as additive, non-breaking releases through v15.0.
