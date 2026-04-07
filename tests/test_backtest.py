"""Tests for backtesting modules"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtesting.future_blind_simulator import (
    FutureBlindSimulator, TradeSignal, Trade, SimulationResult, TradingStrategy
)
from agents.historical_data_collector import DataWindow


class TestTradeSignal:
    """Test TradeSignal dataclass"""

    def test_create_signal(self):
        signal = TradeSignal(
            timestamp=datetime.now(),
            symbol="BTC/USDT",
            action="buy",
            confidence=0.8,
            size=1.0,
            strategy_name="test_strategy",
        )
        assert signal.action == "buy"
        assert signal.confidence == 0.8
        assert signal.symbol == "BTC/USDT"

    def test_signal_with_metadata(self):
        signal = TradeSignal(
            timestamp=datetime.now(),
            symbol="ETH/USDT",
            action="sell",
            confidence=0.5,
            size=0.5,
            strategy_name="test",
            metadata={"rsi": 70},
        )
        assert signal.metadata["rsi"] == 70


class TestTrade:
    """Test Trade dataclass"""

    def test_create_trade(self):
        trade = Trade(
            timestamp=datetime.now(),
            symbol="BTC/USDT",
            side="buy",
            price=50000.0,
            size=0.1,
            fee=5.0,
            trade_id="test_1",
            strategy_name="test",
        )
        assert trade.side == "buy"
        assert trade.price == 50000.0
        assert trade.pnl is None


class TestDataWindow:
    """Test DataWindow dataclass"""

    def _make_window(self, rows=100):
        """Create a synthetic DataWindow for testing"""
        dates = pd.date_range("2024-01-01", periods=rows, freq="1min")
        df = pd.DataFrame({
            "open": np.random.uniform(90, 110, rows),
            "high": np.random.uniform(100, 120, rows),
            "low": np.random.uniform(80, 100, rows),
            "close": np.random.uniform(90, 110, rows),
            "volume": np.random.uniform(1000, 10000, rows),
        }, index=dates)
        return DataWindow(
            symbol="BTC/USDT",
            exchange="binance",
            start_time=dates[0].to_pydatetime(),
            end_time=dates[-1].to_pydatetime(),
            current_time=dates[0].to_pydatetime(),
            data=df,
        )

    def test_create_window(self):
        window = self._make_window(50)
        assert window.symbol == "BTC/USDT"
        assert window.exchange == "binance"
        assert len(window.data) == 50

    def test_has_more_data_at_start(self):
        window = self._make_window(100)
        assert window.has_more_data() is True

    def test_advance_time(self):
        window = self._make_window(100)
        original = window.current_time
        window.advance_time(minutes=5)
        assert window.current_time == original + timedelta(minutes=5)

    def test_get_visible_data_subset(self):
        window = self._make_window(100)
        # At start, only the first row should be visible
        visible = window.get_visible_data()
        assert len(visible) >= 1
        assert len(visible) <= len(window.data)


class TestFutureBlindSimulator:
    """Test FutureBlindSimulator"""

    def _make_window(self, rows=200):
        dates = pd.date_range("2024-01-01", periods=rows, freq="1min")
        # Create a price series with some trend
        close = 100 + np.cumsum(np.random.randn(rows) * 0.5)
        df = pd.DataFrame({
            "open": close - 0.1,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": np.random.uniform(1000, 10000, rows),
        }, index=dates)
        return DataWindow(
            symbol="BTC/USDT",
            exchange="binance",
            start_time=dates[0].to_pydatetime(),
            end_time=dates[-1].to_pydatetime(),
            current_time=dates[0].to_pydatetime(),
            data=df,
        )

    def test_init(self):
        sim = FutureBlindSimulator(initial_capital=10000)
        assert sim.initial_capital == 10000
        assert len(sim.strategies) == 0

    def test_add_strategy(self):
        sim = FutureBlindSimulator()
        strategy = SimpleTestStrategy()
        sim.add_strategy(strategy)
        assert len(sim.strategies) == 1

    @pytest.mark.asyncio
    async def test_run_simulation_no_strategies(self):
        sim = FutureBlindSimulator(initial_capital=10000)
        window = self._make_window(100)
        result = await sim.run_simulation(window)
        assert result.final_balance == 10000
        assert len(result.trades) == 0

    @pytest.mark.asyncio
    async def test_run_simulation_with_strategy(self):
        sim = FutureBlindSimulator(initial_capital=10000)
        sim.add_strategy(SimpleTestStrategy())
        window = self._make_window(200)
        result = await sim.run_simulation(window)
        assert isinstance(result, SimulationResult)
        assert result.final_balance > 0
        assert isinstance(result.total_return, float)
        assert isinstance(result.max_drawdown, float)

    @pytest.mark.asyncio
    async def test_run_simulation_resets_strategies(self):
        sim = FutureBlindSimulator()
        strategy = SimpleTestStrategy()
        strategy.position = 999  # poison the state
        sim.add_strategy(strategy)
        window = self._make_window(200)
        await sim.run_simulation(window)
        assert strategy.position == 0  # should be reset


class SimpleTestStrategy(TradingStrategy):
    """Minimal strategy for testing - buys on every opportunity"""

    def __init__(self):
        super().__init__("test_strategy", {"threshold": 0.6})
        self.call_count = 0

    async def analyze(self, data, current_time):
        self.call_count += 1
        # Generate a buy signal on first call, sell on second, then nothing
        if self.call_count == 1:
            return TradeSignal(
                timestamp=current_time,
                symbol="BTC/USDT",
                action="buy",
                confidence=0.8,
                size=0.1,
                strategy_name=self.name,
            )
        elif self.call_count == 2:
            return TradeSignal(
                timestamp=current_time,
                symbol="BTC/USDT",
                action="sell",
                confidence=0.8,
                size=0.1,
                strategy_name=self.name,
            )
        return None
