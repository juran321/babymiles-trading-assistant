# BabyMiles Trading Assistant

A Hermes Agent skill for moomoo OpenAPI trading — market data, position monitoring, auto stop-loss/take-profit, and one-click liquidation.

## Features

| Script | Purpose |
|--------|---------|
| `analyze_stock.py` | Comprehensive stock analysis: real-time quote, K-line trend, capital flow, options chain, news, and rating |
| `auto_stop_loss_take_profit.py` | Monitor positions and auto-sell when stop-loss or take-profit thresholds are hit |
| `liquidate_all.py` | One-click sell all positions at market price |
| `draw_kline.py` | Generate K-line (candlestick) charts |

## Prerequisites

```bash
# 1. Install moomoo OpenD
#    Download: https://www.moomoo.com/download/OpenAPI

# 2. Configure your account in OpenD.xml, then start OpenD
#    <login_account>YOUR_ACCOUNT</login_account>
#    <login_pwd>YOUR_PASSWORD</login_pwd>

# 3. Install Python SDK
pip install moomoo-api

# 4. Test connection (reads market data & positions)
python3 ~/.hermes/skills/moomooapi/scripts/trade/get_portfolio.py --json
```

> **Trading (buy/sell/stop-loss/liquidate) requires `unlock_trade`.** Market data and position queries work without it. Run unlock only when you need to place orders.

## Install

### Option 1: Natural Language (Recommended for Hermes Agent)

Simply tell your Hermes Agent:

```
Install the babymiles-trading-assistant skill
```

Or:

```
Install this skill for me: https://github.com/juran321/babymiles-trading-assistant
```

Hermes Agent will automatically run:
```bash
hermes skills install https://github.com/juran321/babymiles-trading-assistant/blob/main/SKILL.md
```

### Option 2: Hermes CLI

```bash
hermes skills install https://github.com/juran321/babymiles-trading-assistant/blob/main/SKILL.md
```

Or install by skill name if published to the hub:
```bash
hermes skills search babymiles
hermes skills install babymiles-trading-assistant
```

### Option 3: Manual Clone

```bash
cd ~/.hermes/skills
git clone https://github.com/juran321/babymiles-trading-assistant.git
```

### Option 4: Claude Code

In Claude Code, add this repository as a skill source:

```bash
# Add the repo as a skill tap
claude skills tap add https://github.com/juran321/babymiles-trading-assistant

# Then install the skill
claude skills install babymiles-trading-assistant
```

Or manually clone to Claude Code's skills directory:

```bash
cd ~/.claude/skills  # or wherever Claude Code stores skills
git clone https://github.com/juran321/babymiles-trading-assistant.git
```

Then reference the skill in your Claude Code session:
```
Use the babymiles-trading-assistant skill to analyze TSLA
```

### 2. Configure moomoo OpenD

1. **Set your moomoo account credentials** in `OpenD.xml`:

```xml
<login_account>YOUR_MOOMOO_ACCOUNT</login_account>
<login_pwd>YOUR_PASSWORD</login_pwd>
```

2. **Create the skill config** at `~/.hermes/skills/moomooapi/scripts/config.yaml` (or use the [moomooapi skill](https://www.moomoo.com/skillhub/openapi)):

```yaml
opend:
  host: "127.0.0.1"
  port: 11111
  telnet_port: 22222

trading:
  default_market: "US"
  trd_env: "REAL"      # or "SIMULATE" for paper trading
  security_firm: "FUTUINC"
```

3. **Unlock trade** after OpenD starts (required for placing orders):

```python
from moomoo import OpenSecTradeContext, SecurityFirm
from moomoo.trade.trade_unlock import TradeUnlock

ctx = OpenSecTradeContext(filter_trdmarket=TrdMarket.US, host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUINC)
ret, data = ctx.unlock_trade(password='YOUR_TRADE_PASSWORD', password_md5=None)
print('Unlock result:', ret, data)
ctx.close()
```

Or use the moomooapi skill's unlock helper.

### 3. Verify OpenD is running and unlocked

```bash
python3 ~/.hermes/skills/moomooapi/scripts/trade/get_portfolio.py --json
```

## Usage

### Analyze a stock

```bash
python3 ~/.hermes/skills/babymiles-trading-assistant/scripts/analyze_stock.py US.TSLA
```

### Auto stop-loss / take-profit (dry-run first)

```bash
# Monitor all positions, default -5% stop-loss / +10% take-profit
python3 ~/.hermes/skills/babymiles-trading-assistant/scripts/auto_stop_loss_take_profit.py --monitor --dry-run

# Run as daemon (auto-sell when thresholds hit)
python3 ~/.hermes/skills/babymiles-trading-assistant/scripts/auto_stop_loss_take_profit.py --daemon --interval 60

# Custom thresholds for a specific stock
python3 ~/.hermes/skills/babymiles-trading-assistant/scripts/auto_stop_loss_take_profit.py --code US.TSLA --stop-loss 8 --take-profit 15
```

### Liquidate all positions

```bash
# Preview what will be sold
python3 ~/.hermes/skills/babymiles-trading-assistant/scripts/liquidate_all.py --dry-run

# Execute (requires confirmation)
python3 ~/.hermes/skills/babymiles-trading-assistant/scripts/liquidate_all.py --confirmed

# Force sell without confirmation (use with caution)
python3 ~/.hermes/skills/babymiles-trading-assistant/scripts/liquidate_all.py --force

# Sell only one stock
python3 ~/.hermes/skills/babymiles-trading-assistant/scripts/liquidate_all.py --code US.VGT --confirmed
```

## Skill Integration (Hermes Agent)

Once installed in `~/.hermes/skills/`, Hermes Agent can invoke these scripts automatically:

```
User: "Analyze TSLA for me"
Agent: Runs analyze_stock.py and returns formatted report

User: "Set stop-loss at -3% for my positions"
Agent: Runs auto_stop_loss_take_profit.py with custom thresholds

User: "Sell everything"
Agent: Runs liquidate_all.py --dry-run first, asks for confirmation
```

## Safety Notes

- All trading scripts require `--confirmed` or `--force` to execute actual orders
- `--dry-run` mode previews actions without placing orders
- Auto stop-loss/take-profit runs locally and polls at the specified interval
- Real trading environment (`REAL`) is default — use `SIMULATE` for testing

## License

MIT
