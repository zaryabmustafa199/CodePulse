"""
Structured Logging Service for CodePulse Backend.
Provides formatted JSON/structured logging for observability across analysis stages.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Configure standard logger
logger = logging.getLogger("codepulse")
logger.setLevel(logging.INFO)

# Direct stdout stream handler
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def log_event(event_name: str, level: str = "info", **kwargs: Any) -> None:
    """Emit a structured event log entry with ISO timestamp and context key-values."""
    payload: Dict[str, Any] = {
        "event": event_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs
    }
    log_msg = json.dumps(payload)
    
    if level == "error":
        logger.error(log_msg)
    elif level == "warning":
        logger.warning(log_msg)
    else:
        logger.info(log_msg)
