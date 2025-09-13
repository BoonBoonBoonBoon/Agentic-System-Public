# Agentic System — Overview

**Disclaimer**



- This repository is a public demonstration of a private product developed by my LLC.
- It does not reflect the current state, full functionality, or progress of the actual product under active development.
- It does not reflect the current state, full functionality, or progress of the actual product under active development.
- All secrets have been removed to protect confidentiality for both myself and clients.
- Portions of the codebase and infrastructure have been modified, mocked, or simplified for privacy, testing, and demonstration purposes. 
- This project is not open source. It is provided solely as an artistic/illustrative showcase.
- The code in this repository will not run out-of-the-box. Users are expected to design and implement their own features, configurations, and integrations if they wish to experiment with it.



This repository demonstrates a modular agent framework focused on orchestration patterns, tool integration, and deterministic, auditable Retrieval-Augmented Generation (RAG) workflows. It combines lightweight infrastructure primitives, domain orchestrators, operational agents, and simple utility tools to make building and testing agentic pipelines straightforward.

This is a provenance-first, testable RAG agent architecture using small, composable tools (LangChain-style) and an orchestration layer (LangGraph-style patterns).


**Key Features**
- Modular RAG agent and tool wrappers (Supabase integration, deterministic query helpers).
- Standardized JSON envelope for agent-to-agent communication with per-record provenance.
- Registries for dynamic discovery of orchestrators, operational agents, and tools.
- Lightweight infra primitives: in-memory queue, dispatcher, worker for dev/testing.
- Test-friendly design with mocked vs live test toggles and example wiring for smoke tests.

**Quick Start (dev)**
1. Create and activate a venv (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and set placeholder values (do not commit real secrets):

```text
# .env (example values only)
SUPABASE_URL=https://example.supabase.co
SUPABASE_ANON_KEY=__REDACTED__
OPENAI_API_KEY=__REDACTED__
```

3. Run unit tests (fast, mock-based):

```powershell
pytest -q
```

4. For live queries (developer-only), set `USE_REAL_TESTS=1` in environment before running live scripts. Use careful credential handling and rotate keys if they leak.

**Project layout (high level)**
- `agent/` — core orchestrators, registries, agents, and infra.
	- `Infastructure/` — canonical `interfaces.py` (queue/engine/dispatcher Protocols), `queue/` (InMemoryQueue), `dispatcher/` (Dispatcher), `worker/` (Worker), `orchestration_engine/` (runner stub).
	- `high_level_agents/` — `control_layer` (CampaignManager), `orchestrators` (BaseOrchestrator and domain flows), `registry` for flows.
	- `operational_agents/` — focused agents (RAGAgent, copywriter, db write, delivery) that perform I/O and return canonical envelopes.
	- `tools/` — deterministic clients and helpers (Supabase wrapper, DataCoordinator, tool discovery registry).
	- `utils/` — `envelope.py` (Envelope dataclass and helpers) and optional `schemas.py` (pydantic models) for stricter validation.
- `platform_monitoring/` — lightweight telemetry helpers used across the system.
- `tests/` — unit and integration tests, with flags to gate real external calls.
- `debug/` — local debugging scripts and captured logs (should be sanitized or removed before public release).

**Core concepts**
- Envelope pattern: a canonical JSON envelope `{ metadata, records[], status, error }` is used at component boundaries. Each record includes `provenance` (`source`, `row_id`, `row_hash`, `retrieved_at`) to support audit and deduplication.
- Registries: dynamic discovery for tools and agents. Tools expose `TOOL` or `create_tool()` and are discovered by `agent.tools.registry`. Orchestrators are registered with the orchestrator registry used by `CampaignManager` and `Worker`.
- Protocols & DI: `agent/Infastructure/interfaces.py` defines `QueueInterface`, `OrchestrationEngineProtocol`, and `DispatcherProtocol` to avoid circular imports and enable swapping implementations for tests and production.

**End-to-end flow (concise)**
1. External trigger (API/scheduler/webhook) calls `CampaignManager.ingest_event(event)`.
2. `CampaignManager` resolves the named orchestrator via the orchestrator registry and creates a `run_id` + job payload.
3. Job is enqueued via `QueueInterface.enqueue(...)` (e.g., `InMemoryQueue` in dev).
4. A `Worker` dequeues the job, emits a `worker.job.start` event, resolves the orchestrator and calls `orch.run(payload)`.
5. The orchestrator composes a workflow: for each node it resolves tools/agents, uses `Dispatcher.submit` to enforce concurrency, and calls operational agents.
6. Operational agents (RAGAgent, DataCoordinator, etc.) return canonical envelopes with provenance.
7. Orchestrator aggregates node outputs to a final envelope and returns it to the worker.
8. Worker persists/audits the envelope (TODO: audit store), emits success/error events, and acks or requeues the job.
9. CampaignManager or downstream systems handle delivery (gated by `allow_delivery`) and external observability consumes monitoring events.

**LangGraph vs LangChain (design note)**
- LangGraph-like layer: orchestration, flow graphs, retries, branching, and auditability (Orchestration Engine, Orchestrators).
- LangChain-like layer: tools and LLM logic (SupabaseTool, CopyAgent, RAG-style agents). Keep prompt templates, wrapper logic, and deterministic DB queries in the tools layer.

**Testing & CI**
- Unit tests mock external services for speed and determinism; integration/live tests are gated by `USE_REAL_TESTS`.
- Add an import-check job in CI to validate `agent/Infastructure` modules after refactors.

**Security & publishing checklist**
- Do not commit `.env` or real credentials. Add `.env` to `.gitignore` and remove any tracked `.env` (`git rm --cached .env`).
- Remove or redact any captured logs in `debug/` before public release (e.g., `debug/test_output.txt`).
- Run a secret scan (detect-secrets, truffleHog, or the project's custom scanners) and rotate any exposed credentials.
- If secrets were committed historically, rewrite history using `git-filter-repo` or BFG on a mirrored clone and coordinate pushes to remotes.

**Developer notes & next steps**
- Implement or integrate a real Orchestration Engine (LangGraph or a scheduler) to replace the `runner.py` placeholder.
- Replace `InMemoryQueue`/`Dispatcher` with production queues and rate-limiters as needed.
- Persist envelopes and node traces to an audit store (Supabase wrappers exist in `agent/tools`).
- Add `CONTRIBUTING.md` and `SECURITY.md` for public contributors. Consider adding a `SECURITY.md` with private reporting instructions.

