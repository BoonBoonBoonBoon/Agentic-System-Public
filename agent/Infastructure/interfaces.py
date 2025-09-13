from typing import Any, Dict, Optional, Protocol

"""Infrastructure Interface Contracts.

Purpose:
    This module defines the official "contracts" (interfaces) for core
    infrastructure components like queues and orchestrators. It centralizes these
    shared interfaces to prevent circular import errors and allow different parts
    of the system to communicate without depending on concrete implementations.

Contents:
    - QueueInterface: The contract for any queueing system.
    - OrchestrationEngineProtocol: The contract for any orchestration engine.
    - DispatcherProtocol: The contract for any dispatcher.

Why This Is Important:
    By depending on these simple, stable contracts instead of actual classes,
    we can swap out implementations (e.g., use an in-memory queue for testing
    and a cloud queue for production) without breaking the code that uses them.
    This makes the system more flexible, easier to test, and safer to refactor.

How to Use:
    - Callers: Type-hint your function arguments with these protocols.
        Example: def process_item(my_queue: QueueInterface): ...

    - Implementers: Ensure your concrete class (e.g., InMemoryQueue)
      satisfies the methods and properties defined in the protocol.
"""


class QueueInterface(Protocol):
    """Stable, canonical definition for the queue contract used across the repo.

    Implementations (e.g. `InMemoryQueue`) should implement these methods.
    """

    def enqueue(self, topic: str, message: Dict[str, Any]) -> str:
        """Enqueue a message on `topic`. Return job_id."""

    def dequeue(self, topic: str, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Blocking pop from topic. Return full job dict or None on timeout."""

    def ack(self, job_id: str) -> None:
        """Acknowledge completion of job_id (idempotent)."""

    def requeue(self, job: Dict[str, Any], delay: Optional[float] = None) -> str:
        """Re-enqueue a job (optionally with delay). Returns new job_id."""


class OrchestrationEngineProtocol(Protocol):
    """Protocol for orchestration engine implementations.

    The real implementation lives in `agent.Infastructure.orchestration_engine.runner`.
    This Protocol allows callers to depend on the engine shape without importing
    concrete implementations directly.
    """

    def run_flow(self, name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        ...


class DispatcherProtocol(Protocol):
    """Minimal protocol for dispatcher-like components used by callers.

    Implementations should provide a `submit(agent_name, func, *args, **kwargs)` method.
    """

    def submit(self, agent_name: str, func, *args, **kwargs):
        ...


__all__ = ["QueueInterface", "OrchestrationEngineProtocol", "DispatcherProtocol"]
