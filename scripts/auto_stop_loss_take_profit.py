#!/usr/bin/env python3
"""
BabyMiles Auto Stop-Loss / Take-Profit Script
Monitors positions and automatically places orders when thresholds are hit

Usage:
    # Monitor all positions with default thresholds (stop-loss -5%, take-profit +10%)
    python3 auto_stop_loss_take_profit.py --monitor

    # Monitor specific stock with custom thresholds
    python3 auto_stop_loss_take_profit.py --code US.TSLA --stop-loss 0.05 --take-profit 0.15

    # Dry-run mode (show what would happen without placing orders)
    python3 auto_stop_loss_take_profit.py --monitor --dry-run

    # Daemon mode (runs continuously, checking every 60 seconds)
    python3 auto_stop_loss_take_profit.py --monitor --daemon --interval 60
"""

import sys
import json
import time
import argparse
import subprocess
from datetime import datetime

sys.path.insert(0, '/usr/local/lib/python3.12/dist-packages')

from moomoo import OpenQuoteContext, OpenSecTradeContext, TrdSide, OrderType, TrdEnv, TrdMarket, SecurityFirm, RET_OK

# Account config
ACC_ID = '283445329850596671'
SECURITY_FIRM = SecurityFirm.FUTUINC
TRD_ENV = TrdEnv.REAL
TRD_MARKET = TrdMarket.US


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def get_positions():
    """Get current positions using create_trade_context (matches get_portfolio.py)"""
    import os
    sys.path.insert(0, os.path.expanduser('~/.hermes/skills/moomooapi/scripts'))
    from common import create_trade_context, parse_trd_env, parse_security_firm, check_ret, is_empty

    trd_env = parse_trd_env('REAL')
    security_firm = parse_security_firm('FUTUINC')

    ctx = create_trade_context(market='US', security_firm=security_firm)
    try:
        ret, data = ctx.position_list_query(trd_env=trd_env, refresh_cache=True)
        check_ret(ret, data, ctx, "Query positions")

        positions = []
        if not is_empty(data):
            for i in range(len(data)):
                row = data.iloc[i] if hasattr(data, "iloc") else data[i]
                positions.append({
                    'code': row.get('code', '') if hasattr(row, 'get') else getattr(row, 'code', ''),
                    'name': row.get('stock_name', '') if hasattr(row, 'get') else getattr(row, 'stock_name', ''),
                    'quantity': float(row.get('qty', 0)) if hasattr(row, 'get') else float(getattr(row, 'qty', 0)),
                    'can_sell': float(row.get('can_sell_qty', 0)) if hasattr(row, 'get') else float(getattr(row, 'can_sell_qty', 0)),
                    'avg_cost': float(row.get('average_cost', 0)) if hasattr(row, 'get') else float(getattr(row, 'average_cost', 0)),
                    'market_val': float(row.get('market_val', 0)) if hasattr(row, 'get') else float(getattr(row, 'market_val', 0)),
                    'pl_val': float(row.get('unrealized_pl', 0)) if hasattr(row, 'get') else float(getattr(row, 'unrealized_pl', 0)),
                    'pl_ratio': float(row.get('pl_ratio_avg_cost', 0)) if hasattr(row, 'get') else float(getattr(row, 'pl_ratio_avg_cost', 0)),
                })
        return positions
    finally:
        ctx.close()


def get_snapshot(symbol):
    """Get real-time price"""
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    ret, data = quote_ctx.get_market_snapshot([symbol])
    quote_ctx.close()

    if ret != 0 or data is None:
        return None

    row = data.iloc[0]
    return {
        'last_price': float(row.get('last_price', 0)),
        'change_pct': float(row.get('change_rate', 0)),
    }


def place_market_order(symbol, side, quantity, dry_run=False):
    """Place a market order"""
    side_str = "SELL" if side == TrdSide.SELL else "BUY"

    if dry_run:
        log(f"[DRY-RUN] Would place {side_str} order: {quantity} x {symbol}")
        return True

    trd_ctx = OpenSecTradeContext(
        filter_trdmarket=TRD_MARKET,
        host='127.0.0.1', port=11111,
        security_firm=SECURITY_FIRM
    )

    ret, data = trd_ctx.place_order(
        price=0,  # Market order
        qty=quantity,
        code=symbol,
        trd_side=side,
        order_type=OrderType.MARKET,
        trd_env=TRD_ENV,
        acc_id=ACC_ID
    )

    trd_ctx.close()

    if ret == RET_OK:
        log(f"✅ Order placed: {side_str} {quantity} x {symbol}")
        return True
    else:
        log(f"❌ Order failed: {data}")
        return False


def check_and_execute(pos, stop_loss_pct, take_profit_pct, dry_run=False):
    """Check thresholds and execute if hit"""
    symbol = pos['code']
    avg_cost = pos['avg_cost']
    pl_ratio = pos['pl_ratio']
    can_sell = pos['can_sell']

    if avg_cost <= 0 or can_sell <= 0:
        return False

    # pl_ratio is already a percentage (e.g., -5 for -5%)
    current_pl = pl_ratio

    log(f"{symbol}: Avg Cost ${avg_cost:.2f}, P/L: {current_pl:.2f}%, Can Sell: {can_sell}")

    # Check stop-loss
    if current_pl <= -stop_loss_pct:
        log(f"🚨 STOP-LOSS TRIGGERED for {symbol}! P/L: {current_pl*100:.2f}% (threshold: -{stop_loss_pct*100:.1f}%)")
        return place_market_order(symbol, TrdSide.SELL, can_sell, dry_run)

    # Check take-profit
    if current_pl >= take_profit_pct:
        log(f"🎯 TAKE-PROFIT TRIGGERED for {symbol}! P/L: {current_pl*100:.2f}% (threshold: +{take_profit_pct*100:.1f}%)")
        return place_market_order(symbol, TrdSide.SELL, can_sell, dry_run)

    return False


def monitor_positions(stop_loss_pct, take_profit_pct, interval=60, dry_run=False, target_code=None):
    """Monitor positions continuously"""
    log("=" * 60)
    log("BabyMiles Auto Stop-Loss / Take-Profit Monitor")
    log(f"Stop-Loss: -{stop_loss_pct*100:.1f}% | Take-Profit: +{take_profit_pct*100:.1f}%")
    log(f"Mode: {'DRY-RUN' if dry_run else 'LIVE'}")
    log("=" * 60)

    while True:
        positions = get_positions()

        if not positions:
            log("No positions found.")
        else:
            log(f"Checking {len(positions)} position(s)...")

            for pos in positions:
                if target_code and pos['code'] != target_code:
                    continue
                check_and_execute(pos, stop_loss_pct, take_profit_pct, dry_run)

        if interval <= 0:
            break

        log(f"Sleeping {interval}s...")
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description='BabyMiles Auto Stop-Loss / Take-Profit')
    parser.add_argument('--monitor', action='store_true', help='Monitor positions')
    parser.add_argument('--code', type=str, help='Target stock code (e.g. US.TSLA)')
    parser.add_argument('--stop-loss', type=float, default=0.05, help='Stop-loss threshold (decimal, default: 0.05 = 5%)')
    parser.add_argument('--take-profit', type=float, default=0.10, help='Take-profit threshold (decimal, default: 0.10 = 10%)')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds (default: 60)')
    parser.add_argument('--daemon', action='store_true', help='Run continuously')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without placing orders')
    args = parser.parse_args()

    if not args.monitor:
        parser.print_help()
        return

    interval = args.interval if args.daemon else 0

    try:
        monitor_positions(
            stop_loss_pct=args.stop_loss,
            take_profit_pct=args.take_profit,
            interval=interval,
            dry_run=args.dry_run,
            target_code=args.code
        )
    except KeyboardInterrupt:
        log("\n👋 Monitor stopped by user.")


if __name__ == '__main__':
    main()
