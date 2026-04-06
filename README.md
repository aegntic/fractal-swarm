# Fractal Swarm Trader

Autonomous crypto strategy optimization system. Uses multi-timeframe confluence analysis on Binance data with walk-forward validation, overnight grid search optimization, and paper trading with real market data.

**No real money trades.** Research/backtesting/paper-trading only.

## What It Does

1. **Night Shift** — Every midnight AEST, GitHub Actions runs a fully autonomous optimization pipeline:
   - Expanding-window walk-forward analysis (9 folds, 36-day test windows)
   - Coarse grid search (~30K parameter combinations per symbol)
   - Fine refinement + Darwinian evolutionary optimization
   - Three-layer overfitting detection (IS-OOS gap, consistency, fragility)
   - BB Mean Reversion strategy search
   - Configurable param sweep experiments
   - Full-simulator validation with fees + slippage
   - Self-awareness: discrepancy detection between fast and full simulators
   - Structured morning report committed to repo

2. **Paper Trader** — Runs 24/7, polls Binance for real-time 1h candles, tracks hypothetical positions:
   - ADX regime filter (only enter when ADX > 25)
   - Per-symbol optimized configs (SOL uses night-shift-optimized params)
   - State persistence across restarts
   - Fee + slippage simulation

3. **Self-Correction Loop** — Three independent modules that detect when the evaluation layer is wrong:
   - `evaluator_calibration.py` — compares fast sim vs full sim on random configs
   - `discrepancy_detector.py` — flags symbols where fast/full sim disagree
   - Phase 8 in night shift — runs discrepancy detection automatically

## Architecture

```
Binance ──► OHLCV parquet (data/ohlcv/)
                │
                ▼
    ┌───────────┴───────────────────┐
    │   per_symbol_optimizer.py    │  ◄── Fast sim (indicator-based)
    │   compute_indicators()       │      Used by night_shift grid search
    │   simulate_trades()          │
    │   compute_metrics()          │
    └───────────┬───────────────────┘
                │
    ┌───────────┼───────────────────┐
    │           │                   │
    ▼           ▼                   ▼
paper_trader  night_shift    validate_night_shift
  (live)     (grid search)   (full sim bridge)
                │                   │
                ▼                   ▼
    ┌───────────────────────────────────┐
    │    FutureBlindSimulator          │  ◄── Full sim (fees + slippage)
    │    0.1% fees, 10bps slippage     │      Ground truth for validation
    └───────────────────────────────────┘
                │
                ▼
    data/night_results/YYYY-MM-DD/
    ├── report.md          # morning report
    ├── summary.json        # machine-readable results
    └── full_sim_validation.json
```

## Project Structure

```
fractal-swarm/
├── scripts/
│   ├── night_shift.py              # Autonomous overnight optimizer (main pipeline)
│   ├── paper_trader.py             # Live paper trading engine
│   ├── per_symbol_optimizer.py     # Fast indicator-based simulator + scoring
│   ├── validate_night_shift.py     # Full-sim validation bridge
│   ├── evaluator_calibration.py    # Fast/full sim calibration module
│   ├── discrepancy_detector.py     # Post-run discrepancy detection
│   ├── run_backtest_r2.py          # Production MultiTFStrategy class
│   ├── night_config.json           # Night shift configuration
│   ├── download_ohlcv.py           # Binance data fetcher
│   └── ...                         # WFA, regime filter, etc.
├── backtesting/
│   └── future_blind_simulator.py   # Fee-aware full simulator
├── agents/
│   └── historical_data_collector.py # DataWindow for full simulator
├── data/
│   ├── ohlcv/                      # Binance OHLCV parquet files (committed to repo)
│   ├── night_results/               # Night shift output reports
│   ├── paper_trading/               # Paper trader state + logs
│   ├── calibration/                # Evaluator calibration reports
│   └── discrepancies/              # Discrepancy detection history
├── .github/workflows/
│   └── night_shift.yml             # CI: runs night shift at 14:00 UTC
└── tests/                          # Unit tests
```

## Commands

```bash
# Paper trading
python scripts/paper_trader.py

# Night shift (locally)
python scripts/night_shift.py --skip-fetch
python scripts/night_shift.py --symbols SOL/USDT

# Validate candidates through full simulator
python scripts/validate_night_shift.py --production

# Calibration check
python scripts/evaluator_calibration.py --samples 10

# Discrepancy detection
python scripts/discrepancy_detector.py
```

## Active Symbols & Performance

All validated through FutureBlindSimulator (0.1% fees, 10bps slippage):

| Symbol | Production PnL | Optimized PnL | Consistency | Trades |
|--------|---------------|--------------|-------------|--------|
| SOL/USDT | +36.9% | **+118.3%** | 78% | 429 |
| BNB/USDT | +49.6% | — | 67% | 178 |
| ETH/USDT | +48.1% | — | 78% | 155 |
| BTC/USDT | +17.5% | — | 67% | 153 |

## CI/CD

- **Night shift**: GitHub Actions at 14:00 UTC (midnight AEST), auto-commits results
- **Tests**: pytest on push, flake8 linting
- **Binance is geo-blocked on GitHub runners** — OHLCV data is committed to repo, `--skip-fetch` is default

## Fast Sim Calibration (Critical)

The fast simulator (`per_symbol_optimizer`) is used for the 30K-combo grid search. It MUST match the full simulator exactly on these three points:

1. **ATR = std(returns, 20h) × price** — NOT True Range. Wrong ATR = 1.6x wider stops = false negatives
2. **MR entry uses daily trend only** — `rsi < 35 and daily_bullish`, NOT all-3-TF alignment
3. **Sharpe uses actual trade frequency** — `sqrt(n_trades / total_hours × 8760)`, NOT 1 trade/hour

See `CLAUDE.md` for the full design rationale.

## Roadmap

- [x] Multi-TF confluence strategy with ADX regime filter
- [x] Night shift autonomous optimizer (grid + WFA + overfitting detection)
- [x] Paper trader with live Binance data
- [x] Fast sim calibration (ATR, MR, Sharpe)
- [x] Self-correction modules (calibration + discrepancy detection)
- [x] Full-sim validation pipeline
- [ ] Auto-deploy validated configs to paper trader
- [ ] Per-regime configs (BTC works in trends, not ranges)
- [ ] Multi-strategy portfolio (BB Mean Reversion + MultiTF confluence)
- [ ] Solana migration (architecture port, not code port)

## License

MIT
