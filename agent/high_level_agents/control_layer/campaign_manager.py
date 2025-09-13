from typing import Any, Dict, Optional
from datetime import datetime, timezone
from agent.high_level_agents.orchestrators.registry import Registry
from agent.high_level_agents.orchestrators.base_orchestrator import BaseOrchestrator
from agent.Infastructure.queue.interface import QueueInterface




class CampaignManager:
    """High-level control plane that schedules triggers, manages campaigns,
    and issues orchestration commands. This class subsumes a lightweight
    dispatcher: schedule/run/cancel flows and gate delivery.
    """

    def __init__(self, registry: Optional[Registry] = None, queue: Optional[QueueInterface] = None, allow_delivery: bool = False):
        self.registry = registry or Registry()
        self.queue = queue
        self.allow_delivery = allow_delivery
        self.runs = {}

    def ingest_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest an external event and decide whether to trigger workflows.

        Expected event keys: {'flow': 'lead_sync', 'context': {...}}
        Returns a run descriptor with run_id and status.
        """
        flow = event.get('flow')
        context = event.get('context', {})
        if not flow:
            return {'status': 'error', 'error': 'missing flow'}

        orchestrator = self.registry.get(flow)
        if not orchestrator:
            return {'status': 'error', 'error': f'unknown flow: {flow}'}

        run_id = f"{flow}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        self.runs[run_id] = {'status': 'queued', 'flow': flow, 'started_at': datetime.now(timezone.utc).isoformat()}

        # enqueue the run for async processing
        job = {
            'job_id': f'job-{datetime.now(timezone.utc).timestamp()}',
            'run_id': run_id,
            'orchestrator': flow,
            'payload': context,
            'meta': {'requested_at': datetime.now(timezone.utc).isoformat(), 'flow': flow},
        }

        if self.queue is None:
            # no queue provided: fallback to synchronous run for backward compatibility
            try:
                result = orchestrator.run(context)
                self.runs[run_id]['status'] = 'finished'
                self.runs[run_id]['completed_at'] = datetime.now(timezone.utc).isoformat()
                return {'status': 'ok', 'run_id': run_id, 'result': result}
            except Exception as e:
                self.runs[run_id]['status'] = 'failed'
                self.runs[run_id]['error'] = str(e)
                return {'status': 'error', 'run_id': run_id, 'error': str(e)}

        # enqueue and return run descriptor immediately
        jid = self.queue.enqueue('orchestrate', job)
        self.runs[run_id]['job_id'] = jid
        return {'status': 'queued', 'run_id': run_id, 'job_id': jid}

    def list_runs(self):
        return dict(self.runs)

    def register_flow(self, name: str, orchestrator: BaseOrchestrator):
        self.registry.register(name, orchestrator)


CONTROL_CLASS = CampaignManager
