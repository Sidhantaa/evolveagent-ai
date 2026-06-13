# EvolveAgent AI Demo Guide

Use this guide for a 2-minute portfolio, class, or interview demo of **EvolveAgent AI MVP v2.6**.

## 2-Minute Demo Script

**0:00-0:15 — Introduce the project**

EvolveAgent AI is a workspace-aware, voice-capable multi-agent AI workspace with project memory, real multi-LLM consensus, and an advanced adaptive learning layer. Instead of sending every request directly to one chatbot, it uses a Master Orchestrator Agent to classify the task, retrieve relevant workspace memory, route it through specialist agents, compare Deep Mode candidates when requested, evaluate the output, store memory and analytics, and return one clean final answer.

**0:15-0:35 — Show Simple Mode**

Run:

```text
Explain how EvolveAgent AI works.
```

Show that Simple Mode feels like a normal AI assistant: user message, assistant answer, feedback buttons, and minimal controls.

**0:35-0:55 — Show Developer Mode**

Click **View details** or switch to **Developer Mode**. Show:

- task type
- confidence
- agents used
- provider/model metadata
- workflow trace
- judge score
- per-agent evaluation
- evolution notes
- consensus candidates and selected winner when Deep Mode is enabled

Explain that Developer Mode proves the orchestration behind the clean chat UI.

**Workspace moment — Show project context**

In the left sidebar, create or select a workspace. Open the Memory panel, add a short project fact, then ask a related prompt. In Developer Mode, show that workspace memory was used as scoped context. Explain that v2.6 separates chats, goals, agents, files, recordings, analytics, learning, and memory by project.

**0:55-1:15 — Show file upload**

Upload a resume, README, CSV, or code file and ask:

```text
Review this file and give improvements.
```

Explain that the backend validates the file, saves it locally, extracts text, caps the context, runs the File Analysis Agent, and then routes the prepared context through the specialist agents.

**1:15-1:30 — Show mock Image Agent**

Run:

```text
Generate an image prompt for a futuristic AI assistant.
```

Explain that MVP v2.6 uses a mock image provider, cleans prompt wording, rewrites protected-character requests safely, and returns a preview without calling a real image API.

**1:30-1:45 — Show recording intelligence**

Upload an MP3, M4A, WAV, MP4, or WEBM recording and ask:

```text
Summarize this recording and list action items.
```

Explain that v2.6 stores the recording, transcribes it in mock or OpenAI mode, runs the Recording Analysis Agent, and returns summaries, action items, decisions, study notes, and Q&A.

**1:45-2:00 — Show safe app automation**

Run:

```text
Add a small settings page to this app.
```

Show that EvolveAgent AI scans the project, creates an implementation plan, lists likely files and commands, and asks for approval before any apply step. Explain that v2.0 does not silently edit files.

**Close — Show learning and analytics**

Click **Helpful** or **Save as good answer**, then open the Analytics panel. Show:

- total runs
- average score
- most common task type
- most used agent
- fallback count
- file/image task counts
- feedback summary

Also show the Developer Mode Learning Report if time permits.

**Close with value**

This project demonstrates a realistic multi-agent architecture with task routing, model fallback, file analysis, recording intelligence, mock image generation, voice input, Mission Control goal/task graphs, custom agent templates, approval-gated automation planning, per-agent evaluation, feedback, analytics, and orchestration-level learning reports.
MVP v2.6 adds workspace-scoped project memory so each project can keep its own chats, files, goals, custom agents, analytics, and learning context.

## What to Show First

Start in **Simple Mode**. Do not begin with raw JSON.

Show:

- clean assistant answer
- feedback buttons
- copy/regenerate/view details controls
- attached file names if using files

Then switch to Developer Mode to show the system depth.

## Best Demo Prompt Order

1. `Explain how EvolveAgent AI works.`
2. Create a workspace named `Resume Projects` and add memory: `This workspace prefers concise bullet points and software engineering internship examples.`
3. `Create a 2-minute project demo script.`
4. Upload a resume or README and ask: `Review this file and give improvements.`
5. `Generate an image prompt for a futuristic AI assistant.`
6. Upload a recording and ask: `Summarize this recording and list action items.`
7. Turn on Deep Mode and ask: `Compare the best plan for improving this project demo.`
8. `Build an AI resume analyzer app.`
9. Open Mission Control and run one task.
10. Create a custom `Resume Agent` from the template list.
11. `Add dark mode to this app.`
12. `Run tests for this project.`
13. `Explain the current app architecture.`
14. Upload a document and ask: `Summarize this uploaded document.`
15. Click feedback buttons and open Analytics.
16. Switch to Developer Mode and show consensus, workspace memory, per-agent evaluation, goals, custom agents, and learning report.

## How to Explain Mission Control

Say:

Mission Control turns large objectives into trackable goals and task graphs. The Goal Planner Agent creates phases, task cards, dependencies, priorities, recommended agents, risk level, and the next best task. The user can run one task at a time through the existing agent workflow. Goal Mode does not silently execute code; any task that becomes app automation still requires approval.

Demo prompt:

```text
Build an AI resume analyzer app.
```

Then open **Mission Control** and show:

- active goal
- progress percent
- phases and task cards
- priority and status badges
- run task button
- mark done button

## How to Explain Custom Agent Builder

Say:

Custom agents are reusable workflow specialists that operate under the same permission, governance, and safety rules as built-in agents. They cannot bypass prompt-injection checks, secret scanning, approval gates, or governance logging.

Show the Agent Builder panel and create a template-based agent, such as:

- Resume Agent
- Code Review Agent
- Meeting Notes Agent
- File Summary Agent
- Business Analyst Agent

## How to Explain the Master Agent

The Master Agent is the supervisor. It receives the user request, loads recent chat context, detects the task type, chooses the correct workflow, tracks execution, and returns a structured response.

It decides whether the request is:

- normal text
- file/document analysis
- image generation
- app automation
- recording summary
- coding
- resume review
- business analysis
- system explanation

## How to Explain Specialist Agents

Specialist agents divide the work:

- Research Agent understands context.
- Logic Agent structures reasoning.
- Risk Agent finds assumptions and weak points.
- Strategy Agent recommends next steps.
- Writing Agent creates the final answer.
- Judge Agent scores quality.
- Evolution Agent recommends workflow improvements.
- File Analysis Agent summarizes uploaded documents.
- Image Agent creates safe image prompts and mock previews.

## How to Explain Real Multi-LLM Consensus

The app can use real OpenAI text mode when `OPENAI_API_KEY` is configured. In Deep Mode, MVP v2.6 asks the LLM Router for configured consensus providers, such as OpenAI, Claude, Gemini, and Mistral. Each provider creates an independent candidate answer, the Judge Agent compares them, and the Writing Agent synthesizes one final answer.

If only OpenAI is configured, Deep Mode compares OpenAI with mock. If no keys are present, or if a provider call fails, candidates fall back to mock mode. This keeps the demo stable and lets the full workflow run without paid API access.

Developer Mode shows each candidate, provider/model metadata, fallback status, selected winner, and judge comparison notes. Simple Mode only shows the final answer.

Image generation intentionally stays on `mock_image` in MVP v2.6.

## How to Explain File Upload

Say:

EvolveAgent AI supports document-aware workflows. Files are uploaded through the chat, validated, saved locally, and converted into extracted text. The File Analysis Agent summarizes that context before the normal specialist agents run.

Limitations:

- text-based PDFs only
- no OCR
- no scanned PDF support
- no vector database yet

## How to Explain Recording Intelligence

Say:

EvolveAgent AI v2.6 supports recording upload for MP3, M4A, WAV, MP4, and WEBM files. The backend validates the recording, stores it locally, transcribes it using mock mode or OpenAI transcription mode, and runs a Recording Analysis Agent. The output includes a short summary, detailed summary, key points, action items, decisions, follow-up tasks, study notes, and Q&A.

Limitations:

- no speaker diarization yet
- no video frame understanding yet
- mock transcription is used by default for demos and tests

## How to Explain the Mock Image Agent

Say:

The Image Agent detects visual requests, cleans the prompt, rewrites protected-character wording into safer inspired-character descriptions, and returns a mock preview. This demonstrates the image workflow without adding real image API cost or complexity.

## How to Explain Voice Input

Say:

EvolveAgent AI v2.0 adds browser voice command input. The microphone button uses the browser Web Speech API to transcribe short commands into the chat box. The user can edit the transcription before sending, so voice remains safe and controlled.

## How to Explain App Automation

Say:

For app automation requests, EvolveAgent AI behaves like a safe Codex-style planner. It scans the project, detects frameworks, identifies likely files and build/test commands, and prepares an implementation plan. It asks for approval before any apply step and blocks dangerous paths, secrets, package installs, destructive deletion, and arbitrary shell commands.

Key safety points:

- File edits require approval.
- Commands are allowlisted.
- Destructive file deletion is blocked.
- Unrestricted shell execution is blocked.
- The app does not silently self-modify.

## How to Explain Adaptive Learning

Say:

The system does not train the base model. It self-optimizes the orchestration layer by tracking judge scores, per-agent scores, model fallback, latency, workflow performance, human feedback, model tournament results, and inferred user preferences. It can recommend routing changes and propose prompt improvements, but prompt versions require approval and can be rolled back.

## How to Explain Agent Evaluation

Say:

After each workflow, the Judge Agent evaluates each agent output individually. It scores usefulness and clarity, identifies the strongest and weakest agents, and records improvement suggestions. This makes the project more advanced than a normal chatbot because it measures the quality of the agent team, not just the final answer.

## How to Explain Analytics Dashboard

Say:

The Analytics panel summarizes workflow performance. It tracks total runs, average judge score, latency, fallback usage, file tasks, image tasks, most used agents, recent runs, and human feedback. This is the start of workflow intelligence.

## How to Explain Simple Mode vs Developer Mode

Simple Mode is for normal users. It shows only the answer, files, image preview, feedback, and basic controls.

Developer Mode is for demos and debugging. It shows task routing, workflow trace, provider metadata, judge scores, per-agent evaluation, file context, image metadata, evolution notes, and raw JSON.

## Final Interview-Style Explanation

EvolveAgent AI is a full-stack multi-agent AI workspace I built with FastAPI and React. The system uses a Master Orchestrator Agent to classify requests and route them through specialist agents for research, logic, risk analysis, strategy, final writing, judging, evolution feedback, file analysis, recording analysis, mock image generation, and safe app automation planning. It supports real OpenAI text mode with mock fallback, chat sessions, file upload and document analysis, recording upload and summaries, browser voice command input, safe mock image prompts, approval-gated automation plans, per-agent evaluation, human feedback, analytics, and orchestration-level learning reports. Simple Mode gives users a clean ChatGPT-style experience, while Developer Mode exposes the full agent workflow for technical review.

## Demo Checklist

- Backend running at `http://127.0.0.1:8000`
- Frontend running at `http://127.0.0.1:5173`
- Simple Mode works
- Developer Mode works
- Text prompt works
- File upload works
- Recording upload works
- Image Agent mock preview works
- Feedback buttons work
- Analytics panel works
- Voice input button appears
- App automation plan requires approval
- Learning report works in Developer Mode
- Export Markdown/JSON works
- Backend tests pass
- Frontend build passes
- Linear status endpoint works when configured or unconfigured
- Linear panel can sync/select/run issues when backend is configured
- Poll worker detects In Progress issues and prepares branches (manual poll via Developer Mode)
- Mission Control goal cards show Linear identifier, branch, commit, and push status when linked
