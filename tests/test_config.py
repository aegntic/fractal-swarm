"""Tests for config module"""

import pytest
from config import SwarmConfig, TradingPhase, config


class TestTradingPhase:
    """Test TradingPhase enum"""

    def test_has_three_phases(self):
        phases = list(TradingPhase)
        assert len(phases) == 3

    def test_phase_values(self):
        assert TradingPhase.MICRO.value == "micro"
        assert TradingPhase.GROWTH.value == "growth"
        assert TradingPhase.SCALE.value == "scale"

    def test_phase_ordering(self):
        # Enum values are strings; verify definition order
        phases = list(TradingPhase)
        assert phases[0] == TradingPhase.MICRO
        assert phases[1] == TradingPhase.GROWTH
        assert phases[2] == TradingPhase.SCALE


class TestSwarmConfig:
    """Test SwarmConfig defaults"""

    def test_default_initial_capital(self):
        assert config.initial_capital == 100.0

    def test_default_target_capital(self):
        assert config.target_capital == 100000.0

    def test_phase_thresholds_exist(self):
        assert TradingPhase.MICRO in config.phase_thresholds
        assert TradingPhase.GROWTH in config.phase_thresholds
        assert TradingPhase.SCALE in config.phase_thresholds

    def test_micro_phase_thresholds(self):
        low, high = config.phase_thresholds[TradingPhase.MICRO]
        assert low == 100
        assert high == 1000

    def test_growth_phase_thresholds(self):
        low, high = config.phase_thresholds[TradingPhase.GROWTH]
        assert low == 1000
        assert high == 10000

    def test_scale_phase_thresholds(self):
        low, high = config.phase_thresholds[TradingPhase.SCALE]
        assert low == 10000
        assert high == 100000

    def test_strategy_weights_by_phase(self):
        for phase in TradingPhase:
            assert phase in config.strategy_weights
            weights = config.strategy_weights[phase]
            assert len(weights) > 0
            # Weights should roughly sum to 1.0
            assert abs(sum(weights.values()) - 1.0) < 0.05

    def test_risk_params_by_phase(self):
        for phase in TradingPhase:
            assert phase in config.risk_params
            rp = config.risk_params[phase]
            assert "max_position_size" in rp
            assert "stop_loss" in rp
            assert 0 < rp["max_position_size"] <= 1.0

    def test_exchanges_defined(self):
        assert "spot" in config.exchanges
        assert "dex" in config.exchanges
        assert len(config.exchanges["spot"]) > 0
