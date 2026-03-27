# AI Bybit Trade - Ultimate Edition

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-Proprietary-red)
![Bybit](https://img.shields.io/badge/Bybit-Crypto-orange)
[![GitHub stars](https://img.shields.io/github/stars/crayfish316-oss/ai-bybit-trade)](https://github.com/crayfish316-oss/ai-bybit-trade/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/crayfish316-oss/ai-bybit-trade)](https://github.com/crayfish316-oss/ai-bybit-trade/network)

**Train your own AI Agent for fully automated crypto trading.**

---

Want to become a trading pro, but confused by complex technical analysis and overwhelming market noise?

Now you can train your own AI Agent, let it learn your trading strategy, and have it monitor markets 24/7, identify entries, and execute trades automatically.

**No more staring at screens. No more guessing.**

---

## Get Started

### Free Download + Bybit Bonus

👉 **Register on Bybit with this link:**
https://www.bybit.com/invite?ref=YD4AAG5

| Reward | Amount |
|--------|--------|
| Sign up | $10 USDC |
| Deposit $100 | $10 |
| Complete first trade | $15 |
| Trading fee rebate | Up to 30% |

---

## Features

### 📈 Trading Automation
```python
# Open long
ai.buy("BTC/USDT:USDT", 0.001,
       stop_loss=67000,
       take_profit=70000)

# Open short
ai.sell("ETH/USDT:USDT", 0.1,
         stop_loss=2100,
         take_profit=1950)

# Close position
ai.close("BTC/USDT:USDT")
ai.close_all()  # Close all positions
```

### 💰 Automated Earn
```python
# Put USDT into Earn for interest
ai.lending_purchase("USDT", 100)

# Redeem
ai.lending_redeem("USDT", 50)
```

### 🔄 Account Transfer
```python
# Spot → Futures
ai.transfer("USDT", 100, "SPOT", "LINEAR")

# Futures → Spot
ai.transfer("USDT", 50, "LINEAR", "SPOT")
```

### 🔍 Query Functions
```python
ai.balance()           # USDT balance
ai.total_balance()      # Total balance (including positions)
ai.price("BTC/USDT:USDT")  # Real-time price
ai.positions()          # All positions
ai.open_orders()        # Pending orders
ai.order_book("BTC/USDT:USDT")  # Order book
```

---

## Complete Function Reference

### Trading Functions
| Function | Description |
|----------|-------------|
| `buy(symbol, amount, sl, tp)` | Open long |
| `sell(symbol, amount, sl, tp)` | Open short |
| `close(symbol)` | Close position |
| `close_all()` | Close all positions |
| `set_leverage(symbol, lev)` | Set leverage (1-125x) |
| `cancel_order(id, symbol)` | Cancel order |
| `cancel_all_orders(symbol)` | Cancel all orders |
| `dca(symbol, amount, n, dir)` | Dollar cost averaging |
| `grid_orders(symbol, lo, hi, n, amt)` | Grid orders |

### Transfer Functions
| Function | Description |
|----------|-------------|
| `transfer(coin, amt, from, to)` | Internal transfer |
| `flash_transfer(coin, amt, to_uid, to_type)` | Flash transfer |
| `deposit_address(coin, network)` | Get deposit address |
| `withdraw(coin, amt, addr, network, tag)` | Withdraw |

### Earn Functions
| Function | Description |
|----------|-------------|
| `lending_purchase(coin, amt)` | Purchase earn product |
| `lending_redeem(coin, amt, auto)` | Redeem from earn |
| `lending_balance(coin)` | Earn balance |

### Loan Functions
| Function | Description |
|----------|-------------|
| `loan_borrow(coin, amt, col_coin, col_amt)` | Borrow against crypto |
| `loan_repay(order_id, coin, amt)` | Repay loan |
| `loan_adjust_ltv(order_id, col_amt, borrow_amt)` | Adjust LTV |
| `loan_balance()` | Loan positions |

### Account Functions
| Function | Description |
|----------|-------------|
| `balance(coin)` | Balance query |
| `total_balance(coin)` | Total balance |
| `price(symbol)` | Price query |
| `positions(symbol)` | Position query |
| `wallet_balance(type)` | Wallet balance |
| `all_balances()` | All coin balances |

---

## AI Agent Usage Examples

### Example 1: Trend Following
```python
ai = AIBybit()

# AI analyzes and decides to enter
if ai_analysis_says_bullish():
    ai.buy("BTC/USDT:USDT", 0.001,
           stop_loss=calculate_support(),
           take_profit=calculate_resistance())
```

### Example 2: DCA Strategy
```python
# AI decides to accumulate gradually
ai.dca("BTC/USDT:USDT",
        amount=100,      # Total 100 USDT
        intervals=4,     # Split into 4 buys
        direction="buy")
```

### Example 3: Auto Earn
```python
# Put idle USDT into Earn
idle = ai.balance("USDT")
if idle > 50:
    ai.lending_purchase("USDT", idle * 0.8)
```

### Example 4: Position Management
```python
# AI continuously monitors
positions = ai.positions()
for pos in positions:
    if pos['unrealized_pnl'] < -10:
        # Loss exceeds $10, stop loss
        ai.close(pos['symbol'])
```

---

## Installation

```bash
pip install -r requirements.txt
```

Set environment variables:
```bash
export BYBIT_API_KEY="your_api_key"
export BYBIT_API_SECRET="your_api_secret"
```

Or in code:
```python
ai = AIBybit(
    api_key="your_api_key",
    api_secret="your_api_secret"
)
```

---

## API Permissions

| Function | Required Permission |
|----------|-------------------|
| Trading, Query | Spot / Futures trading |
| Transfer | Account Transfer |
| Withdraw | Withdrawal |

Recommended: Enable "Spot + Futures + Transfer" permissions when creating your Bybit API key.

---

## FAQ

**Q: Is this Skill safe?**
A: Your API key is only used for trading within your own Bybit account. All operations stay in your account.

**Q: How do I train the AI Agent?**
A: This Skill provides execution functions. The AI's training depends on your AI Agent platform (e.g., OpenClaw).

**Q: How much capital do I need?**
A: Recommended minimum is $100 USDT to start trading.

---

## Bybit Referral Link

👉 https://www.bybit.com/invite?ref=YD4AAG5

---

## Warning

⚠️ Cryptocurrency trading involves risk. AI decisions may result in significant losses. Trade responsibly.
