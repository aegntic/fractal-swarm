# Night Shift Design: Zero-Token Autonomous Strategy Optimization

> **Status:** Implementation in progress
> **Created:** 2026-04-03
> **Inspired by:** [karpathy/autoresearch](https://github.com/karpathy/autoresearch) + [chrisworsey55/atlas-gic](https://github.com/chrisworsey55/atlas-gic)

## The Problem With Current Approach

Looking at `backtest_history` in `production_config.json`:

```
WFA_opt:    -1.8% OOS    ← overfitted (optimized per fold)
WFA_fixed:  +5.6%/window ← real edge (fixed params, no peeking)
WFA_ADX:    +5.9%/window ← real edge + regime filter
```

The original `autoresearch.py` (commit `44d9d46`) had a **6% keep rate** and ran only 50 iterations on rolling windows that **overlap** — each "independent" fold shares 85% of its data with neighbors. That's not real out-of-sample validation. The configs were already near-optimal for in-sample, and the script couldn't distinguish real improvement from noise.

Token waste: each gnhf session burns tokens reading outputs, deciding next steps, generating code, debugging. For mechanical parameter sweeps, this is like using a supercomputer to add numbers.

## Design Philosophy

```
Night (0 tokens, ~8 hours):  Mechanical exploration → structured data
Day  (~5K tokens, ~1 hour):  Strategic interpretation → code changes
```

The night shift is a **single deterministic Python script**. No LLM. No decisions. Just math. It does the 99% perspiration so your daytime session can focus on the 1% inspiration.

---

## Architecture: `scripts/night_shift.py`

```
┌─────────────────────────────────────────────────────────┐
│                    NIGHT_SHIFT.PY                        │
│                   (zero LLM tokens)                      │
│                                                         │
│  Phase 1: Data Refresh (2 min)                          │
│    ├─ Fetch latest 365d 1h OHLCV from Binance           │
│    ├─ Compute indicators (RSI, BB, ATR, ADX, momentum)  │
│    └─ Classify regime per 30-day window                  │
│                                                         │
│  Phase 2: Expanding-Window WFA (3 min)                  │
│    ├─ 10 non-overlapping test folds                     │
│    ├─ Train on [0, fold_start], test on [fold_start..]  │
│    └─ Each data point tested OOS exactly once            │
│                                                         │
│  Phase 3: Exhaustive Grid Search (2 min)                │
│    ├─ ~5,760 combos per symbol                          │
│    ├─ Each evaluated on all 10 WFA folds                │
│    └─ Overfitting score computed per candidate           │
│                                                         │
│  Phase 4: Darwinian Refinement (20 min, 5 generations)  │
│    ├─ Take top 20 from grid search                      │
│    ├─ Perturb ±5-15% around each parent                 │
│    ├─ WFA validate all children                         │
│    └─ Survivor selection with overfitting penalty        │
│                                                         │
│  Phase 5: Regime Analysis (1 min)                       │
│    ├─ Per-regime performance breakdown                   │
│    ├─ Correlation matrix changes                        │
│    └─ New opportunity detection                          │
│                                                         │
│  Phase 6: Morning Report (instant)                      │
│    └─ Write data/night_results/YYYY-MM-DD/report.md     │
└─────────────────────────────────────────────────────────┘
```

**Total runtime: ~30 minutes.** The rest of the 8 hours is idle (or looping Darwinian refinement with fresh perturbations). Cron it at midnight, report is ready by 12:45 AM.

---

## The Critical Fix: Proper WFA

Non-overlapping expanding-window WFA:

```
Data: [═══════════════════════════════════════════════] 365 days

Fold 1:  [TRAIN====][TEST]                                 train: 0-72d, test: 72-108d
Fold 2:  [TRAIN============][TEST]                         train: 0-144d, test: 144-180d
Fold 3:  [TRAIN==================][TEST]                   train: 0-216d, test: 216-252d
Fold 4:  [TRAIN========================][TEST]             train: 0-288d, test: 288-324d
Fold 5:  [TRAIN==============================][TEST]       train: 0-360d, test: 360-365d
```

**Key properties:**
- Every data point is OOS exactly **once** — no double-counting
- Expanding train window mimics real deployment (more history over time)
- No look-ahead bias possible — train never includes test data
- Test periods are 36 days each (long enough for ~10-30 trades per symbol)

---

## Overfitting Detection: Three-Layer Defense

### Layer 1: IS-OOS Sharpe Gap

```python
overfitting_score = (IS_Sharpe - OOS_Sharpe) / max(abs(IS_Sharpe), 0.01)

# < 0.2  → healthy (IS and OOS are close)
# 0.2-0.5 → mild overfit (acceptable with other strong signals)
# > 0.5  → likely overfit → REJECT
```

### Layer 2: OOS Consistency

```python
# What % of folds have positive OOS Sharpe?
oos_consistency = count(OOS_Sharpe > 0) / num_folds

# Current baseline: 55-57% (from WFA_fixed/WFA_ADX)
# Requirement: >= 50% (at least half the folds must be profitable)
```

### Layer 3: Parameter Sensitivity

```python
# For the best config, perturb each param ±10%
# If any single perturbation causes Sharpe to drop >40% → fragile/overfit

sensitivity = {}
for param in config:
    for delta in [-0.10, +0.10]:
        perturbed = {**config, param: config[param] * (1 + delta)}
        perturbed_sharpe = evaluate(perturbed)
        sensitivity[param] = max(abs(perturbed_sharpe - baseline) / baseline)

fragility = max(sensitivity.values())
# fragility > 0.4 → likely fitting to noise, not signal
```

---

## Ranking Formula: The Survivor Score

```python
SURVIVOR_SCORE = (
    OOS_Sharpe                          # raw return signal
    * OOS_Consistency                   # stability across time
    * (1 - clamp(Overfitting_Score, 0, 1))  # penalize overfitting
    / (1 + MaxDD_OOS / 100)            # risk-adjusted
    * min(Trades_Per_Fold / 15, 1.0)   # require statistical significance
)
```

Naturally selects for configs that:
- Have real OOS edge (Sharpe > 0)
- Work across different market conditions (consistency)
- Aren't fitting to noise (low overfitting score)
- Don't blow up (reasonable max drawdown)
- Trade enough to be meaningful (not 2 lucky trades)

---

## Parameter Search Space

Two-stage approach to manage combinatorial explosion:

### Stage 1: Coarse Grid (~30K combos, ~30 seconds)

```python
GRID = {
    "signal_threshold":    [0.30, 0.33, 0.35, 0.38, 0.40, 0.43, 0.45, 0.50],
    "take_profit_atr":     [3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 7.0],
    "stop_loss_atr":       [1.0, 1.25, 1.5, 2.0, 2.5, 3.0],
    "max_hold_hours":      [36, 48, 72, 96, 120],
    "time_decay_hours":    [12, 24, 36, 48],
    "trailing_stop_atr":   [0.0, 1.0],     # coarse: on/off
    "score_flip_delay_hrs": [0, 2],         # coarse: on/off
}
# 8 × 8 × 6 × 5 × 4 × 2 × 2 = 30,720 combos
```

### Stage 2: Fine Refinement (~2.5K combos, ~3 seconds)

Around top 100 from Stage 1:
```python
"trailing_stop_atr":   [0.0, 0.5, 0.8, 1.0, 1.2, 1.5],
"score_flip_delay_hrs": [0, 1, 2, 3, 4],
```

### Stage 3: Darwinian (5 generations × 50 candidates, ~1 second)

Top 50 from Stage 2, random perturbation ±5-15%, Survivor Score selection.

**Total computation: ~35 seconds.**

---

## Night Config: `data/night_config.json`

```json
{
  "version": "1.0",
  "schedule": {
    "fetch_fresh_data": true,
    "max_hours_runtime": 8
  },
  "symbols": ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"],
  "wfa": {
    "num_folds": 10,
    "test_fold_days": 36,
    "min_trades_per_fold": 10
  },
  "grid_search": {
    "coarse": true,
    "fine_refinement_top_n": 100,
    "darwinian_generations": 5,
    "darwinian_population": 50
  },
  "overfitting": {
    "max_is_oos_gap": 0.5,
    "min_oos_consistency": 0.50,
    "max_fragility": 0.4
  },
  "regime_analysis": {
    "adx_threshold": 25.0,
    "volatility_percentile_window": 60
  },
  "experiments": [
    {
      "name": "trailing_stop_sweep",
      "type": "param_override",
      "params": {"trailing_stop_atr": [0.0, 0.5, 0.8, 1.0, 1.2, 1.5, 2.0]}
    },
    {
      "name": "regime_conditional_sl",
      "type": "conditional",
      "condition": "adx > 25",
      "param_overrides": {"stop_loss_atr": 3.5},
      "else_overrides": {"stop_loss_atr": 1.5}
    }
  ],
  "output_dir": "data/night_results"
}
```

The `experiments` array is where daytime strategic thinking plugs in. Code a hypothesis ("maybe wider stops in trending markets"), add it to the config, and the night shift tests it rigorously.

---

## Morning Report Format

Generated at `data/night_results/YYYY-MM-DD/report.md` with sections:
1. **Market State** — regime, ADX, volatility percentile, correlations
2. **Production Baseline** — current config OOS metrics across all folds
3. **Top 10 Candidates** — ranked by Survivor Score with full metrics + deltas
4. **Overfitting Warnings** — rejected configs and why
5. **Regime Analysis** — per-regime performance breakdown
6. **Comparison to Previous Night** — trend tracking
7. **Action Items** — prioritized recommendations with confidence levels

---

## Daytime Workflow

```
08:00  Read report.md                        (~500 tokens in)
08:05  Ask LLM: "What should I prioritize?"   (~1K tokens)
08:10  LLM suggests prioritized actions       (~1K tokens out)
08:15  Code the change (gnhf session)        (~3K tokens)
08:30  Add new experiment to night_config.json
08:35  Commit, push. Done until tomorrow.
```

**Total daytime tokens: ~5.5K** vs current approach of 30-100K+ for manual exploration.

---

## Anti-Overfit Summary

| Approach | Result | Why |
|----------|--------|-----|
| WFA_opt (optimize per fold) | **-1.8% OOS** | Params fit to noise in each fold |
| WFA_fixed (no optimization) | **+5.6%/window** | Params are robust by coincidence |
| **Night Shift** | **?** | Proper validation + overfitting detection |

Key differences from current `autoresearch.py`:

| Current | Night Shift |
|---------|-------------|
| 50 iterations | 30K+ evaluations |
| Rolling windows (85% overlap) | Expanding window (0% overlap) |
| Single objective (Sharpe) | Composite Survivor Score |
| No overfitting detection | 3-layer defense |
| No regime analysis | Per-regime breakdown |
| stdout only | Structured report + JSON |
| Manual state management | Automatic, idempotent |
| No data refresh | Fresh Binance data nightly |

---

## Implementation Next Steps

- [x] **Step 1:** Build core WFA engine — expanding-window folds with IS/OOS split
- [x] **Step 2:** Port grid search — reuse `per_symbol_optimizer.py` logic, evaluate through WFA folds
- [x] **Step 3:** Add overfitting layers — IS-OOS gap, consistency, sensitivity (fragility as penalty, not rejection)
- [x] **Step 4:** Generate morning report — structured markdown + JSON
- [ ] **Step 5:** Wire up cron — `0 0 * * * python scripts/night_shift.py`

## Implementation Notes

### Design Decisions Made During Implementation

1. **Coarse pass uses single 720-bar window (not WFA folds)** — 30K combos × 1 window = 30K evaluations in ~25s. The coarse pass is just a fast filter to eliminate obviously bad configs.

2. **Fine refinement re-evaluates on ALL WFA folds** — top 100 from coarse get 30 fine-grained variants each (1500 total), evaluated on all 9 folds. This is where the real validation happens.

3. **Fragility is a weighted penalty, not a hard rejection** — During testing, fragility > 0.4 rejected 100% of fine candidates. Changed to `survivor *= 1/(1+fragility)` so fragile-but-profitable configs still surface with lower confidence. The inverse formula ensures survivor is always non-negative for positive-Sharpe configs.

4. **`is_coarse_only` flag prevents single-window results from contaminating final rankings** — The report only shows candidates validated on 5+ WFA folds.

5. **Production baseline is force-evaluated on all folds** — Added Phase 2b that runs the production config through full WFA before any grid search, ensuring an apples-to-apples comparison.

6. **Per-fold Sharpe winsorized at ±100** — With 2 trades, `compute_metrics` can produce Sharpe >8000 (std≈0, annualized by sqrt(8760)). Winsorizing prevents single-fold outliers from destroying aggregate metrics.

7. **Median OOS Sharpe instead of mean** — Mean is dominated by outliers (e.g., 9 folds with Sharpe [-44, -24, -13, +2, +17, +18, +31, +55, +8563] → mean=+956). Median gives +17, which honestly represents typical performance.

8. **Production baseline preservation** — Phase 3 grid search no longer overwrites `all_results`, preserving Phase 2b's production baseline evaluation.

### Performance

- **SOL single symbol, 9 folds, 36d test**: ~29 min (1765s)
- **All 4 symbols, 9 folds, 36d test**: ~136 min (estimated)
- **Bottleneck**: Fine refinement (9 folds × 1500 candidates × 7-11 evals each)
- **Coarse pass**: ~25s per symbol (30K combos on 720-bar window)
- **Darwinian**: ~2 min per generation per symbol

### Key Findings from Test Runs

- **SOL** consistently outperforms — 100% OOS consistency, survivor ~16.8, median Sharpe ~+19
- **BTC** — survivor scores were inflated to ~300 by a single 2-trade fold with Sharpe +8563; fixed by winsorization + median
- **Production config** actually performs decently (median OOS Sharpe +10.04, 56% consistency) — the previous report showed -50 because mean was dragged by outlier negative folds
- **ETH** — no candidates pass coarse filter; the strategy may need fundamental adaptation for ETH
- **BNB** — coarse-only results were misleading (high survivor but only 14 trades/fold)
