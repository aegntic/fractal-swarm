"""Tests for historical data collector"""

import pytest
from agents.historical_data_collector import HistoricalDataCollector, DataWindow, HistoricalDataSwarm
from datetime import datetime, timedelta
import pandas as pd
import numpy as np


class TestDataWindow:
    """Test DataWindow"""

    def _make_df(self, rows=100):
        dates = pd.date_range("2024-01-01", periods=rows, freq="1min")
        return pd.DataFrame({
            "open": np.random.uniform(90, 110, rows),
            "high": np.random.uniform(100, 120, rows),
            "low": np.random.uniform(80, 100, rows),
            "close": np.random.uniform(90, 110, rows),
            "volume": np.random.uniform(1000, 10000, rows),
        }, index=dates)

    def test_create_window(self):
        df = self._make_df(50)
        window = DataWindow(
            symbol="BTC/USDT",
            exchange="binance",
            start_time=df.index[0].to_pydatetime(),
            end_time=df.index[-1].to_pydatetime(),
            current_time=df.index[0].to_pydatetime(),
            data=df,
        )
        assert window.symbol == "BTC/USDT"
        assert len(window.data) == 50

    def test_advance_time(self):
        df = self._make_df(100)
        window = DataWindow(
            symbol="ETH/USDT",
            exchange="coinbase",
            start_time=df.index[0].to_pydatetime(),
            end_time=df.index[-1].to_pydatetime(),
            current_time=df.index[0].to_pydatetime(),
            data=df,
        )
        before = window.current_time
        window.advance_time(10)
        assert window.current_time == before + timedelta(minutes=10)

    def test_advance_time_clamps_to_end(self):
        df = self._make_df(50)
        end = df.index[-1].to_pydatetime()
        window = DataWindow(
            symbol="BTC/USDT",
            exchange="binance",
            start_time=df.index[0].to_pydatetime(),
            end_time=end,
            current_time=df.index[0].to_pydatetime(),
            data=df,
        )
        window.advance_time(minutes=99999)
        assert window.current_time == end

    def test_has_more_data_true(self):
        df = self._make_df(100)
        window = DataWindow(
            symbol="BTC/USDT",
            exchange="binance",
            start_time=df.index[0].to_pydatetime(),
            end_time=df.index[-1].to_pydatetime(),
            current_time=df.index[0].to_pydatetime(),
            data=df,
        )
        assert window.has_more_data() is True

    def test_has_more_data_false_at_end(self):
        df = self._make_df(50)
        end = df.index[-1].to_pydatetime()
        window = DataWindow(
            symbol="BTC/USDT",
            exchange="binance",
            start_time=df.index[0].to_pydatetime(),
            end_time=end,
            current_time=end,
            data=df,
        )
        assert window.has_more_data() is False

    def test_get_visible_data_at_start(self):
        df = self._make_df(100)
        start = df.index[0].to_pydatetime()
        window = DataWindow(
            symbol="BTC/USDT",
            exchange="binance",
            start_time=start,
            end_time=df.index[-1].to_pydatetime(),
            current_time=start,
            data=df,
        )
        visible = window.get_visible_data()
        assert len(visible) == 1

    def test_get_visible_data_after_advance(self):
        df = self._make_df(100)
        start = df.index[0].to_pydatetime()
        window = DataWindow(
            symbol="BTC/USDT",
            exchange="binance",
            start_time=start,
            end_time=df.index[-1].to_pydatetime(),
            current_time=start,
            data=df,
        )
        window.advance_time(5)
        visible = window.get_visible_data()
        assert len(visible) == 6  # 0-5 inclusive


class TestHistoricalDataCollector:
    """Test HistoricalDataCollector"""

    def test_init(self):
        collector = HistoricalDataCollector()
        assert collector is not None
        assert len(collector.exchanges) == 0
        assert len(collector.data_cache) == 0

    def test_init_with_none_redis(self):
        collector = HistoricalDataCollector(redis_client=None)
        assert collector is not None


class TestHistoricalDataSwarm:
    """Test HistoricalDataSwarm"""

    def test_init(self):
        swarm = HistoricalDataSwarm(num_agents=3)
        assert swarm is not None
