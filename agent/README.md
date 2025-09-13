# Agent package — Overview

This README is a concise reference for the `agent/` package: the main moving
parts, responsibilities, how they connect, and a step-by-step flow from an
external trigger to a final canonical envelope. Use this as a quick onboarding
guide and as a map for refactors or productionization work.

Summary of main components
--------------------------
- **Infrastructure (agent/Infastructure)**
  - `interfaces.py` — canonical Protocols (QueueInterface, OrchestrationEngineProtocol, DispatcherProtocol).
  - `queue/in_memory.py` — `InMemoryQueue` for local development (visibility timeout, ack/requeue).
  - `dispatcher/dispatcher.py` — in-process `Dispatcher` enforcing per-agent concurrency (semaphores).
  - `worker/worker.py` — `Worker` pulls jobs, resolves orchestrators, runs them, emits monitoring events, and handles ack/requeue.
  - `orchestration_engine/runner.py` — intended orchestration engine abstraction (local runner placeholder).

- **High-level agents (agent/high_level_agents)**
  - `control_layer/campaign_manager.py` — `CampaignManager` accepts triggers, selects flows, creates run/job metadata, enqueues runs, and gates delivery.
  - `orchestrators/` — `BaseOrchestrator` and domain orchestrator implementations (LeadOrchestrator, DeliveryOrchestrator) which implement `run` and orchestrate node calls.

- **Operational agents (agent/operational_agents)**
  - Domain-specific workers/tools (RAGAgent, CopywriterAgent, DB write agents, delivery tools). They perform I/O, call external services, and return canonical envelopes.

- **Tools (agent/tools)**
  - Small clients and deterministic helpers (Supabase client wrapper, DataCoordinator, tool discovery registry).

- **Utils (agent/utils)**
  - `envelope.py` — `Envelope` dataclass and helpers for canonical envelope creation and validation.
  - `schemas.py` — optional `pydantic` models used when `pydantic` is installed.

- **Monitoring (platform_monitoring)**
  - `exporters.py` — lightweight event logging helpers used to emit observability events across the system.

How these parts interact (high-level)
------------------------------------
- Registries discover and return orchestrators and tools by name to keep wiring dynamic and decoupled.
- The canonical envelope (`agent/utils/envelope.py`) is the contract used at component boundaries: every node/agent should return an envelope-like dict with `metadata` and `records` containing `provenance`.
- CampaignManager is the control plane: it receives triggers and enqueues jobs. Queue + Worker is the async execution boundary. Workers resolve orchestrators from the registry and run them, while Dispatcher enforces per-agent concurrency when invoking costly agents.

Step-by-step flow (trigger → final envelope)
-------------------------------------------
1) External trigger arrives: an API call, a scheduled event, or a webhook.
   - Entrypoint: `CampaignManager.ingest_event(event)` (`agent/high_level_agents/control_layer/campaign_manager.py`).

2) CampaignManager chooses the orchestrator for the requested flow.
   - Uses the orchestrator registry (under `agent/high_level_agents/orchestrators`) to resolve the flow name.
   - Generates a `run_id`, builds a `job` payload, and either enqueues it or runs synchronously if no queue is configured.

3) Job is enqueued on a topic (async boundary).
   - Queue contract: `QueueInterface.enqueue(topic, message)` (`agent/Infastructure/interfaces.py`).
   - Local dev uses `InMemoryQueue.enqueue(...)`.

4) Worker dequeues the job and starts execution.
   - `Worker.run_once` dequeues (`queue.dequeue`) and emits `worker.job.start` via `platform_monitoring`.

5) Worker resolves the orchestrator and calls `orch.run(payload)`.
   - Orchestrator is fetched via the orchestrator registry.
   - Orchestrator composes flow logic, calling operational agents and the orchestration engine as needed.

6) Node execution and agent calls.
   - For each node the orchestrator/engine resolves the tool/agent and calls it via `Dispatcher.submit(agent_name, func, ...)` to enforce limits.
   - Operational agents return canonical envelopes (`Envelope.from_records(...)`).

7) Orchestrator aggregates node outputs into a final canonical envelope.
   - Validate the envelope (use `BaseOrchestrator.validate_envelope` or `Envelope.validate()`).

8) Worker persists/audits results and acknowledges the queue.
   - Emit `worker.job.success` via `platform_monitoring` and call `queue.ack(job_id)`.
   - On transient errors, requeue; on repeated failures, ack and record traces.

9) CampaignManager / external systems handle delivery and further actions.
   - Delivery gating and security: action-producing agents require explicit enablement (`allow_delivery` in CampaignManager).

Cross-cutting concerns and TODOs
-------------------------------
- Observability: extend `platform_monitoring` to structured traces/metrics.
- Persistence: persist final envelopes and node traces to an audit store (Supabase wrapper exists in `agent/tools`).
- Production infra: replace `InMemoryQueue` and `Dispatcher` with distributed backends (Redis, SQS, or a task runner) implementing `QueueInterface`.
- Orchestration Engine: implement `OrchestrationEngine.run_flow` or integrate with a graph runner for retries, parallelism, and node policies.
- Security: ensure `.env` and credentials are not committed; follow the repo sanitization checklist before public release.

Quick dev wiring pattern (example)
---------------------------------
- Instantiate `InMemoryQueue`, `Registry`, `CampaignManager`, register flows, start a `Worker` in the same process for smoke tests.

TODO
---------------------------------
- Add a runnable wiring example `agent/Infastructure/wiring.py` (demo + smoke test).
- Add a small orchestration engine stub that runs a sequence of node callables and wires `Dispatcher` for concurrency.
- Add a CI import-check to ensure `agent/Infastructure` modules import cleanly after refactors.

If you want, I'll create the wiring example and a minimal smoke test now.
