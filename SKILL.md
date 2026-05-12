---
name: babymiles-trading-assistant
description: >-
  Comprehensive moomoo OpenAPI trading assistant. Auto-configures environment, queries market data,
  analyzes capital flow/options anomalies, searches news, fetches K-lines, and places orders.
  Supports both real and simulated accounts. Requires moomoo OpenD running.
  
  Naming: Named after the user's identity (BabyMiles) rather than the vendor (moomoo) to keep
  the skill user-centric. All skill content is English-based; conversation with the user remains
  in their preferred language (Chinese).
metadata:
  version: 1.0.0
  author: BabyMiles Trading Bot
  requires:
    - moomoo OpenD (running on 127.0.0.1:11111)
    - Python 3.8+
    - moomoo SDK (pip install moomoo-api)
    - pandas, matplotlib (for K-line charts)
---

# BabyMiles Trading Assistant

## Environment Setup

### 1. Check OpenD Status
```bash
# Check if OpenD is running
ps aux | grep OpenD | grep -v grep

# Check port
netstat -tlnp | grep 11111
```

### 2. Python Environment
```bash
# Must set before running any script
export PYTHONPATH=/usr/local/lib/python3.12/dist-packages:$PYTHONPATH
```

### 3. Check Account Type (Futu vs Moomoo)

**Query account list:**
```bash
cd ~/.hermes/skills/moomooapi
python3 scripts/trade/get_accounts.py --json
```

**Account type identification:**
| Field | Futu | Moomoo |
|-------|------|--------|
| security_firm | `FUTUINC` | `MOOMOO` |
| trd_env | REAL / SIMULATE | REAL / SIMULATE |

**Example output:**
```json
{
  "acc_id": "283445329850596671",
  "trd_env": "REAL",
  "security_firm": "FUTUINC",
  "market": "US"
}
```

### 4. Account Info (Real Account)
- Account ID: `283445329850596671`
- Security Firm: `FUTUINC`
- Market: US
- Trade Env: REAL

## Feature Modules

### A. Market Data

**Get real-time snapshot:**
```bash
cd ~/.hermes/skills/moomooapi
python3 scripts/quote/get_snapshot.py US.TSLA --json
```

**Get K-line data:**
```bash
cd ~/.hermes/skills/moomooapi
python3 scripts/quote/get_kline.py US.TSLA --ktype 1d --num 10 --json
```

**K-line API return format** (note: returns 3 values):
```python
ret, data, page_req_key = quote_ctx.request_history_kline(
    'US.TSLA', start='2026-04-20', end='2026-05-13', ktype='K_DAY'
)
```

### B. Comprehensive Stock Analysis (One-click multi-skill)

**Analyze a single stock:**
```bash
# Standard analysis
python3 ~/.hermes/skills/babymiles-trading-assistant/scripts/analyze_stock.py US.TSLA

# JSON output
python3 ~/.hermes/skills/babymiles-trading-assistant/scripts/analyze_stock.py US.TSLA --json

# Markdown report
python3 ~/.hermes/skills/babymiles-trading-assistant/scripts/analyze_stock.py US.TSLA --report
```

**Analysis dimensions:**
| Dimension | Skill | Content |
|-----------|-------|---------|
| Real-time Quote | moomooapi | Price, change, volume |
| K-line Trend | moomooapi | 10-30 day trend, support/resistance |
| Capital Flow | moomoo-capital-anomaly | Main force in/out, acceleration signals |
| Options Anomaly | moomoo-derivatives-anomaly | Big orders, IV, put/call |
| Options Chain | babymiles-trading-assistant | Strike prices, volume, OI |
| Technical Signals | moomoo-technical-anomaly | Divergence, volume anomalies |
| News Sentiment | moomoo-news-search | Latest news, announcements |

**Sample output:**
```
============================================================
📊 US.TSLA Comprehensive Analysis Report
============================================================

[Real-time Quote]
Price: $433.83 | Change: -2.75% 📉
Open: $440.00 | High: $445.00 | Low: $430.00
Prev Close: $446.10 | Volume: 50,770,000 | Turnover: $21.9B

[K-line Trend]
Last 17 days
Latest: $433.83 | Period High: $449.00 | Period Low: $420.00
MA5: $438.50 | MA10: $425.00
Trend: Bullish alignment 📈

[Capital Flow]
⚠️ Main force net outflow

[Options Anomaly]
📈 Call options active

[Options Chain]
Expiry: 2026-05-15, 2026-05-22

Call Options:
Strike       Price      Volume     OI
---------------------------------------------
$440.00      $12.50     2100       5300
$450.00      $8.20      1800       4100

Put Options:
Strike       Price      Volume     OI
---------------------------------------------
$420.00      $9.30      1500       3200
$410.00      $6.10      1200       2800

[Related News]
1. [05/12] Tesla announces new Model 3 pricing strategy
2. [05/11] Analyst upgrades TSLA to Buy rating
3. [05/10] Tesla deliveries beat expectations in Q2

[Overall Rating] ⭐⭐⭐☆☆
Recommendation: Neutral, hold or wait

============================================================
Analysis Time: 2026-05-13 07:35:00
============================================================
```

### C. Order Placement

**Market order buy (real account):**
```bash
cd ~/.hermes/skills/moomooapi
python3 scripts/trade/place_order.py \
  --code US.VGT \
  --side BUY \
  --quantity 1 \
  --order-type MARKET \
  --trd-env REAL \
  --acc-id 283445329850596671 \
  --security-firm FUTUINC \
  --confirmed
```

**Query order status:**
```bash
cd ~/.hermes/skills/moomooapi
python3 scripts/trade/get_orders.py \
  --trd-env REAL --market US \
  --acc-id 283445329850596671 \
  --security-firm FUTUINC --json
```

### D. Capital Flow Analysis

```bash
cd ~/.hermes/skills/moomoo-capital-anomaly
python3 scripts/handle_capital_anomaly.py US.SMH --json
```

### E. Options Anomaly Analysis

```bash
cd ~/.hermes/skills/moomoo-derivatives-anomaly
python3 scripts/handle_derivatives_anomaly.py US.TSLA --json
```

### F. News Search

**moomoo news:**
```bash
curl -sG 'https://ai-news-search.moomoo.com/news_search' \
  -H 'User-Agent: moomoo-news-search/0.0.2 (Skill)' \
  --data-urlencode 'keyword=TSLA' \
  --data-urlencode 'size=10' \
  --data-urlencode 'news_type=1' \
  --data-urlencode 'lang=en' \
  --data-urlencode 'sort_type=2'
```

**DuckDuckGo search:**
```bash
~/.hermes/skills/research/duckduckgo-search/scripts/duckduckgo.sh "keyword"
```

### G. Portfolio Query

```bash
cd ~/.hermes/skills/moomooapi
python3 scripts/trade/get_portfolio.py \
  --trd-env REAL \
  --market US \
  --acc-id 283445329850596671 \
  --security-firm FUTUINC \
  --json
```

## K-line Charting

**Quick K-line generation:**
```bash
python3 ~/.hermes/skills/babymiles-trading-assistant/templates/draw_kline.py \
  --code US.TSLA --start 2026-04-20 --end 2026-05-13 --output /tmp/tsla_kline.png
```

**Parameters:**
- `--code`: Stock code (e.g. US.TSLA, HK.00700)
- `--start`: Start date (YYYY-MM-DD)
- `--end`: End date (YYYY-MM-DD)
- `--output`: Output image path
- `--ktype`: K-line type (K_DAY, K_WEEK, K_1M, K_5M, etc.)

**K-line API note:**
```python
# request_history_kline returns 3 values!
ret, data, page_req_key = quote_ctx.request_history_kline(
    'US.TSLA', start='2026-04-20', end='2026-05-13', ktype='K_DAY'
)
```

Detailed charting guide in `references/kline-charting.md` (in moomooapi skill).

## Position Query Pitfall

When writing scripts that query positions, **DO NOT pass `acc_id` directly to `position_list_query()`**. This causes `ERROR. Nonexisting acc_id!` for some accounts.

**Wrong:**
```python
trd_ctx = OpenSecTradeContext(filter_trdmarket=TrdMarket.US, ...)
ret, data = trd_ctx.position_list_query(trd_env=TrdEnv.REAL, acc_id='283445329850596671')
```

**Correct (matches get_portfolio.py):**
```python
from common import create_trade_context, parse_trd_env, check_ret, is_empty
ctx = create_trade_context(market='US', security_firm=SecurityFirm.FUTUINC)
ret, data = ctx.position_list_query(trd_env=parse_trd_env('REAL'), refresh_cache=True)
check_ret(ret, data, ctx, "Query positions")
```

### Position Field Mapping

| Concept | API Field Name | Type | Example |
|---------|---------------|------|---------|
| Stock code | `code` | string | `US.VGT` |
| Stock name | `stock_name` | string | `Vanguard Information Technology ETF` |
| Quantity | `qty` | float | `1.0` |
| Can sell qty | `can_sell_qty` | float | `1.0` |
| Average cost | `average_cost` | float | `111.42` |
| Current price | `nominal_price` | float | `112.05` |
| Market value | `market_val` | float | `112.05` |
| Unrealized P/L | `unrealized_pl` | float | `0.63` |
| **P/L ratio** | `pl_ratio_avg_cost` | **percentage** | `0.57` means **+0.57%** |
| Realized P/L | `realized_pl` | float | `0.0` |
| Today P/L | `today_pl_val` | float | `0.63` |

> **Critical**: `pl_ratio_avg_cost` is already a percentage value. `0.57` = +0.57%, NOT +57%. Do NOT multiply by 100.

## Trade Unlock

**Important:** First trade requires unlock. Can use SDK code or OpenD GUI.

### Method 1: SDK Code Unlock (Recommended)
```python
from moomoo import *

pwd_unlock = 'your_trade_password'
trd_ctx = OpenSecTradeContext(
    filter_trdmarket=TrdMarket.US,
    host='127.0.0.1',
    port=11111,
    security_firm=SecurityFirm.FUTUINC  # or SecurityFirm.MOOMOO
)

ret, data = trd_ctx.unlock_trade(pwd_unlock)
if ret == RET_OK:
    print('Unlock successful!')
else:
    print(f'Unlock failed: {data}')

trd_ctx.close()
```

**Notes:**
- `security_firm` must match your account type (FUTUINC or MOOMOO)
- Unlock state is valid for current OpenD instance only
- If OpenD restarts, need to unlock again

### Method 2: OpenD GUI Manual Unlock
1. Open OpenD GUI
2. Click "Unlock Trade" button
3. Enter trade password

### Method 3: Telnet (Does NOT support unlock)
```bash
# Moomoo/Futu OpenD telnet does NOT support unlock_trade command
nc 127.0.0.1 22222
# Type help to see available commands
```

## Security Rules

1. **DO NOT leak** account_id, passwords, or sensitive info
2. **unlock_trade** should be executed by user themselves for security
3. Must add `--confirmed` flag before placing orders
4. Real account operations require caution
5. Ensure `security_firm` matches account type (FUTUINC/MOOMOO)

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| ECONNREFUSED | OpenD not running | `nohup ./OpenD > /tmp/opend.log 2>&1 &` |
| ImportError: cannot import | PYTHONPATH not set | `export PYTHONPATH=/usr/local/lib/python3.12/dist-packages:$PYTHONPATH` |
| Trade not unlocked | unlock_trade not executed | User runs unlock_trade script themselves |
| NumPy version conflict | pandas/numexpr compiled version mismatch | `pip install --upgrade pandas matplotlib --break-system-packages` |
| `position_list_query` returns empty | Passing `acc_id` directly causes `Nonexisting acc_id` error | Use `create_trade_context()` + `refresh_cache=True` without `acc_id`. See `references/moomoo-api-pitfalls.md` |
| P/L ratio display wrong | `pl_ratio_avg_cost` is already a percentage (0.57 = 0.57%), not decimal | Do NOT multiply by 100. See field mapping below. |
| unlock_trade not in telnet | Moomoo OpenD telnet doesn't support unlock | Use Python SDK unlock_trade() |
| OpenD disconnects | Process crashed | Check logs, restart OpenD |

**OpenD restart command:**
```bash
cd /root/moomoo_OpenD_10.5.6508_Ubuntu18.04/moomoo_OpenD_10.5.6508_Ubuntu18.04
nohup ./OpenD > /tmp/moomoo_opend.log 2>&1 &
```

**NumPy compatibility:**
```bash
# If "A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x"
pip install --upgrade pandas matplotlib --break-system-packages
# Or force reinstall
pip install pandas --force-reinstall --break-system-packages
```

## Related Skills

- moomooapi: Basic quotes and trading
- moomoo-capital-anomaly: Capital flow analysis
- moomoo-derivatives-anomaly: Options anomaly detection
- moomoo-news-search: News search
- moomoo-stock-digest: Stock digest
- duckduckgo-search: Web search

## References

- `references/multi-skill-orchestration.md` — How analyze_stock.py aggregates multiple skills
- `references/numpy-compatibility.md` — NumPy 2.x compatibility fixes
- `references/user-preferences.md` — User profile and communication preferences

## Templates

- `templates/draw_kline.py` - K-line chart generation script

## Scripts

- `scripts/analyze_stock.py` - Comprehensive stock analysis (calls multiple skills)