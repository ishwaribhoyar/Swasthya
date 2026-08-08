"""
Feature flags configuration.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class FeatureFlags:
    """Application feature flags."""
    enable_ai_copilot: bool = False
    enable_advanced_analytics: bool = False
