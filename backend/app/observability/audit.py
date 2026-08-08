"""
Audit logging utilities.
"""
from __future__ import annotations
from app.observability.logger import get_logger

logger = get_logger(__name__)

class AuditLogger:
    """Audit logger for tracking user actions."""
    @staticmethod
    def log_action(user_id: str, action: str, resource: str, details: dict) -> None:
        """Log a user action."""
        logger.info("audit_log", user_id=user_id, action=action, resource=resource, details=details)
