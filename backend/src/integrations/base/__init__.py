"""Base classes for integrations."""

from src.integrations.base.normalizer import BaseNormalizer
from src.integrations.base.processor import EventProcessor

__all__ = ["BaseNormalizer", "EventProcessor"]
