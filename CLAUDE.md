# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A crypto backtesting and paper trading system with automated overnight strategy optimization. Uses multi-timeframe confluence analysis on hourly Binance data with walk-forward validation to avoid overfitting. The production strategy (MultiTFStrategy) is validated on 365d data with 47-fold WFA.

**This is a research/backtesting/paper-trading project.** No real money trades. The `_archive/` and `worldmonitor/` directories are unrelated to the active system — ignore them unless explicitly asked about them.

## Commands

```bash
# Paper trading (live Binance data, no real trades)
python scripts/paper_trader.py

# Night shift — overnight parameter optimization (no LLM, pure math)
python scripts/night_shift.py                      # defaults (4 symbols, 9 folds)
python scripts/night_shift.py --skip-fetch         # use cached data
python scripts/night_shift.py --symbols SOL/USDT   # single symbol

# Validate night shift candidates through FutureBlindSimulator
python scripts/validate_night_shift.py
python scripts/validate_night_shift.py --symbol SOL/USDT --top 3

# Download OHLCV data from Binance (no API key needed)
python scripts/download_ohlcv.py

# Run backtests
python scripts/run_backtest_r2.py                  # production MultiTFStrategy
python scripts/wfa_fixed_params.py                 # 47-fold walk-forward analysis

# Tests
pytest

# Lint (CI runs these)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

## Architecture

### Data Flow

```
Binance → download_ohlcv.py → data/ohlcv/{SYMBOL}_1h.parquet
                                   ↓
              per_symbol_optimizer (compute_indicators, simulate_trades, _compute_score)
                                   ↓
              ┌──────────────┬────────────────────┐
              │              │                    │
         paper_trader   run_backtest_r2      night_shift
         (live poll)    (full simulator)    (grid search + WFA)
              │              │                    │
              └──────────────┴────────────────────┘
                                   ↓
                        knowledge_base/production_config.json
                        data/night_results/YYYY-MM-DD/report.md
```

### Key Files

- **`backtesting/future_blind_simulator.py`** — `TradingStrategy` ABC, `FutureBlindSimulator`, `TradeSignal`, `Trade`, `SimulationResult`. The ABC requires implementing `async analyze(data, current_time) -> Optional[TradeSignal]`. Applies 0.1% fees, 10bps slippage, max 20% position size.

- **`scripts/run_backtest_r2.py`** — Production `MultiTFStrategy` class + `timeframe_signal()` helper (exported and used by paper_trader). Score-based entry (0–1.0 range) from multi-TF trend alignment (0.4), mean reversion/RSI (0.3), momentum (0.15), Bollinger Bands (0.15), volume bonus (+0.1).

- **`scripts/per_symbol_optimizer.py`** — Fast indicator-based simulation. Exports `compute_indicators()`, `simulate_trades()`, `compute_metrics()`, `_compute_score()`. Used by night_shift for speed. Computes all indicators (RSI, BB, ATR, ADX, momentum) as DataFrame columns.

- **`scripts/night_shift.py`** — Overnight optimization. Expanding-window WFA (non-overlapping folds), coarse grid search (~30K combos), fine refinement, Darwinian evolution. Three-layer overfitting detection (IS-OOS gap, consistency, fragility). Generates structured morning reports.

- **`scripts/paper_trader.py`** — Live paper trader. Polls Binance 1h candles every 60s, runs the same score logic as the backtest. ADX regime filter (only enter when ADX > 25). State persists to `data/paper_trading/state.json`. Has per-symbol params (SOL uses night-shift-optimized config, others use production defaults).

- **`scripts/validate_night_shift.py`** — Bridges the two evaluation paths: takes night shift candidates (fast indicator sim) and validates them through the full `FutureBlindSimulator` (with fees/slippage).

- **`agents/historical_data_collector.py`** — `DataWindow` class that feeds OHLCV data to the simulator.

- **`knowledge_base/production_config.json`** — Single source of truth for active config, WFA results, symbols, regime filter settings.

- **`knowledge_base_schema.py`** — Data structures: `StrategyGenome`, `KnowledgeBase` for saving/loading strategies.

### Validation Pipeline

1. **Backtest** on 365d data → must show positive PnL, PF > 1.0
2. **Walk-Forward Analysis** — 47 rolling 30-day windows, 7-day step (fixed params, no per-fold optimization)
3. **ADX Regime Filter** — only enter when ADX > 25 (reduces variance 29%, +31.7% PnL)
4. **Night Shift** — expanding-window WFA + grid search + overfitting detection
5. **Simulator Validation** — confirm edge survives fees + slippage in FutureBlindSimulator

### Active Symbols

- BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT
- XRP/USDT was dropped (net negative across all WFA folds)

### Production Strategy Parameters

| Param | Default | SOL (night-shift optimized) |
|-------|---------|---------------------------|
| signal_threshold | 0.40 | 0.35 |
| take_profit_atr | 6.0 | 4.0 |
| stop_loss_atr | 2.5 | 1.25 |
| max_hold_hours | 96 | 36 |
| time_decay_hours | 48 | 41 |
| trailing_stop_atr | 1.0 | 0.70 |
| score_flip_delay_hrs | 2 | 1 |

### Full-Sim Validation Results (2026-04-05, fees + slippage)

| Symbol | Production PnL | Optimized PnL | Consistency | Trades |
|--------|---------------|--------------|-------------|--------|
| SOL | +36.9% | **+118.3%** | 78% | 429 |
| BNB | +49.6% | — | 67% | 178 |
| ETH | +48.1% | — | 78% | 155 |
| BTC | +17.5% | — | 67% | 153 |

### Key Design Decisions

- **Fast sim must match full sim exactly** — the fast sim (`per_symbol_optimizer`) approximates the full sim (`FutureBlindSimulator`). Critical invariants:
  - **ATR = std(returns, 20h) × price** — NOT True Range. Using wrong ATR caused 1.6x wider stops and rejected profitable configs.
  - **MR condition uses daily trend only** — `rsi < 35 and daily_bullish`, NOT all-3-TF alignment.
  - **Sharpe uses actual trade frequency** — `sqrt(n_trades / total_hours × 8760)`, not assume 1 trade/hour.
- **Median OOS Sharpe** (not mean) for aggregate metrics — prevents single-fold outliers from dominating.
- **Per-fold Sharpe winsorized at ±100** — with few trades, Sharpe can go to ±8000+ via annualization.
- **Fragility is a penalty, not a hard rejection** — formula: `survivor *= 1/(1+fragility)`.
- **Self-correction modules**: `evaluator_calibration.py` and `discrepancy_detector.py` run after each night shift to catch fast/full sim divergence.

### Self-Correction Architecture (Phase 3)

Three independent modules, all testable without LLM:
1. **`scripts/evaluator_calibration.py`** — compares fast vs full sim on random configs, maintains correction table
2. **`scripts/discrepancy_detector.py`** — post-night-shift check, flags symbols where evaluation is unreliable, skips Darwinian for persistently flagged symbols
3. **`scripts/night_shift.py` Phase 8** — runs discrepancy detection automatically after validation

## Data

- `data/ohlcv/{SYMBOL}_{TF}.parquet` — Binance OHLCV, 1h/4h/1d timeframes, ~365 days
- `data/night_results/YYYY-MM-DD/report.md` — morning reports from night shift
- `data/paper_trading/state.json` — paper trader state (survives restarts)

## CI/CD

- **Night shift**: GitHub Actions cron at 14:00 UTC (midnight AEST), commits results to repo
- **Tests**: `pytest` on push to master, Python 3.9–3.11, flake8 linting
- **Workflow files**: `.github/workflows/night_shift.yml`, `.github/workflows/python-tests.yml`

## Autonomous Agent Workflow

The `AGENT_PROMPT.md` file describes the workflow for an AI research agent:
1. Read the framework (TradingStrategy ABC, existing MultiTFStrategy)
2. Implement a new strategy in `scripts/strategies/research_{name}.py`
3. Backtest on 365d data across all symbols
4. Walk-forward validate if initial results are positive
5. Commit findings (even failures) with clear messages
6. Never push to remote, only commit locally on `gnhf/strategy-research` branch