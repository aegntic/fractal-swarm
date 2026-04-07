"""
Backtest multi-timeframe confluence strategy against real Binance data.
Outputs Sharpe ratio, win rate, max drawdown, per-strategy breakdown.
"""
import asyncio
import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from multi_timeframe_learning_swarm import (
    TechnicalAnalyzer, ConfluenceAnalyzer, Timeframe
)
from backtesting.future_blind_simulator import (
    FutureBlindSimulator, TradingStrategy, TradeSignal
)
from knowledge_base_schema import StrategyGenome

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "ohlcv")
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]


class ConfluenceStrategy(TradingStrategy):
    """Multi-timeframe confluence strategy wired to real data"""

    def __init__(self, name, params=None):
        super().__init__(name, params or {})
        self.genome = StrategyGenome(
            name=name,
            confluence_threshold=self.params.get("confluence_threshold", 0.6),
            min_timeframe_alignment=self.params.get("min_alignment", 3),
        )

    async def analyze(self, data: pd.DataFrame, current_time: datetime) -> Optional[TradeSignal]:
        if len(data) < 50:
            return None

        # Calculate features
        close = data["close"]
        returns = close.pct_change()

        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1] if loss.iloc[-1] != 0 else 50

        # Trend (SMA cross)
        sma_20 = close.rolling(20).mean().iloc[-1]
        sma_50 = close.rolling(50).mean().iloc[-1] if len(data) >= 50 else sma_20
        price = close.iloc[-1]

        # Volume
        vol = data["volume"]
        vol_ratio = vol.iloc[-1] / vol.rolling(20).mean().iloc[-1] if vol.rolling(20).mean().iloc[-1] > 0 else 1

        # Momentum
        mom_5 = returns.rolling(5).mean().iloc[-1] if len(returns) >= 5 else 0
        mom_20 = returns.rolling(20).mean().iloc[-1] if len(returns) >= 20 else 0

        # Bollinger Band position
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        upper = sma20 + 2 * std20
        lower = sma20 - 2 * std20
        bb_pos = (price - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1]) if (upper.iloc[-1] - lower.iloc[-1]) > 0 else 0.5

        # Scoring
        score = 0.0
        reasons = []

        # Trend alignment
        if price > sma_20 > sma_50:
            score += 0.3
            reasons.append("bull_trend")
        elif price < sma_20 < sma_50:
            score -= 0.3
            reasons.append("bear_trend")

        # RSI
        if rsi < 30:
            score += 0.25
            reasons.append("rsi_oversold")
        elif rsi > 70:
            score -= 0.25
            reasons.append("rsi_overbought")
        elif 40 < rsi < 60:
            score += 0.05
            reasons.append("rsi_neutral_bull")

        # Momentum
        if mom_5 > 0.01:
            score += 0.15
            reasons.append("mom5_up")
        elif mom_5 < -0.01:
            score -= 0.15
            reasons.append("mom5_down")

        if mom_20 > 0.005:
            score += 0.1
            reasons.append("mom20_up")
        elif mom_20 < -0.005:
            score -= 0.1
            reasons.append("mom20_down")

        # Volume confirmation
        if vol_ratio > 1.5 and score != 0:
            score *= 1.2
            reasons.append("high_vol")

        # Bollinger
        if bb_pos < 0.2:
            score += 0.1
            reasons.append("bb_lower")
        elif bb_pos > 0.8:
            score -= 0.1
            reasons.append("bb_upper")

        # Decision
        threshold = self.params.get("signal_threshold", 0.4)
        if score > threshold:
            confidence = min(abs(score) / 1.5, 1.0)
            return TradeSignal(
                timestamp=current_time,
                symbol=self.params.get("symbol", "BTC/USDT"),
                action="buy",
                confidence=confidence,
                size=self.params.get("position_size", 1.0),
                strategy_name=self.name,
                metadata={"score": round(score, 3), "reasons": reasons, "rsi": round(rsi, 1)},
            )
        elif score < -threshold:
            confidence = min(abs(score) / 1.5, 1.0)
            return TradeSignal(
                timestamp=current_time,
                symbol=self.params.get("symbol", "BTC/USDT"),
                action="sell",
                confidence=confidence,
                size=self.params.get("position_size", 1.0),
                strategy_name=self.name,
                metadata={"score": round(score, 3), "reasons": reasons, "rsi": round(rsi, 1)},
            )
        return None


def load_multi_tf_data(symbol: str) -> Dict[str, pd.DataFrame]:
    """Load all timeframes for a symbol, align to 1h index"""
    safe = symbol.replace("/", "_")
    data = {}
    for tf in ["1h", "4h", "1d"]:
        path = os.path.join(DATA_DIR, f"{safe}_{tf}.parquet")
        if os.path.exists(path):
            df = pd.read_parquet(path)
            if tf != "1h":
                # Forward-fill hourly from higher timeframes
                df = df.resample("1h").ffill()
            data[tf] = df
    return data


def compute_metrics(trades: list, initial_capital: float) -> Dict:
    """Compute performance metrics from trade list"""
    if not trades:
        return {"trades": 0, "win_rate": 0, "total_pnl_pct": 0, "sharpe": 0, "max_drawdown": 0}

    buys = {t.trade_id: t for t in trades if t.side == "buy"}
    sells = [t for t in trades if t.side == "sell"]

    pnls = []
    for sell in sells:
        # Match with most recent unmatched buy
        best_buy = None
        for buy_id, buy in buys.items():
            if buy.symbol == sell.symbol and buy.timestamp < sell.timestamp:
                if best_buy is None or buy.timestamp > best_buy.timestamp:
                    best_buy = buy
        if best_buy:
            pnl_pct = (sell.price - best_buy.price) / best_buy.price * 100
            pnls.append(pnl_pct)
            del buys[best_buy.trade_id]

    wins = [p for p in pnls if p > 0]
    total_return = sum(pnls) if pnls else 0

    # Max drawdown from cumulative PnL
    cum = np.cumsum(pnls)
    running_max = np.maximum.accumulate(cum)
    drawdowns = cum - running_max
    max_dd = abs(min(drawdowns)) if len(drawdowns) > 0 else 0

    # Sharpe (annualized, assuming 1h candles)
    if len(pnls) > 1:
        sharpe = np.mean(pnls) / np.std(pnls) * np.sqrt(24 * 365) if np.std(pnls) > 0 else 0
    else:
        sharpe = 0

    return {
        "trades": len(sells),
        "win_rate": len(wins) / len(pnls) if pnls else 0,
        "avg_pnl_pct": np.mean(pnls) if pnls else 0,
        "total_pnl_pct": total_return,
        "max_drawdown_pct": max_dd,
        "sharpe": sharpe,
        "best_trade": max(pnls) if pnls else 0,
        "worst_trade": min(pnls) if pnls else 0,
        "buy_signals": sum(1 for t in trades if t.side == "buy"),
        "sell_signals": sum(1 for t in trades if t.side == "sell"),
    }


async def backtest_symbol(symbol: str, params: Dict = None) -> Dict:
    """Run backtest for a single symbol"""
    data = load_multi_tf_data(symbol)
    if "1h" not in data or len(data["1h"]) < 100:
        return {"symbol": symbol, "error": "insufficient data"}

    df = data["1h"].copy()

    strategy = ConfluenceStrategy(
        f"confluence_{symbol}",
        {**{"symbol": symbol, "position_size": 0.1}, **(params or {})},
    )

    sim = FutureBlindSimulator(initial_capital=10000)
    sim.add_strategy(strategy)

    from agents.historical_data_collector import DataWindow
    window = DataWindow(
        symbol=symbol,
        exchange="binance",
        start_time=df.index[0].to_pydatetime(),
        end_time=df.index[-1].to_pydatetime(),
        current_time=df.index[0].to_pydatetime(),
        data=df,
    )

    result = await sim.run_simulation(window, time_step_minutes=60)
    metrics = compute_metrics(result.trades, sim.initial_capital)

    return {
        "symbol": symbol,
        "candles": len(df),
        "start": str(df.index[0].date()),
        "end": str(df.index[-1].date()),
        "final_balance": round(result.final_balance, 2),
        **metrics,
    }


async def run_parameter_sweep():
    """Test multiple parameter combinations"""
    param_sets = [
        {"signal_threshold": 0.3, "min_alignment": 2, "label": "aggressive"},
        {"signal_threshold": 0.4, "min_alignment": 3, "label": "moderate"},
        {"signal_threshold": 0.5, "min_alignment": 3, "label": "conservative"},
        {"signal_threshold": 0.6, "min_alignment": 4, "label": "strict"},
    ]

    print(f"\n{'='*80}")
    print(f"BACKTEST RESULTS — {len(SYMBOLS)} symbols, 90 days real Binance data")
    print(f"{'='*80}\n")

    for ps in param_sets:
        label = ps.pop("label")
        params = {k: v for k, v in ps.items()}

        print(f"\n── {label.upper()} (threshold={params.get('signal_threshold', 0.4)}, alignment={params.get('min_alignment', 3)}) ──\n")
        print(f"  {'Symbol':12s} {'Candles':>7s} {'Buy':>5s} {'Sell':>5s} {'Trades':>6s} {'Win%':>6s} {'AvgPnL':>8s} {'TotalPnL':>9s} {'MaxDD':>7s} {'Sharpe':>7s}")
        print(f"  {'─'*12} {'─'*7} {'─'*5} {'─'*5} {'─'*6} {'─'*6} {'─'*8} {'─'*9} {'─'*7} {'─'*7}")

        results = []
        for symbol in SYMBOLS:
            r = await backtest_symbol(symbol, params)
            if "error" not in r:
                results.append(r)
                buys = r.get("buy_signals", 0)
                sells = r.get("sell_signals", 0)
                trades = r.get("trades", 0)
                wr = r.get("win_rate", 0) * 100
                avg_pnl = r.get("avg_pnl_pct", 0)
                total_pnl = r.get("total_pnl_pct", 0)
                max_dd = r.get("max_drawdown_pct", 0)
                sharpe = r.get("sharpe", 0)
                print(f"  {r['symbol']:12s} {r['candles']:7d} {buys:5d} {sells:5d} {trades:6d} {wr:5.1f}% {avg_pnl:7.3f}% {total_pnl:8.3f}% {max_dd:6.2f}% {sharpe:7.2f}")

        if results:
            avg_wr = np.mean([r.get("win_rate", 0) for r in results])
            avg_pnl = np.mean([r.get("total_pnl_pct", 0) for r in results])
            avg_sharpe = np.mean([r.get("sharpe", 0) for r in results])
            avg_dd = np.mean([r.get("max_drawdown_pct", 0) for r in results])
            print(f"  {'─'*12} {'─'*7} {'─'*5} {'─'*5} {'─'*6} {'─'*6} {'─'*8} {'─'*9} {'─'*7} {'─'*7}")
            print(f"  {'AVERAGE':12s} {'':>7s} {'':>5s} {'':>5s} {sum(r['trades'] for r in results):6d} {avg_wr*100:5.1f}% {avg_pnl/len(results):7.3f}% {avg_pnl:8.3f}% {avg_dd:6.2f}% {avg_sharpe:7.2f}")

    # Save results
    out_path = os.path.join(DATA_DIR, "..", "backtest_results.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"run_at": datetime.now().isoformat(), "data": results}, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    asyncio.run(run_parameter_sweep())
