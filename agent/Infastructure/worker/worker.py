import threading
import traceback
from typing import Any, Dict, Optional

import platform_monitoring

from agent.Infastructure.queue.interface import QueueInterface
from agent.high_level_agents.orchestrators.registry import Registry


class Worker:
    """Worker that pulls jobs, resolves orchestrators via Registry, runs them, persists/audits result.

    Responsibilities:
    - dequeue job
    - resolve orchestrator = registry.get(name) -> returns class/callable
    - call orchestrator.run(payload) and validate envelope
    - ack job on success, requeue or ack on failure
    - emit platform_monitoring events at start/success/error
    """

    def __init__(self, queue: QueueInterface, registry: Registry, topic: str = "orchestrate"):
        self.queue = queue
        self.registry = registry
        self.topic = topic
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def run_once(self, timeout: float = 1.0) -> None:
        item = self.queue.dequeue(self.topic, timeout=timeout)
        if not item:
            return
        job_id = item.get("job_id")
        run_id = item.get("run_id")
        orchestrator_name = item.get("orchestrator")
        platform_monitoring.log_event("worker.job.start", {"job_id": job_id, "run_id": run_id, "orchestrator": orchestrator_name})
        try:
            orch_factory = self.registry.get(orchestrator_name)
            if orch_factory is None:
                raise RuntimeError(f"unknown orchestrator: {orchestrator_name}")
            # If the registry returns a class (type), instantiate it. If it returns
            # an instance or a callable, use it directly.
            if isinstance(orch_factory, type):
                orch = orch_factory()
            else:
                orch = orch_factory
            envelope = orch.run(item.get("payload", {}))
            platform_monitoring.log_event("worker.job.success", {"job_id": job_id, "run_id": run_id, "records": len(envelope.get("records", [])) if envelope else 0})
            # TODO: persist envelope to audit store
            self.queue.ack(job_id)
        except Exception as exc:
            platform_monitoring.log_event("worker.job.error", {"job_id": job_id, "run_id": run_id, "error": str(exc)})
            try:
                meta = item.setdefault("meta", {})
                meta["last_error"] = meta.get("last_error", 0) + 1
                if meta["last_error"] <= 1:
                    self.queue.requeue(item)
                else:
                    self.queue.ack(job_id)
            except Exception:
                self.queue.ack(job_id)
            platform_monitoring.log_event("worker.job.trace", {"job_id": job_id, "trace": traceback.format_exc()})

    def start(self, poll_interval: float = 0.5):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, args=(poll_interval,), daemon=True)
        self._thread.start()

    def _run_loop(self, poll_interval: float):
        while not self._stop.is_set():
            try:
                self.run_once(timeout=poll_interval)
            except Exception:
                platform_monitoring.log_event("worker.loop.error", {"error": traceback.format_exc()})

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
