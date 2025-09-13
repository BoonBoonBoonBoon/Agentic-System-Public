## High-level agents — overview

This package contains the control and orchestration pieces that schedule,
coordinate, and execute multi-step workflows. The implementation is intentionally
small and modular so orchestrators and operational agents can be developed and
tested independently.

#### Top-level responsibilities
- CampaignManager (`control_layer/campaign_manager.py`):
	- Accepts external triggers or events, decides which flow to run, creates a
		run descriptor (run_id), and either executes the orchestrator synchronously
		or enqueues a job for async processing. Acts as the control-plane entrypoint.

- OrchestrationEngine (`orchestration_engine/runner.py`):
	- Executes flow definitions (graph or sequence of steps). Responsible for
		step sequencing, conditional branching, retries, and returning a canonical
		envelope with metadata and records.

- Orchestrators (`orchestrators/*.py`, `BaseOrchestrator`):
	- Domain-level workflow classes that encapsulate business logic (e.g., lead
		handling, delivery). Implement a `run(payload)` contract and use the
		`Registry` to find operational agents/tools.

- Dispatcher (`dispatcher/dispatcher.py`):
	- Lightweight in-process concurrency guard. Enforces per-agent concurrency
		limits using semaphores. Intended for development; replace with an external
		throttling service in production.

- Queue & Worker (see `agent/Infastructure/queue` and `agent/Infastructure/worker`):
	- `QueueInterface` and `InMemoryQueue` provide async handoff semantics
		(enqueue, dequeue, visibility timeout, ack, requeue).
	- `Worker` polls the queue, resolves the orchestrator via `Registry`, runs
		it, and handles ack/requeue logic and monitoring events.

#### How these pieces work together (high-level flow)
1. External event → `CampaignManager.ingest_event(event)` decides the flow.
2. If async, `CampaignManager` enqueues a job on the queue; otherwise it calls
	 the orchestrator directly.
3. Worker dequeues a job, resolves the orchestrator (via `Registry`), and
	 calls `orchestrator.run(payload)`.
4. Orchestrator (or `OrchestrationEngine`) invokes operational agents (via
	 `Registry`) to perform tasks; Dispatcher may be used to respect concurrency
	 limits for expensive operations (LLMs, DB writes).
5. Worker acknowledges success or requeues on transient failures; platform
	 monitoring emits events for observability.






