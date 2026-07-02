# EvolveAgent AI — Demo Data Checklist

A checklist of sample records that make a demo or screenshot session look complete. **This repo has no automated demo-data generator** — create these live in the running app (mock mode is fine). Do **not** commit runtime JSON (`backend/app/data/*.json` is git-ignored), and never use real secrets or private data.

> Note: all data lives locally as JSON via `StorageService`. Creating the records below through the UI or API is enough — nothing needs to be seeded from a script.

## Checklist

- [ ] **One workspace** — the app auto-creates a default workspace; optionally add a second named one.
- [ ] **One memory item** — add a workspace memory entry (Memory / Project Brain panel).
- [ ] **One project** — create a project in the Project Manager panel.
- [ ] **One portfolio record** — ensure the project appears in Portfolio Mode.
- [ ] **One governance event** — run any prompt or stateful action; it logs automatically (view in the governance panel).
- [ ] **One MCP connector** — MCP Hub → add a connector from a template (e.g. GitHub).
- [ ] **One executive board decision** — Executive Board panel → create a session and generate a review.
- [ ] **One simulation scenario** — Simulation World panel → create a world + scenario and run it.
- [ ] **One innovation idea** — Innovation Lab panel → add a scored idea.
- [ ] **One operating layer readiness snapshot** — Operating Layer panel → generate a readiness snapshot.

## Optional (for a fuller MCP demo)

- [ ] **One MCP execution request** — MCP Hub → request execution on the connector (mock).
- [ ] **One approvals-inbox item** — a pending approval will appear in the Approvals Inbox for a write action.

## Capture tips

- Keep mock mode on (`LLM_MODE=mock`, `IMAGE_MODE=mock`, `TRANSCRIPTION_MODE=mock`).
- Use a consistent browser width across screenshots.
- Hide secrets — no API keys, no `.env`, no private/personal content.
- See `screenshots/README.md` for the prioritized shot list and file names.

## If a safe generator is added later

If a demo-data generator is added under `scripts/` in the future, document its usage here (e.g. `python scripts/seed_demo_data.py`). Until then, create records live as above — no runtime JSON should be committed.
