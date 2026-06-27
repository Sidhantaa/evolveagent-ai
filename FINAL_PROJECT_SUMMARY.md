# EvolveAgent AI — Project Summary (current: EvolveAgent OS v15.0)

## Final Platform Positioning

EvolveAgent OS is a local-first, workspace-aware multi-agent AI platform with governed automation, plugins, analytics, evaluation, and portfolio management.

The v15.0 EvolveAgent OS checkpoint is a final platform-readiness layer added additively on top of the existing system:

- **Unified installer readiness** (`GET /api/os/installer`) — backend/frontend setup steps, required + optional env vars, verification commands, detected readiness, and missing-config warnings. Read-only; it never installs or runs anything.
- **Plugin SDK** (`GET /api/os/plugin-sdk`, `POST /api/os/plugin-sdk/validate`) — declarative plugin manifest schema, permission levels (`read_only`, `plan_only`, `approve_to_edit`, `approve_to_run`, `blocked`), allowed tool types, safety rules, example manifest, and a manifest validator. No remote plugin loading or plugin code execution.
- **SLA monitoring** (`GET /api/os/sla`) — uptime proxy score, latency, success/fallback rate, blocked actions, failed quality/codex jobs, recent incidents, rating, and recommendations from local data only.
- **OS scheduler overview** (`GET /api/os/scheduler`) — aggregated queue/approval/automation health on top of the existing `AgentSchedulerService` (not a replacement).
- **EvolveAgent OS launch panel** (`GET /api/os/summary`) — combined installer readiness, plugin SDK summary, SLA rating, scheduler health, and safety notes, surfaced in a Developer Mode panel. Simple Mode stays clean.

EvolveAgent OS is local-first and governed: not fully autonomous without approval, not a self-training base model, not a production hosted SaaS, and with no unrestricted shell access.

## Short Summary

EvolveAgent AI is a workspace-aware, voice-capable multi-agent AI operating workspace. It combines a polished Jarvis-style interface with Master Agent routing, specialist agents, real OpenAI mode with mock fallback, file and recording analysis, mock image previews, Mission Control goals, custom agents, Project Brain search, safe tool routing, approval workflows, analytics, adaptive learning, and Developer Mode transparency.

## Full Technical Summary

The project uses a FastAPI backend and Vite React frontend. The backend receives user requests, resolves workspace context, loads relevant memory, classifies the task, routes work through the correct agent workflow, evaluates the result, logs governance and analytics metadata, stores memory, and returns a structured response. The frontend has Simple Mode for normal use and Developer Mode for technical inspection.

The v3.5 checkpoint adds professional UI/UX polish on top of the v3.0 Agent OS foundation:

- Jarvis-style Simple Mode command center
- Responsive Developer Mode sidebar
- Light/dark theme toggle with CSS design tokens
- Theme-consistent panels, composer, markdown/code blocks, cards, and controls
- First-run onboarding walkthrough
- Improved ARIA labels and focus states
- Reduced-motion handling

The v3.0 checkpoint added the first Agent OS foundation on top of the existing v2.x system:

- Project Brain / Knowledge Base search and export
- Cross-session knowledge links
- Memory importance ranking and pinning
- Assistant Tools
- Tool Registry and Tool Router
- Plugin manifest loading
- Developer Mode Tool Trace
- Approval Workflow 2.0
- Approval Queue and Audit UI
- Agent Jobs scheduler and lifecycle controls
- System Prompt Registry
- Kernel Service wrapper around request orchestration
- Jarvis-style Simple Mode foundation

## Key Features

- ChatGPT-style chat UI
- Browser voice input
- Simple Mode and Developer Mode
- Master Orchestrator Agent
- Specialist agents for research, logic, risk, strategy, writing, judging, evolution, memory, files, recordings, images, and planning
- Real OpenAI text mode with mock fallback
- Deep Mode multi-LLM consensus metadata
- File upload and document analysis
- Recording upload and recording analysis
- Mock Image Agent with safe prompt rewriting
- Mission Control goal planning and task graphs
- Custom Agent Builder and Agent Skill Store
- Workspace memory and workspace-scoped analytics
- Project Brain search/export
- Cross-session knowledge links
- Memory importance ranking
- Assistant Tools and Tool Router
- Local plugin manifests
- Approval chains, queue, audit, and rejection records
- Safe file editor and allowlisted command runner
- Governance logging, prompt-injection checks, secret scanning, and permissions
- Adaptive Learning Engine
- Human feedback and analytics dashboard
- Agent Jobs scheduler
- System Prompt Registry
- Kernel Service wrapper
- Professional v3.5 UI polish with Jarvis-style command center, theme tokens, onboarding, accessibility improvements, and responsive layout

## What Problem It Solves

Normal chatbots produce one opaque answer. EvolveAgent AI separates routing, context, tools, file/recording analysis, risk checks, writing, judging, feedback, memory, approvals, analytics, and learning into inspectable layers. This makes the system easier to demo, debug, govern, and improve.

## What Makes It Different

- It uses a Master Agent instead of one direct chatbot call.
- It routes tasks through specialist workflows.
- It uses project/workspace memory.
- It can inspect files and recordings.
- It can create goal/task graphs.
- It supports reusable custom agents.
- It can select governed tools and show a tool trace.
- It requires approval for risky actions.
- It tracks quality with judge and per-agent evaluation.
- It has Developer Mode for transparency.
- It uses mock fallback so demos still work without API keys.

## Safety Boundaries

- File edits require approval.
- Commands are allowlisted.
- Destructive file deletion is blocked.
- Unrestricted shell execution is blocked.
- Package installation is blocked.
- `.env`, `.git`, `node_modules/`, `venv/`, uploads, and local runtime data are protected.
- Prompt changes are versioned and reversible.
- Custom agents cannot bypass governance.
- The app does not train or fine-tune the base LLM.
- The app does not silently self-modify.

Correct learning description:

> The system self-optimizes the orchestration layer through prompt versioning, workflow strategy memory, model performance tracking, and user feedback.

## Current Limitations

- No authentication
- No cloud database
- No vector search
- No OCR for scanned PDFs
- No real image-generation API
- No speaker diarization
- No full video frame understanding
- No deployment setup
- JSON storage is for MVP/demo use
- Agent Jobs are local persisted jobs, not distributed workers

## Future Roadmap

- Manual UI QA for v3.5 across Simple Mode, Developer Mode, light/dark theme, onboarding, and responsive layout
- Better responsive layout and accessibility
- Light/dark theme tokens
- Onboarding walkthrough
- Server-Sent Events streaming
- Richer approval diff previews
- Vector memory and retrieval
- Real image generation
- OCR/scanned PDF support
- User accounts and team workspaces
- Deployment

## Resume Bullets

- Built EvolveAgent AI, a full-stack multi-agent AI operating workspace using FastAPI, React, and OpenAI with Master Agent routing, specialist workflows, and Developer Mode transparency.
- Implemented real OpenAI mode with mock fallback and Deep Mode consensus metadata so the app remains demoable with or without API keys.
- Added file upload, document analysis, recording analysis, mock image prompts, browser voice input, Mission Control goal planning, and governed custom agents.
- Built Project Brain search across workspace memory, chats, files, recordings, goals, and custom agents with knowledge export, cross-session links, and memory importance ranking.
- Implemented a governed Tool Router with Assistant Tools, plugin manifests, permission levels, and Developer Mode tool tracing.
- Added Approval Workflow 2.0 with approval chains, queue endpoints, audit records, rejection handling, optional webhook notification, and governance logging.
- Built an Agent OS foundation with persisted Agent Jobs, lifecycle controls, health monitoring, System Prompt Registry, and a Kernel Service wrapper around request orchestration.
- Designed safety controls including prompt-injection checks, secret scanning, protected paths, allowlisted commands, approval-gated automation, and no unrestricted shell execution.

## Interview Explanation

EvolveAgent AI is a full-stack AI operating workspace I built to explore safe multi-agent orchestration. The system uses a Master Orchestrator Agent to classify requests, retrieve workspace memory, select tools or specialist agents, evaluate output quality, and store feedback and analytics. It supports text, files, recordings, image prompts, voice input, goal planning, custom agents, and approval-gated automation. Developer Mode exposes the workflow trace, provider metadata, consensus candidates, tool trace, approvals, agent jobs, system prompts, and raw JSON. The v3.5 checkpoint adds professional UI polish over the Agent OS foundation while keeping risky actions behind human approval and governance controls.
