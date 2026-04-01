"""Third-party integrations for NeuroGraph.

Provides webhook handlers and normalizers for:
- Slack (messages, reactions, threads)
- Gmail (emails via push notifications)
- Notion (pages, databases)
"""

from src.integrations.base.normalizer import BaseNormalizer
from src.integrations.base.processor import EventProcessor

__all__ = ["BaseNormalizer", "EventProcessor"]
