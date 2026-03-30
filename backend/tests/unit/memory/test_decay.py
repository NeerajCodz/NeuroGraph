"""Unit tests for decay module."""

import pytest
import math
from datetime import datetime, timedelta


class TestTemporalDecay:
    """Tests for TemporalDecay class."""

    def test_init(self, mock_settings):
        """Test decay engine initialization."""
        from src.memory.decay import TemporalDecay
        
        decay = TemporalDecay()
        
        assert decay.decay_rate == 0.05

    def test_compute_decay_zero_days(self, mock_settings):
        """Test decay with zero days (should be 1.0)."""
        from src.memory.decay import TemporalDecay
        
        decay = TemporalDecay()
        result = decay.compute(0)
        
        assert result == 1.0

    def test_compute_decay_one_day(self, mock_settings):
        """Test decay after one day."""
        from src.memory.decay import TemporalDecay
        
        decay = TemporalDecay()
        result = decay.compute(1)
        
        expected = math.exp(-0.05 * 1)
        assert abs(result - expected) < 0.001

    def test_compute_decay_30_days(self, mock_settings):
        """Test decay after 30 days."""
        from src.memory.decay import TemporalDecay
        
        decay = TemporalDecay()
        result = decay.compute(30)
        
        expected = math.exp(-0.05 * 30)  # ~0.223
        assert abs(result - expected) < 0.001

    def test_compute_temporal_score(self, mock_settings):
        """Test temporal score with confidence."""
        from src.memory.decay import TemporalDecay
        
        decay = TemporalDecay()
        result = decay.compute_temporal_score(10, 0.8)
        
        expected_decay = math.exp(-0.05 * 10)
        expected = expected_decay * 0.8
        assert abs(result - expected) < 0.001

    def test_compute_from_timestamp(self, mock_settings):
        """Test decay from timestamp."""
        from src.memory.decay import TemporalDecay
        
        decay = TemporalDecay()
        
        # 10 days ago
        timestamp = datetime.now() - timedelta(days=10)
        result = decay.compute_from_timestamp(timestamp)
        
        expected = math.exp(-0.05 * 10)
        assert abs(result - expected) < 0.01  # Allow some tolerance for time calculations

    def test_custom_decay_rate(self, mock_settings):
        """Test with custom decay rate."""
        from src.memory.decay import TemporalDecay
        
        decay = TemporalDecay(decay_rate=0.1)
        result = decay.compute(10)
        
        expected = math.exp(-0.1 * 10)  # ~0.368
        assert abs(result - expected) < 0.001
