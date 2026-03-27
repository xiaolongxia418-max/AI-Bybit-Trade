# AI Bybit Trade

Want to become a trading pro, but confused by complex technical analysis and overwhelming market noise?

**Now you can train your own AI Agent.**

Let it learn your trading strategy, monitor markets 24/7, identify entry points, and execute trades automatically.

No more staring at screens. No more guessing the market.

---

## What Can It Do?

### 📈 Trading
Spot, futures, leverage — all controlled by AI.
```python
ai.buy("BTC/USDT:USDT", 0.001, stop_loss=67000, take_profit=70000)
```

### 💰 Earn
Put idle funds into Earn automatically and earn interest.
```python
ai.lending_purchase("USDT", 100)
```

### 🔄 Transfer
Move funds between accounts with one command.
```python
ai.transfer("USDT", 50, "SPOT", "LINEAR")
```

### 🔍 Query
Balance, positions, prices — always at your fingertips.
```python
ai.balance()
ai.positions()
ai.price("BTC/USDT:USDT")
```

---

## Why Use It?

| Trading Yourself | AI Agent Does It |
|------------------|------------------|
| ❌ Sleep = miss opportunities | ✅ 24/7 automated trading |
| ❌ Emotions affect decisions | ✅ Follows discipline |
| ❌ Reactions too slow | ✅ Millisecond execution |
| ❌ Manual trading is tiring | ✅ Earn while you sleep |

---

## 🎁 Free Download + Bybit Bonus

This Skill is completely free.

If you want to support the developer, use this referral link to register on Bybit:

👉 https://www.bybit.com/invite?ref=YD4AAG5

With this link, you get:
- ✅ Up to **$6,135** in rewards
- ✅ Deposit $100 → Get $10
- ✅ Complete first trade → Get $15
- ✅ Up to 30% trading fee rebate

---

## Supported Features

| Category | Functions |
|----------|-----------|
| **Trading** | buy, sell, close, set_leverage, cancel, DCA, Grid |
| **Earn** | lending_purchase, lending_redeem, lending_balance |
| **Loan** | loan_borrow, loan_repay, loan_adjust_ltv, loan_balance |
| **Transfer** | transfer, flash_transfer, deposit_address, withdraw |
| **Query** | balance, positions, price, order_book, wallet |

---

## Quick Start

```bash
pip install -r requirements.txt
export BYBIT_API_KEY="your_key"
export BYBIT_API_SECRET="your_secret"
```

```python
from ai_bybit_trade import AIBybit

ai = AIBybit()

# AI decides → Execute trade
ai.buy("BTC/USDT:USDT", 0.001,
       stop_loss=67000,
       take_profit=70000)
```

---

## Version

**v2.0.0** - Full version with all major features

---

## Warning

⚠️ Cryptocurrency trading involves risk. AI decisions may result in losses. Trade responsibly.

---

## Support This Project

If you want to support the developer, here's the referral link:

👉 https://www.bybit.com/invite?ref=YD4AAG5
