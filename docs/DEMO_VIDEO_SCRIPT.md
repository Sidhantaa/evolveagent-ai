# EvolveAgent AI — Demo Video Script (5–7 minutes)

A scene-by-scene script with exact narration and suggested demo prompts. Target length: 5–7 minutes. Run the backend at `http://127.0.0.1:8000` and the frontend at `http://127.0.0.1:5173` before recording.

---

## 1. Opening (≈20 seconds)

**On screen:** EvolveAgent AI home / Simple Mode command center.

**Narration:**
> "This is EvolveAgent AI — a local-first, workspace-aware multi-agent AI operating system. Instead of one opaque chatbot call, it routes every request through a Master Orchestrator Agent, specialist agents, a governance layer, workspace memory, and an evaluation engine. It runs entirely on your machine with JSON-based storage, and it works with or without API keys thanks to mock fallback."

---

## 2. Architecture Overview (≈45 seconds)

**On screen:** `docs/ARCHITECTURE.md` high-level diagram, or the README architecture diagram.

**Narration:**
> "Here's the architecture. A request — text, a file, a recording, a Linear task, or workspace input — goes to the Master Orchestrator Agent. It detects the task type and coordinates specialist agents: research, logic, risk, strategy, and writing. Everything passes through a governance and permission layer. A Judge Agent and the Evaluation Lab score the result. Workspace memory, analytics, and an adaptive learning engine close the loop. Simple Mode shows just the answer; Developer Mode exposes every layer."

---

## 3. Chat + Developer Mode Demo (≈60 seconds)

**On screen:** Simple Mode, then toggle Developer Mode.

**Demo prompt:**
```text
Explain how EvolveAgent AI works.
```

**Narration:**
> "In Simple Mode the experience is clean — one answer, feedback buttons, and a Jarvis-style command center. Now I'll switch to Developer Mode and run the same prompt. Here you can see the detected task type and confidence, the agents that were used, provider and model metadata, the full workflow trace, the judge score, and per-agent evaluation. This transparency is the core idea: every decision the system makes is inspectable."

---

## 4. File / Recording Workflow (≈60 seconds)

**On screen:** Upload a document, then optionally a recording.

**Demo prompts:**
```text
Summarize this uploaded document.
```
```text
Summarize this recording and list action items.
```

**Narration:**
> "EvolveAgent AI also understands files and recordings. I'll upload a document — the backend validates the file, extracts the text, caps the context, and routes it through the File Analysis Agent. For recordings, it transcribes with mock or OpenAI Whisper mode, then the Recording Analysis Agent produces a summary, key points, action items, and decisions. Same orchestration pipeline, different input type."

---

## 5. Mission Control + Custom Agents (≈90 seconds)

**On screen:** Mission Control panel, then Custom Agent Builder / Skill Store.

**Demo prompt:**
```text
Build an AI resume analyzer app.
```

**Narration:**
> "For bigger objectives, Mission Control turns a goal into a plan. I'll ask it to build an AI resume analyzer app. The Goal Planner Agent generates phases, a task graph, dependencies, risk level, and the next best task. Each task card can be run through the same workflow, and progress is tracked. Goal mode never silently executes code — anything that becomes automation goes through approval."
>
> "EvolveAgent AI also has a Custom Agent Builder and an Agent Skill Store. I can create a reusable specialist from a template — Resume, Code Review, Meeting Notes, Bug Fix, and more. Custom agents run under the same governance and permission rules as built-in agents; they can't bypass the firewall, secret scanner, or approval gates."

---

## 6. Governance + Safe Automation (≈60 seconds)

**On screen:** Developer Mode — Approval Queue, Tool Trace, governance events.

**Demo prompt:**
```text
Add a small settings page to this app.
```

**Narration:**
> "Safety is built into the architecture. When I ask it to change the app, it plans the work and asks for approval before any apply step. Every request passes a prompt-injection firewall and a secret scanner. Tools have permission levels — read-only runs immediately, but edit and run actions require human approval. Here's the Approval Queue and the governance audit log. There's no unrestricted shell — only an allowlist of build and test commands. Nothing destructive, nothing silent."

---

## 7. Linear / Codex Workflow (≈45 seconds)

**On screen:** Linear board (external) + `docs/linear-handoffs/` + backend Linear/Codex endpoints.

**Narration:**
> "EvolveAgent AI also connects to a real development workflow. When a Linear issue is moved to In Progress, the backend can create a branch, write a handoff file, and trigger a guarded Codex worker job. That job runs the test suite and frontend build, then posts a success or failure comment back to Linear. Keys stay server-side, and full autonomous mode is off by default — verification gates every completion."

---

## 8. Evaluation / Project / Portfolio Dashboard (≈60 seconds)

**On screen:** Analytics panel, AI Evaluation Lab, AI Project Manager, Portfolio Mode, EvolveAgent OS panel.

**Narration:**
> "Finally, the measurement layer. The Analytics dashboard tracks runs, scores, latency, and fallback usage. The AI Evaluation Lab runs benchmarks, A/B tests, and regression checks on the agents themselves. The AI Project Manager surfaces risks and status reports, and Portfolio Mode rolls multiple workspaces into one health view. The EvolveAgent OS panel shows installer readiness, the plugin SDK, an SLA rating, and scheduler health — the platform-readiness layer that ties it all together."

---

## 9. Closing (≈20 seconds)

**On screen:** Back to Simple Mode.

**Narration:**
> "That's EvolveAgent AI. It's different from a normal chatbot because it separates routing, context, tools, analysis, risk, judging, memory, approvals, analytics, and learning into inspectable, governed layers. It self-optimizes its orchestration — not the base model — and keeps every risky action behind human approval. Local-first, transparent, and safe by design."

---

## Suggested Demo Prompt Order

1. `Explain how EvolveAgent AI works.`
2. `Search my project knowledge for app automation decisions.`
3. `Summarize this uploaded document.` (with a file attached)
4. `Summarize this recording and list action items.` (with a recording attached)
5. `Build an AI resume analyzer app.`
6. Create a custom `Resume Agent` from the template list.
7. `Add a small settings page to this app.`
8. Open Developer Mode: Approval Queue, Tool Trace, Agent Jobs, EvolveAgent OS panel.

## Recording Tips

- Keep Simple Mode and Developer Mode toggles visible to emphasize the contrast.
- Use mock mode (`LLM_MODE=mock`, `IMAGE_MODE=mock`, `TRANSCRIPTION_MODE=mock`) for a cost-free, reliable recording.
- Pre-load one demo document and one demo recording so uploads are instant.
