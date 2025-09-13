from typing import Dict, Any
import logging

logger = logging.getLogger('platform_monitoring')


def log_event(event: Dict[str, Any] | str, payload: Dict[str, Any] | None = None):
    """Log a monitoring event.

    Backwards-compatible:
    - `log_event(event_dict)` -> logs the dict
    - `log_event(name, payload)` -> logs name and payload
    """
    if payload is None and isinstance(event, dict):
        logger.info('MONITOR_EVENT %s', event)
    else:
        name = event if isinstance(event, str) else str(event)
        logger.info('MONITOR_EVENT name=%s payload=%s', name, payload)


def prometheus_metric(name: str, value: float, labels: Dict[str, str] | None = None):
    # placeholder for prometheus client integration
    logger.info('PROM_METRIC %s=%s labels=%s', name, value, labels)
