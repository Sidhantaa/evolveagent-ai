# EvolveAgent AI MVP v2.6 — Workspace Memory + Personal AI Context Summary

## Short Summary

EvolveAgent AI is a workspace-aware, voice-controlled, ChatGPT-style multi-agent AI workspace with project memory, Mission Control, Custom Agent Builder, real multi-LLM consensus, governance, and an Advanced Adaptive Learning Engine. It routes user requests through a Master Orchestrator Agent, specialist agents, a Judge Agent, an Evolution Agent, workspace memory, feedback, analytics, safe automation planning, recording analysis, goal/task planning, reusable custom agents, and learning reports that optimize the orchestration layer.

## Full Technical Summary

EvolveAgent AI is built with a FastAPI backend and Vite React frontend. The backend receives chat requests, creates or loads chat sessions, classifies task type, runs the correct workflow, evaluates results, saves memory and analytics, and returns a structured response. The frontend presents Simple Mode for clean user-facing answers and Developer Mode for workflow inspection.

MVP v2.6 supports real OpenAI text mode, optional Deep Mode consensus across configured OpenAI, Claude, Gemini, and Mistral providers, mock fallback, JSON-based chat/session storage, file upload and document analysis, recording upload and transcript summaries, mock image preview generation, per-agent evaluation, human feedback, analytics, browser voice command input, Mission Control goal/task graphs, Custom Agent Builder templates, approval-gated app automation planning, safe project scanning, allowlisted test/build command execution, prompt versioning, task-specific learning insights, workflow strategy memory, model routing suggestions, user preference learning, workspace switching, workspace-scoped records, and searchable/editable project memory.

## Key Features

- Master Orchestrator Agent
- Specialist text agents
- Judge Agent scoring
- Per-agent usefulness and clarity evaluation
- Evolution Agent recommendations
- JSON memory and workflow storage
- Chat sessions and message history
- File upload and document analysis
- Recording upload and transcript analysis
- Recording Analysis Agent
- Mock Image Agent with safe prompt rewriting
- Browser voice command input
- `app_automation` task routing
- Project Scanner Agent
- Implementation Planner Agent
- Approval workflow before automation apply
- Safe file editor path validation
- Safe command runner allowlist
- Adaptive Learning Agent
- Advanced learning report with strongest/weakest agents by task type
- Workflow strategy memory with feedback and fallback rates
- Model routing suggestions by task category
- User preference learning
- Prompt versioning with approve/reject/rollback
- Human feedback buttons
- Analytics dashboard
- Simple Mode and Developer Mode
- Real OpenAI text mode with mock fallback
- Real multi-LLM consensus in Deep Mode
- Consensus winner and model tournament tracking
- Mission Control goal planning and task graph storage
- Goal Planner Agent with phases, dependencies, priorities, risk, and next-best-task recommendations
- Goal/task APIs and Mission Control UI
- Custom Agent Builder with governed reusable specialist agents
- Prebuilt Agent Skill Store templates
- Goal/custom-agent analytics and learning insights
- Workspace switcher with automatic default workspace fallback
- Workspace-scoped chats, files, recordings, goals, task graphs, custom agents, feedback, analytics, learning, and governance metadata
- Workspace memory timeline with add, search, filter, edit, and delete controls
- Relevant workspace memory retrieval before agent runs with capped context
- Workspace-filtered analytics and learning reports
- Linear issue sync into Mission Control with governed git commit workflow and In Progress poll detection

## Architecture Overview

The user sends text, files, voice-transcribed input, image prompts, or app automation requests through the React chat UI. FastAPI receives the request and sends it to the Master Orchestrator Agent. The Master Agent detects the task type and routes the request to the correct workflow:

- Workspace context is resolved first. If no workspace is provided, the default workspace is used.
- Relevant workspace memory is retrieved and capped before being added to agent context.
- Text tasks use Research, Logic, Risk, Strategy, Writing, Judge, Evolution, and Memory agents.
- File tasks run File Analysis before the normal specialist workflow.
- Image tasks use the mock Image Agent with safe prompt rewriting.
- App automation tasks run Project Scanner and Implementation Planner, then ask for approval.
- Recording summary tasks use uploaded recording transcripts and the Recording Analysis Agent.

Results, feedback, workflow traces, workspace memories, analytics, prompt versions, model performance data, and learning reports are stored locally in JSON.

## What Problem It Solves

Normal chatbots often produce one opaque answer. EvolveAgent AI separates routing, reasoning, risk analysis, writing, judging, feedback, memory, analytics, automation planning, and learning into inspectable workflow layers. This makes the system easier to evaluate, explain, and improve.

## What Makes It Different From a Normal Chatbot

- It uses a Master Agent to route tasks.
- It uses specialist agents instead of one generic answer.
- It evaluates each agent individually.
- It stores workflow analytics and human feedback.
- It organizes context by workspace instead of keeping every project in one global memory.
- It retrieves relevant project memory before a run while keeping Simple Mode clean.
- It supports file-aware workflows.
- It supports recording/audio summary workflows.
- It supports voice-to-chat input.
- It can prepare safe app automation plans.
- It can compare multiple model candidates in Deep Mode and synthesize one final answer.
- It can turn a large goal into a trackable task graph.
- It can run individual goal tasks through the existing agent workflow.
- It lets users create reusable governed custom agents from templates.
- It requires approval before automation apply.
- It has Simple Mode for users and Developer Mode for technical review.
- It has mock fallback so it remains demoable without paid API access.
- It optimizes the orchestration layer without claiming the base model trains itself.

## Safety Boundaries

- File edits require explicit user approval.
- Command execution is allowlisted.
- Allowed commands are `npm run build`, `npm test`, `npm run lint`, `pytest`, and `python -m pytest`.
- Destructive file deletion is not supported.
- Unrestricted shell execution is not supported.
- Package installation is not supported through automation.
- `.env`, `.git`, `node_modules/`, `venv/`, uploads, and local data/analytics files are blocked from editing.
- The app does not silently self-modify.
- Prompt changes are versioned, require approval, and can be rolled back.
- The base LLM is not fine-tuned or retrained by the app.

Correct learning description:

> The system self-optimizes the orchestration layer through prompt versioning, workflow strategy memory, model performance tracking, and user feedback.

## Current Limitations

- No authentication
- No cloud database
- No vector memory
- No OCR or scanned PDF support
- No real image-generation API
- No speaker diarization yet
- No full video frame understanding yet
- No deployment setup
- No unrestricted code editing
- No autonomous file deletion
- JSON storage is for MVP/demo use, not production scale
- Workspace memory is keyword/importance based, not vector search

## Future Roadmap

- Server-Sent Events streaming
- Longer recording processing and richer transcript metadata
- Speaker diarization
- More advanced model routing and cost tracking
- Real image API
- OCR/scanned PDF support
- Vector search and retrieval
- Patch preview with second approval
- User accounts and team workspace sharing
- Cloud database
- Deployment
- Agent performance trends over time

## Demo Prompts

- `Add dark mode to this app`
- `Run tests for this project`
- `Explain the current app architecture`
- `Summarize this uploaded document`
- `Summarize this recording and list action items`
- `Turn this lecture recording into study notes`
- `Generate an image prompt for a futuristic AI assistant`
- `Create a workspace for Resume Projects and remember that I prefer concise bullet points`
- `Explain how EvolveAgent AI works`
- `Review my FastAPI backend architecture`
- `Build an AI resume analyzer app`
- `Create a full implementation plan for a SaaS app`
- `Break this goal into tasks`

## Resume Bullets

- Built EvolveAgent AI, a full-stack voice-controlled multi-agent AI workspace using FastAPI, React, and OpenAI with a Master Orchestrator Agent for task routing.
- Designed specialist agents for research, logic analysis, risk detection, strategy planning, writing, judging, evolution feedback, memory, file analysis, image prompt generation, and automation planning.
- Implemented real OpenAI text mode and optional multi-LLM consensus across configured providers, with mock fallback to keep workflows stable when API keys are missing or provider calls fail.
- Added browser voice command input, chat sessions, message history, markdown rendering, export controls, and JSON-based local memory.
- Built file upload and document analysis for PDFs, resumes, CSVs, code files, markdown, JSON, and text documents.
- Added recording upload and mock/OpenAI transcription support for MP3, M4A, WAV, MP4, and WEBM recordings with transcript summaries, action items, decisions, study notes, and Q&A.
- Implemented approval-gated app automation planning with safe project scanning, path validation, and allowlisted build/test command execution.
- Created an Advanced Adaptive Learning Engine that tracks judge scores, per-agent scores, feedback, model performance, workflow strategy, prompt versions, and inferred user preferences.
- Built Simple Mode for clean user-facing responses and Developer Mode for inspecting workflow trace, provider metadata, automation plans, learning reports, judge scores, per-agent scores, file context, image metadata, and raw JSON.
- Added Mission Control for goal planning, task graph creation, task progress tracking, runnable subtasks, and goal analytics.
- Built a Custom Agent Builder with governed reusable agents and prebuilt templates for resume review, code review, meetings, files, pharmacy PA, business analysis, bug fixing, and study notes.
- Added workspace-scoped project memory with a memory timeline, relevant memory retrieval, default workspace fallback, workspace-filtered chats/goals/agents, and workspace-specific analytics/learning reports.

## Interview Explanation

EvolveAgent AI is a full-stack project I built to demonstrate a workspace-aware, voice-controlled multi-agent AI operating workflow. Instead of sending every prompt to one chatbot, the system uses a Master Orchestrator Agent to classify the task, retrieve relevant workspace memory, and route the request through the right workflow. Text tasks go through research, logic, risk, strategy, writing, judging, evolution, and memory agents. In Deep Mode, it can compare candidates from configured OpenAI, Claude, Gemini, Mistral, and mock providers, then synthesize one final answer. File tasks use a File Analysis Agent before the normal workflow. Recording tasks use a Transcription Service and Recording Analysis Agent. Image tasks use a mock Image Agent with safe prompt rewriting. App automation tasks scan the project and create an implementation plan, but require approval before any apply step. MVP v2.6 adds workspaces and project memory so chats, files, recordings, goals, custom agents, analytics, learning, and relevant memories can be scoped by project. Simple Mode keeps the UI clean, while Developer Mode shows workspace memory usage, consensus candidates, selected winner, model metadata, goals, custom agents, and the full agent workflow for technical review.
