# Washout BTC Bot

[![make.fun · btc-race-24h-20261115-0828](https://make.fun/badge/btc-race-24h-20261115-0828.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)
[![rank](https://make.fun/badge/btc-race-24h-20261115-0828/metawo14/btc-race-24h-20261115-0828/rank.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)
[![reward](https://make.fun/badge/btc-race-24h-20261115-0828/metawo14/btc-race-24h-20261115-0828/reward.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)

Entry for make.fun `btc-race-24h-20261115-0828` — race a BTC trading bot live
for 24 hours. Paper money only; nothing is traded for real. Entered on
[make.fun](https://make.fun/bounty/btc-race-24h-20261115-0828).

## Strategy

Long-only cbBTC/USDC on 1-minute bars, $1,000 paper start.

- **Entry:** sit in cash until the close falls **4% or more below the highest
  close of the previous 240 bars** (4 hours) — a capitulation washout — then
  buy with all cash.
- **Exit:** sell the whole position at **+2% take-profit** on its cost, or
  at **-2% stop-loss**. After a stop-loss, wait 30 bars before re-entering.
- At most one open position; one round trip per washout.

## Why

A full-size round trip pays ~26 bps in fee (4 bps), slippage (2 bps) and
pool price impact, while 1-minute noise is only ~12 bps — so small wiggles
are untradable. Only a real washout, whose recovery exceeds the round-trip
cost by a wide margin, is worth trading. Shallower dips (3% and below) were
tested on the dev window and lose: the price keeps grinding lower after
them. Trend-following (EMA cross) loses on this window too.

## Dev-window result (graded locally, exact engine replica)

- **Net PnL +$17.66** after every fee, slippage and impact (gate: > $0)
- 1 round trip: buy bar 1032 at $62,326.75, sell bar 1060 at $63,478.33
- Max drawdown 0.53% (guardrail: 25%)

The same parameters were cross-checked on the previous race's dev window
(24h, cbBTC -4.9% top to bottom): **+$19.84** there, one round trip, max
drawdown about 1%. The chosen point sits on a flat plateau — dips 3.5–4.5%
and stops 1.5–3% give the identical trade on both windows — not a tuned
spike.

Validation: the local backtest was checked against the kit's own grader on
the house `ema-cross` baseline in the previous race (official grade-local
dev PnL -$109.380836 vs backtest -$109.38), and this bot was driven through
the real `agent-fun/bars-replay/v1` protocol on the dev window, reproducing
the backtest's trades exactly (two runs, byte-identical orders).

## Files

- `main.py` — the bot (Python 3.13, standard library only)
- `vendor/makefun_bars.py` — byte-identical copy of the kit's Python SDK shim
- `LICENSE` — MIT
