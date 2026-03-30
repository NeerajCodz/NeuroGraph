"""Temporal decay engine for memory confidence over time."""

import math
from datetime import datetime
from typing import Any

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class TemporalDecay:
    """Manages temporal decay of memory confidence.
    
    Uses exponential decay: confidence(t) = initial_confidence * e^(-rate * age)
    
    Default rate (0.05) means:
    - 1 day old: 95% of original confidence
    - 7 days old: 70% of original confidence
    - 14 days old: 50% of original confidence
    - 30 days old: 22% of original confidence
    - 60 days old: 5% of original confidence
    """

    def __init__(self, decay_rate: float | None = None) -> None:
        """Initialize decay engine.
        
        Args:
            decay_rate: Custom decay rate (defaults to config value)
        """
        settings = get_settings()
        self._decay_rate = decay_rate or settings.memory_decay_rate

    @property
    def decay_rate(self) -> float:
        """Get current decay rate."""
        return self._decay_rate

    def calculate_decay(self, age_days: float) -> float:
        """Calculate decay factor for a given age.
        
        Args:
            age_days: Age in days
            
        Returns:
            Decay factor between 0 and 1
        """
        if age_days < 0:
            return 1.0
        return math.exp(-self._decay_rate * age_days)

    def compute(self, age_days: float) -> float:
        """Alias for calculate_decay for test compatibility."""
        return self.calculate_decay(age_days)

    def compute_temporal_score(self, age_days: float, confidence: float) -> float:
        """Calculate temporal score (decay * confidence)."""
        decay = self.calculate_decay(age_days)
        return decay * confidence

    def compute_from_timestamp(self, timestamp: datetime) -> float:
        """Calculate decay from a timestamp."""
        age_days = self.get_age_days(timestamp)
        return self.calculate_decay(age_days)

    def apply_decay(
        self,
        confidence: float,
        age_days: float,
    ) -> float:
        """Apply decay to a confidence score.
        
        Args:
            confidence: Original confidence (0-1)
            age_days: Age in days
            
        Returns:
            Decayed confidence
        """
        decay = self.calculate_decay(age_days)
        return confidence * decay

    def get_age_days(self, created_at: datetime | str) -> float:
        """Calculate age in days from creation timestamp.
        
        Args:
            created_at: Creation timestamp
            
        Returns:
            Age in days (can be fractional)
        """
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        
        now = datetime.utcnow()
        if created_at.tzinfo:
            now = datetime.now(created_at.tzinfo)
        
        delta = now - created_at.replace(tzinfo=None)
        return delta.total_seconds() / 86400  # seconds per day

    def apply_to_results(
        self,
        results: list[dict[str, Any]],
        confidence_key: str = "confidence",
        created_at_key: str = "created_at",
    ) -> list[dict[str, Any]]:
        """Apply decay to a list of results.
        
        Args:
            results: List of result dictionaries
            confidence_key: Key for confidence value
            created_at_key: Key for creation timestamp
            
        Returns:
            Results with decayed confidence and added metadata
        """
        decayed_results = []
        
        for result in results:
            result = result.copy()
            
            original_confidence = result.get(confidence_key, 1.0)
            created_at = result.get(created_at_key)
            
            if created_at:
                age_days = self.get_age_days(created_at)
                decay = self.calculate_decay(age_days)
                decayed_confidence = original_confidence * decay
                
                result["original_confidence"] = original_confidence
                result["age_days"] = age_days
                result["decay_factor"] = decay
                result[confidence_key] = decayed_confidence
            
            decayed_results.append(result)
        
        return decayed_results

    def should_prune(
        self,
        confidence: float,
        age_days: float,
        min_confidence: float = 0.1,
    ) -> bool:
        """Check if a memory should be pruned due to decay.
        
        Args:
            confidence: Original confidence
            age_days: Age in days
            min_confidence: Minimum threshold
            
        Returns:
            True if decayed confidence is below threshold
        """
        decayed = self.apply_decay(confidence, age_days)
        return decayed < min_confidence

    def estimate_half_life(self) -> float:
        """Estimate half-life in days (time for confidence to reach 50%).
        
        Based on: 0.5 = e^(-rate * t)
        Solving: t = -ln(0.5) / rate = 0.693 / rate
        """
        return 0.693 / self._decay_rate

    def estimate_retention_days(
        self,
        initial_confidence: float,
        min_confidence: float = 0.1,
    ) -> float:
        """Estimate days until confidence drops below threshold.
        
        Args:
            initial_confidence: Starting confidence
            min_confidence: Threshold to calculate retention for
            
        Returns:
            Days until confidence drops below threshold
        """
        if initial_confidence <= min_confidence:
            return 0.0
        
        # Solve: min = initial * e^(-rate * t)
        # t = -ln(min/initial) / rate
        ratio = min_confidence / initial_confidence
        return -math.log(ratio) / self._decay_rate


def apply_temporal_decay(
    results: list[dict[str, Any]],
    decay_rate: float | None = None,
) -> list[dict[str, Any]]:
    """Convenience function to apply decay to results.
    
    Args:
        results: List of results with confidence and created_at
        decay_rate: Optional custom decay rate
        
    Returns:
        Results with decayed confidence
    """
    decay = TemporalDecay(decay_rate)
    return decay.apply_to_results(results)
