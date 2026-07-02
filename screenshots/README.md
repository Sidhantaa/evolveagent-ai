# Screenshots

This folder holds final screenshots for submission, GitHub, and portfolio use. Actual image files are optional — this guide is the recommended capture checklist. **Only the guide is committed unless real screenshots already exist. Do not create fake screenshots.**

## Prioritized Portfolio Pack (v44.5) — capture these 12 first

Capture in this order; these tell the story fastest for a portfolio or demo.

| # | Screen | File name | How to reach it |
|---|--------|-----------|-----------------|
| 1 | Chat home / Simple Mode | `01-simple-mode.png` | Open the app (Simple Mode); prompt `Explain how EvolveAgent AI works.` |
| 2 | Developer Mode workflow trace | `02-developer-mode.png` | Toggle Developer Mode; run the same prompt; show the workflow trace |
| 3 | Governance panel | `03-governance.png` | Developer Mode → governance / approval audit |
| 4 | Memory Intelligence panel | `04-memory.png` | Open the Memory / Project Brain panel |
| 5 | Project Manager | `05-project-manager.png` | Open the Project Manager panel |
| 6 | Portfolio Mode | `06-portfolio-mode.png` | Open the Portfolio panel |
| 7 | Operating Layer (v40) | `07-operating-layer.png` | Developer Mode → EvolveAgent Operating Layer panel |
| 8 | MCP Hub (v41) | `08-mcp-hub.png` | Developer Mode → MCP Hub panel (connectors + executions + inbox) |
| 9 | Master tuning / approvals | `09-master-tuning.png` | Developer Mode → Approvals / MCP Approvals Inbox (v44) |
| 10 | Executive Board (v35) | `10-executive-board.png` | Developer Mode → Executive Board panel |
| 11 | Simulation World (v37) | `11-simulation-world.png` | Developer Mode → Simulation World panel |
| 12 | Innovation Lab (v36) | `12-innovation-lab.png` | Developer Mode → Innovation Lab panel |

### Capture instructions

- **Run the backend** (`cd backend && ./venv/bin/uvicorn app.main:app --port 8000`).
- **Run the frontend** (`cd frontend && npm run dev -- --host 127.0.0.1 --port 5173`).
- Open the app locally at `http://127.0.0.1:5173`.
- **Seed or use demo data** if available — see `docs/DEMO_DATA_CHECKLIST.md` (otherwise create a couple of records live during capture).
- Use a **consistent browser width** across all shots.
- **Hide secrets** — no API keys, no `.env`, no private/personal data.
- Keep mock mode on (`LLM_MODE=mock`, `IMAGE_MODE=mock`, `TRANSCRIPTION_MODE=mock`) for clean, cost-free captures.

The detailed 20-shot checklist below remains available for a fuller set.

---


## How to Capture

1. **Run the backend:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload --port 8000
   ```
2. **Run the frontend:**
   ```bash
   cd frontend
   npm run dev -- --host 127.0.0.1 --port 5173
   ```
3. Open `http://127.0.0.1:5173`.
4. Use the demo prompts below to reach each screen.
5. Capture each screen and save it with the consistent name shown.
6. Keep mock mode on (`LLM_MODE=mock`, `IMAGE_MODE=mock`, `TRANSCRIPTION_MODE=mock`) for clean, cost-free captures.

## Screenshot Checklist

| # | Screen | Suggested file name | How to reach it |
|---|--------|---------------------|-----------------|
| 1 | Home / chat screen | `01-chat-home.png` | Open the app in Simple Mode |
| 2 | Simple Mode answer | `02-simple-mode.png` | Prompt: `Explain how EvolveAgent AI works.` |
| 3 | Developer Mode workflow trace | `03-developer-mode.png` | Toggle Developer Mode, run the same prompt |
| 4 | File upload / document analysis | `04-file-analysis.png` | Upload a doc, prompt: `Summarize this uploaded document.` |
| 5 | Recording intelligence | `05-recording-intelligence.png` | Upload audio, prompt: `Summarize this recording and list action items.` |
| 6 | Image Agent | `06-image-agent.png` | Prompt: `Generate an image prompt for a futuristic AI assistant.` |
| 7 | Workspace memory | `07-workspace-memory.png` | Open the Memory / Project Brain panel |
| 8 | Mission Control | `08-mission-control.png` | Prompt: `Build an AI resume analyzer app.` |
| 9 | Custom Agent Builder | `09-custom-agent-builder.png` | Open Agent Builder / Skill Store, create from a template |
| 10 | Agent Skill Store | `10-skill-store.png` | Show the template list (Resume, Code Review, Bug Fix, …) |
| 11 | Security / governance panel | `11-governance.png` | Developer Mode → governance / approval audit |
| 12 | Linear workflow panel | `12-linear-workflow.png` | Linear board + `docs/linear-handoffs/` (workflow is server-side) |
| 13 | Slack / Notion integration view | `13-integrations.png` | Show integration status if present |
| 14 | AI Evaluation Lab | `14-evaluation-lab.png` | Open the Evaluation Lab panel |
| 15 | AI Project Manager dashboard | `15-project-manager.png` | Open the Project Manager panel |
| 16 | Portfolio Mode | `16-portfolio-mode.png` | Open the Portfolio panel |
| 17 | EvolveAgent OS platform readiness | `17-platform-readiness.png` | Developer Mode → EvolveAgent OS panel |
| 18 | Analytics dashboard | `18-analytics.png` | Open the Analytics panel |
| 19 | Learning report | `19-learning-report.png` | Open the Learning panel |
| 20 | Final project health dashboard | `20-project-health.png` | Portfolio / health overview |

### Short Name Variant

If you prefer the shorter naming scheme, these map to the most demo-critical screens:

```
01-chat-home.png
02-simple-mode.png
03-developer-mode.png
04-file-analysis.png
05-recording-intelligence.png
06-mission-control.png
07-custom-agent-builder.png
08-governance.png
09-linear-workflow.png
10-evaluation-lab.png
11-project-manager.png
12-portfolio-mode.png
13-platform-readiness.png
```

## Demo Prompt Reference

- `Explain how EvolveAgent AI works.`
- `Search my project knowledge for app automation decisions.`
- `Summarize this uploaded document.`
- `Summarize this recording and list action items.`
- `Generate an image prompt for a futuristic AI assistant.`
- `Build an AI resume analyzer app.`
- `Add a small settings page to this app.`

## Safety Checklist

- Do not include API keys.
- Do not include private uploaded documents.
- Do not include personal data.
- Do not show `.env`.
- Use demo files or synthetic content only.
