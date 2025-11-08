import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class AuditLogger:
    """Centralized audit logging utility."""

    @staticmethod
    def log_security_event(event_type: str, details: Dict[str, Any]):
        """Logs a security-relevant event.

        Args:
            event_type (str): The type of security event (e.g., USER_MODE_CHANGE, ACCOUNT_REMOVAL).
            details (Dict[str, Any]): A dictionary containing event-specific details.
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details
        }
        logger.warning(f"AUDIT_LOG: {log_entry}")

    @staticmethod
    def log_action(user_id: int, action: str, resource_type: str, resource_id: Any = None, details: Dict[str, Any] = None):
        """Logs a general user action for auditing purposes."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {}
        }
        logger.info(f"ACTION_LOG: {log_entry}")
