## Infrastructure package


This package contains the runtime building blocks that high-level agents use
to execute workflows: queues, workers, dispatchers, and the orchestration
engine. Implementations here are intentionally lightweight for
development.

### Core components

- `interfaces.py` — stable Protocols for infra contracts:
	- `QueueInterface`: enqueue/dequeue/ack/requeue semantics.
	- `OrchestrationEngineProtocol`: `run_flow(name, context) -> dict`.
	- `DispatcherProtocol`: concurrency control `submit(agent_name, func, ...)`.

- `queue/` — queue contract and in-memory implementation:
	- `queue/interface.py` re-exports the canonical `QueueInterface`.
	- `queue/in_memory.py` implements `InMemoryQueue` with visibility timeout
		and basic requeue semantics. Useful for tests and local development.

- `worker/` — background executor:
	- `worker/worker.py` implements `Worker` that polls a queue topic, resolves
		orchestrators from the `Registry`, runs them, and handles ack/requeue.

- `dispatcher/` — execution guard:
	- `dispatcher/dispatcher.py` enforces per-agent concurrency limits using
		semaphores. Replace this with a distributed limiter for production.

- `orchestration_engine/` — flow runtime:
	- `orchestration_engine/runner.py` defines `OrchestrationEngine` (flow
		executor interface). Implementations should accept a flow name and
		context and return a canonical envelope.


