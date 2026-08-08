"""
Metrics tracking stubs.
"""
from __future__ import annotations

class Metrics:
    """Metrics recording stubs."""
    @staticmethod
    def record_request(endpoint: str) -> None:
        """Record an incoming request."""
        pass

    @staticmethod
    def record_error(endpoint: str, error_type: str) -> None:
        """Record an error."""
        pass

    @staticmethod
    def record_latency(endpoint: str, duration: float) -> None:
        """Record request latency."""
        pass
