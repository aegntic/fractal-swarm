"""
Walk-Forward Analysis (WFA) for the multi-TF strategy.

Splits 365 days of data into rolling train/test windows.
Trains (optimizes) on the training window, validates on the out-of-sample test window.
Rolls forward and repeats.

This is the gold standard for checking whether a backtested edge is real or overfitted.

Window scheme:
  - 365 days total, split into N folds
  - Each fold: [train_days | test_days] then shift by test_days
  - Default: 60-day train, 30-day test, 15-day step (anchored walk-forward)
  - No overlap between train and test

Metrics per fold:
  - Train: optimize signal_threshold and ATR multipliers on training window
  - Test: apply best params to unseen test window, record OOS performance
  - Report: OOS return, OOS Sharpe, OOS win rate, OOS PF, OOS max DD
  - Aggregate: mean/std of OOS metrics across all folds
"""
import asyncio
import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from itertools import product

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backtesting.future_blind_simulator import (
    FutureBlindSimulator, TradingStrategy, TradeSignal, Trade
)
from agents.historical_data_collector import DataWindow

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "ohlcv")
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]


def load_1h(symbol: str) -> pd.DataFrame:
    """Load 1h data for a symbol."""
    safe = symbol.replace("/", "_")
    path = os.path.join(DATA_DIR, f"{safe}_1h.parquet")
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_parquet(path)


def compute_round_trip_metrics_list(trips: list) -> Dict:
    """Compute performance metrics from round-trip dicts."""
    if not trips:
        return {"round_trips": 0, "win_rate": 0, "total_pnl_pct": 0, "avg_pnl_pct": 0,
                "sharpe": 0, "max_drawdown_pct": 0, "best_trade": 0, "worst_trade": 0,
                "avg_win": 0, "avg_loss": 0, "profit_factor": 0, "avg_hold_hrs": 0,
                "exit_reasons": {}}

    pnls = [r["pnl_pct"] for r in trips]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]

    cum = np.cumsum(pnls)
    running_max = np.maximum.accumulate(cum)
    drawdowns = cum - running_max
    max_dd = abs(min(drawdowns)) if len(drawdowns) > 0 else 0
    sharpe = np.mean(pnls) / np.std(pnls) * np.sqrt(24 * 365) if np.std(pnls) > 0 else 0

    avg_win = np.mean(wins) if wins else 0
    avg_loss = abs(np.mean(losses)) if losses else 0
    pf = avg_win / avg_loss if avg_loss > 0 else float("inf")

    exit_reasons = {}
    for r in trips:
        reason = r.get("exit_reason", "signal")
        exit_reasons[reason] = exit_reasons.get(reason, 0) + 1

    return {
        "round_trips": len(trips),
        "win_rate": len(wins) / len(pnls),
        "total_pnl_pct": sum(pnls),
        "avg_pnl_pct": np.mean(pnls),
        "avg_hold_hrs": np.mean([r["hold_hrs"] for r in trips]),
        "max_drawdown_pct": max_dd,
        "sharpe": sharpe,
        "best_trade": max(pnls),
        "worst_trade": min(pnls),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": pf,
        "exit_reasons": exit_reasons,
    }


async def backtest_window(symbol: str, df: pd.DataFrame, params: Dict) -> Dict:
    """Run backtest on a specific DataFrame window."""
    if len(df) < 250:
        return {"symbol": symbol, "error": "insufficient_data"}

    # Import the strategy class from the backtest script
    # We need to import it here to avoid circular imports
    from scripts.run_backtest_r2 import MultiTFStrategy

    strategy = MultiTFStrategy(
        f"wfa_{symbol}",
        {**{"symbol": symbol}, **params},
    )

    sim = FutureBlindSimulator(initial_capital=10000)
    sim.add_strategy(strategy)

    window = DataWindow(
        symbol=symbol,
        exchange="binance",
        start_time=df.index[0].to_pydatetime(),
        end_time=df.index[-1].to_pydatetime(),
        current_time=df.index[0].to_pydatetime(),
        data=df,
    )

    result = await sim.run_simulation(window, time_step_minutes=60)
    round_trips = strategy.completed_round_trips
    metrics = compute_round_trip_metrics_list(round_trips)

    return {
        "symbol": symbol,
        "candles": len(df),
        "start": str(df.index[0].date()),
        "end": str(df.index[-1].date()),
        **metrics,
    }


async def run_fold(
    fold_num: int,
    train_start: datetime,
    train_end: datetime,
    test_start: datetime,
    test_end: datetime,
    symbols: List[str],
    param_grid: Dict[str, List],
) -> Dict:
    """Run one walk-forward fold: optimize on train, validate on test."""

    # ── Phase 1: Training — find best params on training window ──
    param_combos = list(dict(zip(param_grid.keys(), vals))
                        for vals in product(*param_grid.values()))

    best_params = None
    best_total_pnl = -float("inf")

    for params in param_combos:
        total_pnl = 0.0
        for symbol in symbols:
            full_df = load_1h(symbol)
            if full_df.empty:
                continue
            train_df = full_df[train_start:test_end]  # include test for full sim context
            # Actually we only backtest the TRAIN portion
            train_slice = full_df[train_start:train_end]
            if len(train_slice) < 250:
                continue
            r = await backtest_window(symbol, train_slice, params)
            if "error" not in r:
                total_pnl += r.get("total_pnl_pct", 0)

        if total_pnl > best_total_pnl:
            best_total_pnl = total_pnl
            best_params = params

    # ── Phase 2: Testing — apply best params to unseen test window ──
    test_results = []
    for symbol in symbols:
        full_df = load_1h(symbol)
        if full_df.empty:
            continue
        # For test, we need data from before test_start for indicator warmup
        warmup_start = test_start - timedelta(hours=250)
        test_df = full_df[warmup_start:test_end]
        if len(test_df) < 250:
            continue
        r = await backtest_window(symbol, test_df, best_params)
        if "error" not in r:
            test_results.append(r)

    # Aggregate test metrics
    if not test_results:
        return {"fold": fold_num, "error": "no_test_results"}

    agg = {
        "fold": fold_num,
        "train_period": f"{train_start.date()} to {train_end.date()}",
        "test_period": f"{test_start.date()} to {test_end.date()}",
        "best_params": best_params,
        "train_pnl": round(best_total_pnl, 2),
        "oos_total_pnl": round(sum(r.get("total_pnl_pct", 0) for r in test_results), 2),
        "oos_avg_win_rate": round(np.mean([r.get("win_rate", 0) for r in test_results]) * 100, 1),
        "oos_avg_sharpe": round(np.mean([r.get("sharpe", 0) for r in test_results]), 2),
        "oos_avg_pf": round(np.mean([r.get("profit_factor", 0) for r in test_results
                                     if r.get("profit_factor", 0) != float("inf")]), 2),
        "oos_avg_max_dd": round(np.mean([r.get("max_drawdown_pct", 0) for r in test_results]), 2),
        "oos_total_trades": sum(r.get("round_trips", 0) for r in test_results),
        "oos_per_symbol": {
            r["symbol"]: {
                "pnl": round(r.get("total_pnl_pct", 0), 2),
                "wr": round(r.get("win_rate", 0) * 100, 1),
                "trades": r.get("round_trips", 0),
            }
            for r in test_results
        },
    }
    return agg


async def run_walk_forward(
    train_days: int = 60,
    test_days: int = 30,
    step_days: int = 30,
    symbols: List[str] = None,
    param_grid: Dict[str, List] = None,
):
    """
    Run anchored walk-forward analysis.

    Args:
        train_days: Number of days in each training window
        test_days: Number of days in each test window
        step_days: Step size between folds (in days)
        symbols: Symbols to test (default: all 5)
        param_grid: Parameter combinations to optimize over
    """
    if symbols is None:
        symbols = SYMBOLS
    if param_grid is None:
        # Lean grid around the winning config — enough to validate robustness
        param_grid = {
            "signal_threshold": [0.40, 0.45],
            "min_alignment": [3],
            "take_profit_atr": [5.0, 6.0],
            "stop_loss_atr": [2.5],
            "max_hold_hours": [96],
            "time_decay_hours": [48],
        }

    # Determine data boundaries
    sample_df = load_1h(symbols[0])
    if sample_df.empty:
        print("ERROR: No data found. Run download_ohlcv.py first.")
        return

    data_start = sample_df.index[0].to_pydatetime()
    data_end = sample_df.index[-1].to_pydatetime()
    total_days = (data_end - data_start).days

    print(f"\n{'='*90}")
    print(f"WALK-FORWARD ANALYSIS")
    print(f"Data: {data_start.date()} to {data_end.date()} ({total_days} days)")
    print(f"Window: {train_days}d train / {test_days}d test / {step_days}d step")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Param grid: {len(list(product(*param_grid.values())))} combinations")
    print(f"{'='*90}\n")

    # Generate folds
    folds = []
    current = data_start
    fold_num = 0
    while True:
        train_start = current
        train_end = train_start + timedelta(days=train_days)
        test_start = train_end
        test_end = test_start + timedelta(days=test_days)

        if test_end > data_end:
            break

        folds.append((fold_num, train_start, train_end, test_start, test_end))
        current += timedelta(days=step_days)
        fold_num += 1

    print(f"Generated {len(folds)} folds\n")
    print(f"{'Fold':>4s} {'Train Period':>24s} {'Test Period':>24s} {'Train PnL':>10s} "
          f"{'OOS PnL':>9s} {'OOS WR':>7s} {'OOS Sharpe':>10s} {'OOS PF':>7s} {'OOS DD':>7s} {'Trades':>6s}")
    print(f"{'─'*4} {'─'*24} {'─'*24} {'─'*10} {'─'*9} {'─'*7} {'─'*10} {'─'*7} {'─'*7} {'─'*6}")

    all_folds = []
    for fold_num, train_start, train_end, test_start, test_end in folds:
        print(f"  Processing fold {fold_num}...", end="", flush=True)
        result = await run_fold(
            fold_num, train_start, train_end, test_start, test_end,
            symbols, param_grid
        )
        if "error" not in result:
            all_folds.append(result)
            print(f"\r  {result['fold']:4d} {result['train_period']:>24s} {result['test_period']:>24s} "
                  f"{result['train_pnl']:9.1f}% {result['oos_total_pnl']:8.1f}% "
                  f"{result['oos_avg_win_rate']:6.1f}% {result['oos_avg_sharpe']:9.2f} "
                  f"{result['oos_avg_pf']:6.2f} {result['oos_avg_max_dd']:6.1f}% "
                  f"{result['oos_total_trades']:6d}", flush=True)
        else:
            print(f"\r  {fold_num:4d} SKIPPED: {result.get('error', 'unknown')}", flush=True)

    # ── Aggregate results ──
    if not all_folds:
        print("\nNo valid folds!")
        return

    oos_pnls = [f["oos_total_pnl"] for f in all_folds]
    oos_sharpes = [f["oos_avg_sharpe"] for f in all_folds]
    oos_wrs = [f["oos_avg_win_rate"] for f in all_folds]
    oos_pfs = [f["oos_avg_pf"] for f in all_folds]
    oos_dds = [f["oos_avg_max_dd"] for f in all_folds]

    profitable_folds = sum(1 for p in oos_pnls if p > 0)

    print(f"\n{'='*90}")
    print(f"WALK-FORWARD SUMMARY ({len(all_folds)} folds)")
    print(f"{'='*90}")
    print(f"  Profitable folds:  {profitable_folds}/{len(all_folds)} "
          f"({profitable_folds/len(all_folds)*100:.0f}%)")
    print(f"  Mean OOS PnL:      {np.mean(oos_pnls):.1f}% (±{np.std(oos_pnls):.1f})")
    print(f"  Mean OOS Sharpe:   {np.mean(oos_sharpes):.2f} (±{np.std(oos_sharpes):.2f})")
    print(f"  Mean OOS Win Rate: {np.mean(oos_wrs):.1f}%")
    print(f"  Mean OOS PF:       {np.mean(oos_pfs):.2f}")
    print(f"  Mean OOS Max DD:   {np.mean(oos_dds):.1f}%")
    print(f"  Total OOS PnL:     {sum(oos_pnls):.1f}%")

    # Per-symbol OOS consistency
    all_symbols_oos = {s: [] for s in symbols}
    for f in all_folds:
        for sym, data in f.get("oos_per_symbol", {}).items():
            if sym in all_symbols_oos:
                all_symbols_oos[sym].append(data["pnl"])

    print(f"\n  Per-symbol OOS consistency (positive folds / total folds):")
    for sym in symbols:
        pnls = all_symbols_oos[sym]
        pos = sum(1 for p in pnls if p > 0)
        avg = np.mean(pnls) if pnls else 0
        print(f"    {sym:12s}  {pos}/{len(pnls)} folds profitable  "
              f"avg PnL: {avg:+.1f}%")

    # Robustness verdict
    consistency = profitable_folds / len(all_folds)
    if consistency >= 0.7 and np.mean(oos_pnls) > 0:
        verdict = "✅ STRONG — Strategy edge is robust across market conditions"
    elif consistency >= 0.5 and np.mean(oos_pnls) > 0:
        verdict = "⚠️ MODERATE — Edge exists but inconsistent. Needs refinement"
    elif consistency >= 0.3:
        verdict = "❌ WEAK — Edge is marginal, likely overfitted to full-sample"
    else:
        verdict = "❌ FAILED — No out-of-sample edge detected"

    print(f"\n  VERDICT: {verdict}")

    # Save results
    out_path = os.path.join(DATA_DIR, "..", "walk_forward_results.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({
            "run_at": datetime.now().isoformat(),
            "config": {
                "train_days": train_days,
                "test_days": test_days,
                "step_days": step_days,
                "symbols": symbols,
                "param_grid": {k: v for k, v in param_grid.items()},
            },
            "folds": all_folds,
            "summary": {
                "total_folds": len(all_folds),
                "profitable_folds": profitable_folds,
                "consistency_pct": round(consistency * 100, 1),
                "mean_oos_pnl": round(np.mean(oos_pnls), 2),
                "std_oos_pnl": round(np.std(oos_pnls), 2),
                "mean_oos_sharpe": round(np.mean(oos_sharpes), 2),
                "mean_oos_wr": round(np.mean(oos_wrs), 1),
                "mean_oos_pf": round(np.mean(oos_pfs), 2),
                "total_oos_pnl": round(sum(oos_pnls), 2),
                "verdict": verdict,
            },
            "per_symbol_consistency": {
                sym: {
                    "positive_folds": sum(1 for p in pnls if p > 0),
                    "total_folds": len(pnls),
                    "avg_pnl": round(np.mean(pnls), 2) if pnls else 0,
                }
                for sym, pnls in all_symbols_oos.items()
            },
        }, f, indent=2, default=str)
    print(f"\n  Results saved to {out_path}")


if __name__ == "__main__":
    asyncio.run(run_walk_forward())
