# EvolveAgent AI

## Current Status
- Main branch: v150 frontend merged
- Latest PR: #202
- CI: backend + frontend passing
- Mode: local-first, governance-first, approval-gated

## Core Flow
Goal -> Plan -> Agents -> Tools -> Approval -> Execution -> Verification -> Memory -> Improvement

## Project Areas
- Workspace Brain
- Mission Control
- Durable Workflows
- Code Changes
- GitHub Connector
- Governance
- Memory v2
- Agent Registry
- MCP Hub
- Portfolio / Roadmap

## Key Docs
- [[../CODEX_HANDOFF]]
- [[../CODEX_ASSIGNMENT_v100]]
- [[../CODEX_ASSIGNMENT_v150_frontend]]
- [[../ARCHITECTURE]]
- [[../architecture/Project-Architecture]]
- [[../architecture/Route-Page-Coverage-Audit]]
- [[../PORTFOLIO_PACK]]
- [[../RESUME_BULLETS]]
- [[../CASE_STUDY]]
- [[../INTERVIEW_EXPLANATION]]

## Roadmap Notes
- [[../roadmap/README]]
- [[../roadmap/EvolveAgent-v200-Strategy]]
- [[../architecture/README]]
- [[../handoffs/README]]
- [[../decisions/README]]
- [[../release-notes/README]]

## Manual Checks
- Start backend: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000`
- Start frontend: `cd frontend && npm run dev`
- Open app: `http://127.0.0.1:5173`
