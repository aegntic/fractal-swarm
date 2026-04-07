# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

A crypto backtesting and paper trading system with automated overnight strategy optimization. Uses multi-timeframe confluence analysis on hourly Binance data with walk-forward validation. The production strategy (MultiTFStrategy) generates scores from trend alignment (1h/4h/1d), mean reversion (RSI), momentum, and Bollinger Bands.

**This is a research/backtesting/paper-trading project.** No real money trades.

- **`_archive/`** and **`worldmonitor/`** are unrelated to the active system — ignore them.
- **`knowledge_base/`** has legacy config/schema code not actively used.

## Quick Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install pandas numpy ccxt pyarrow redis

# Paper trading (runs 24/7, polls Binance 1h candles)
PYTHONUNBUFFERED=1 nohup python scripts/paper_trader.py >> data/paper_trading/paper_trader.log 2>&1 &

# Night shift locally
python scripts/night_shift.py --skip-fetch

# Full-sim validation
python scripts/validate_night_shift.py --production
```

## Commands

```bash
# Paper trading
python scripts/paper_trader.py

# Night shift
python scripts/night_shift.py                      # defaults (4 symbols, 9 folds)
python scripts/night_shift.py --skip-fetch         # use cached data
python scripts/night_shift.py --symbols SOL/USDT   # single symbol

# Validation
python scripts/validate_night_shift.py --production           # production + candidates
python scripts/validate_night_shift.py --symbol SOL/USDT --top 3

# Self-correction modules
python scripts/evaluator_calibration.py --samples 20            # calibrate fast vs full sim
python scripts/evaluator_calibration.py --fast-only             # quick diversity check
python scripts/discrepancy_detector.py                           # check latest night results

# Data
python scripts/download_ohlcv.py                   # fetch from Binance (no API key needed)
```

## Architecture

### Data Flow

```
Binance → download_ohlcv.py → data/ohlcv/{SYMBOL}_1h.parquet (committed to repo)
                                   ↓
              per_symbol_optimizer (compute_indicators, simulate_trades, _compute_score)
              ┌────────────────┴────────────────┐
              │                                 │
         night_shift (grid search)         paper_trader (live)
         fast sim (~30K combos)            real-time Binance
              │                                 │
              ▼                                 ▼
    ┌─────────────────┐                 data/paper_trading/
    │ validate_       │                   state.json
    │ night_shift.py  │
    │ (full sim bridge)│
    └────────┬────────┘
             │
             ▼
    FutureBlindSimulator (fees + slippage)
             │
             ▼
    data/night_results/YYYY-MM-DD/report.md
```

### Key Files

| File | Purpose |
|------|---------|
| `scripts/night_shift.py` | Main pipeline: grid search → WFA → Darwinian → report → validation → discrepancy check |
| `scripts/per_symbol_optimizer.py` | Fast simulator: `compute_indicators()`, `simulate_trades()`, `compute_metrics()`, `_compute_score()` |
| `scripts/paper_trader.py` | Live paper trader: polls Binance, ADX filter, per-symbol configs |
| `scripts/validate_night_shift.py` | Bridges fast sim → full sim for candidate validation |
| `scripts/run_backtest_r2.py` | Production `MultiTFStrategy` class + `timeframe_signal()` helper |
| `scripts/evaluator_calibration.py` | Compares fast vs full sim on random configs, outputs calibration report |
| `scripts/discrepancy_detector.py` | Post-night-shift check, flags symbols where fast/full sim disagree |
| `scripts/night_config.json` | Night shift configuration (symbols, folds, experiments, thresholds) |
| `backtesting/future_blind_simulator.py` | `FutureBlindSimulator`: 0.1% fees, 10bps slippage, max 20% position |
| `agents/historical_data_collector.py` | `DataWindow` class feeding data to full simulator |

### Validation Pipeline

1. **Night shift fast sim** — coarse grid (~30K combos) → fine refinement → Darwinian evolution
2. **Three-layer overfitting detection** — IS-OOS gap, OOS consistency, parameter fragility
3. **Full-sim validation** — top candidates through FutureBlindSimulator (fees + slippage)
4. **Discrepancy detection** — compare fast/full sim rankings, flag divergent symbols
5. **Paper trading** — live market validation with real Binance data

### Active Symbols

BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT. XRP was dropped (net negative across all WFA folds).

### Strategy Parameters

| Param | Production | SOL Optimized |
|-------|-----------|--------------|
| signal_threshold | 0.40 | 0.35 |
| take_profit_atr | 6.0 | 4.0 |
| stop_loss_atr | 2.5 | 1.25 |
| max_hold_hours | 96 | 36 |
| time_decay_hours | 48 | 41 |
| trailing_stop_atr | 1.0 | 0.70 |
| score_flip_delay_hrs | 2 | 1 |

### Full-Sim Validation Results (2026-04-05)

| Symbol | Production PnL | Optimized PnL | Consistency | Trades |
|--------|---------------|--------------|-------------|--------|
| SOL | +36.9% | **+118.3%** | 78% | 429 |
| BNB | +49.6% | — | 67% | 178 |
| ETH | +48.1% | — | 78% | 155 |
| BTC | +17.5% | — | 67% | 153 |

## Critical: Fast Sim Calibration

The fast simulator (`per_symbol_optimizer`) is used for the 30K-combo grid search. It MUST match the full simulator exactly. Three invariants were discovered the hard way:

1. **ATR formula**: `std(returns, 20h) × price` — NOT True Range. Wrong ATR made stops 1.6x wider, causing BTC to show -16% instead of +3%.
2. **MR entry condition**: `rsi < 35 and daily_trend == bullish` — NOT `bull_count >= min_alignment`. The fast sim was requiring all 3 TFs bullish (much rarer).
3. **Sharpe annualization**: `sqrt(n_trades / total_hours × 8760)` — NOT `sqrt(24 × 365)`. The old formula assumed 1 trade/hour (actual is ~0.01), overstating Sharpe by ~10x.

If you change anything in `_compute_score()` or `simulate_trades()`, run `evaluator_calibration.py` with a small full-sim sample to verify the fast sim still agrees directionally.

## Night Shift Pipeline Phases

1. **Phase 1: Data** — load cached parquet (Binance geo-blocked on GitHub, data is committed to repo)
2. **Phase 2: WFA Folds** — expanding-window, non-overlapping, 9 folds × 36-day test windows
3. **Phase 2b: Production Baseline** — evaluate current config as reference
4. **Phase 3: Coarse Grid** — ~30K parameter combinations per symbol
5. **Phase 3b: Fine Refinement** — top 100 per symbol on all folds
6. **Phase 4: Darwinian Evolution** — 5 generations, mutate best candidates
7. **Phase 4b: BB Mean Reversion** — separate strategy grid search (Bollinger Band bounce)
8. **Phase 4c: Custom Experiments** — configurable param sweeps from `night_config.json`
9. **Phase 5: Regime Analysis** — ADX, volatility percentile, correlations
10. **Phase 6: Morning Report** — markdown + JSON report with top candidates and action items
11. **Phase 7: Auto-Validation** — top 3 candidates through full FutureBlindSimulator
12. **Phase 8: Discrepancy Detection** — compare fast/full sim, flag divergent symbols

## Self-Correction Architecture

Three independent modules (no LLM needed):

1. **`evaluator_calibration.py`** — runs on N random configs, measures sign agreement and PnL correlation between fast and full sim
2. **`discrepancy_detector.py`** — post-night-shift, tracks consecutive flags per symbol, skips Darwinian after 2 consecutive bad nights
3. **Phase 8 in night_shift.py** — calls discrepancy detector automatically

Output: `data/calibration/` and `data/discrepancies/`

## CI/CD

- **Night shift**: GitHub Actions cron at 14:00 UTC (midnight AEST), also supports `workflow_dispatch`
- **Binance is geo-blocked on GitHub runners** — OHLCV data lives in repo under `data/ohlcv/`, `fetch_fresh_data` defaults to `false`
- **Data refresh**: run `download_ohlcv.py` locally, commit updated parquets, push before midnight
- **Workflow**: `.github/workflows/night_shift.yml` (300 min timeout, Python 3.12)
- **Dependencies in CI**: `pandas numpy ccxt pyarrow redis`

## GitHub Access

- **Remote**: `git@github.com:tradewife/fractal-swarm.git` (SSH)
- **PAT stored**: `~/.config/gh/config.yml` (for `workflow_dispatch` triggers)
- **Trigger manually**: `curl -X POST -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/repos/tradewife/fractal-swarm/actions/workflows/night_shift.yml/dispatches -d '{"ref":"master"}'`

## Design Decisions

- **Median OOS Sharpe** (not mean) — prevents single-fold outliers from dominating
- **Per-fold Sharpe winsorized at ±100** — prevents tiny-sample Sharpe from going to ±8000+
- **Fragility is a penalty, not rejection** — `survivor *= 1/(1+fragility)`
- **Survivor Score**: `avg_oos_sharpe × consistency × (1-overfitting) × dd_factor × trade_factor × fragility_penalty`
- **Paper trader has no Redis dependency** for runtime (only the full sim validation path needs it)
- **Virtual environment**: `.venv/` with Python 3.13.3, ccxt 4.5.46, pandas 3.0.2
