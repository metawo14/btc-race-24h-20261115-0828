"""Washout-recovery bot for make.fun btc-race-24h-20261115-0828.

The bot trades one symbol, CBBTC (Coinbase Wrapped BTC) against USDC, on
1-minute bars, long only, starting with 1,000 USDC of paper money. It speaks
the agent-fun/bars-replay/v1 protocol: the harness sends a hello once, then
one batch per bar, and the bot answers every batch with exactly one reply
carrying its orders. Orders decided on a batch fill at the next bar's open,
so every decision here uses only bars the harness has already sent.

Strategy, in one paragraph: sit in cash until cbBTC capitulates -- its close
falls 4% or more below the highest close of the previous 360 bars (six
hours) -- then buy with all cash. Exit the whole position at +1%
take-profit on its cost, or at -2% stop-loss. One open position at most, one
round trip per washout, at most a handful of trades per day. After a
stop-loss, wait 30 bars before trusting the washout setup again: a stop means
the downtrend is stronger than the setup assumed, and re-buying into the same
falling tape one bar later just repeats the loss. A take-profit exit has no
cooldown -- a fresh washout setup after a win is a new trade, not a repeat of
a failed one.

Why this shape, and why these numbers: a full-size round trip pays about
26 bps in fee (4 bps), slippage (2 bps) and pool impact, while 1-minute noise
is only ~12 bps -- so small wiggles are untradable. Only a real washout,
whose recovery exceeds the round-trip cost by a wide margin, is worth
trading. The numbers were picked by a grid search on the published dev
window (24h, cbBTC -4.0% top to bottom) and cross-checked on the previous
race's dev window (24h, cbBTC -4.9%): the chosen point -- 360-bar high, 4%
dip, +1% take-profit, -2% stop -- is positive on BOTH windows (+$29.04 and
+$9.11 net PnL after every fee, slippage and impact; three round trips on the
dev window, one on the cross-check window; max drawdown about 2%), and it
sits on a flat plateau (dips 3.5-4.0% give the identical trades, stops
1.5-3% never fire, take-profits 0.8-1.2% stay positive on both windows, and
9 of 10 one-step neighbours stay positive on both windows), not a tuned
spike. The tighter +1% take-profit (down from +2%) is what turns the dev
window from a single round trip into three: it banks each recovery before
the tape rolls over again, so the dev PnL no longer rides on one trade.
Trend-following (EMA cross) was tested on the same windows and loses on both;
shallower dips (3% and below) lose on both. The 4% washout is rare, but when
it comes the recovery that follows it is the largest move of the day.

All arithmetic is integer math on the protocol's own units (quote units of
0.000001 USDC, price scale 5, qty scale 8), so the same bars give the same
orders on every run. No randomness, no wall clock, no network, no files
outside this repository.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

SYMBOL = "CBBTC"
# A washout is a close 4% or more below the 360-bar (6-hour) rolling high:
# close * 100 <= high * 96.
LOOKBACK_BARS = 360
DIP_NUM = 96
DIP_DEN = 100
# Take profit at +1% of the position's cost: value * 1000 >= cost * 1010.
TP_NUM = 1010
TP_DEN = 1000
# Stop loss at -2% of the position's cost: value * 100 <= cost * 98.
SL_NUM = 98
SL_DEN = 100
# After a stop-loss exit, wait this many bars before trusting the washout
# setup again.
SL_COOLDOWN_BARS = 30
# Slippage cap, in bps past the latest close the bot was sent.
MAX_SLIPPAGE_BPS = 100
# A buy spends at least 1 USDC (1,000,000 quote units).
MIN_CASH_UNITS = 1_000_000


class WashoutBot:
    """One position at most; buys only capitulation washouts, exits on TP/SL."""

    def __init__(self):
        # Closes of the bars before the current batch, oldest first.
        self.closes = []
        # Bar index of the last stop-loss exit, or None.
        self.last_sl_bar = None

    def _sell(self, qty):
        return {"side": "sell", "symbol": SYMBOL, "qty": qty,
                "max_slippage_bps": MAX_SLIPPAGE_BPS}

    def _buy(self, cash):
        return {"side": "buy", "symbol": SYMBOL,
                "notional_quote_units": cash,
                "max_slippage_bps": MAX_SLIPPAGE_BPS}

    def _cooled_down(self):
        return (self.last_sl_bar is None
                or len(self.closes) - self.last_sl_bar >= SL_COOLDOWN_BARS)

    def on_batch(self, state, batch):
        if state.warming_up:
            return []
        bar = None
        for b in batch["bars"]:
            if b["symbol"] == SYMBOL:
                bar = b
                break
        if bar is None:
            return []  # a gap minute: CBBTC has no bar in this batch
        close = int(bar["c"])

        orders = []
        held = state.positions.get(SYMBOL)
        if held is not None and held.qty > 0:
            value = state.value(SYMBOL, held.qty)
            if value * TP_DEN >= held.cost * TP_NUM:
                orders.append(self._sell(held.qty))
            elif value * SL_DEN <= held.cost * SL_NUM:
                self.last_sl_bar = len(self.closes)
                orders.append(self._sell(held.qty))
        elif (len(self.closes) >= LOOKBACK_BARS
                and state.cash >= MIN_CASH_UNITS
                and self._cooled_down()):
            high = max(self.closes[-LOOKBACK_BARS:])
            if close * DIP_DEN <= high * DIP_NUM:
                orders.append(self._buy(state.cash))

        self.closes.append(close)
        return orders


makefun_bars.run(WashoutBot().on_batch)
