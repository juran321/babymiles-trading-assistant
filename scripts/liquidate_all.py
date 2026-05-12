#!/usr/bin/env python3
"""
BabyMiles One-Click Liquidate All Positions
Sells all holdings at market price

Usage:
    # Show what would be sold (dry-run)
    python3 liquidate_all.py --dry-run

    # Liquidate all positions (requires --confirmed)
    python3 liquidate_all.py --confirmed

    # Liquidate specific stock only
    python3 liquidate_all.py --code US.SMH --confirmed

    # Force liquidate (no confirmation prompt)
    python3 liquidate_all.py --confirmed --force
"""

import sys
import json
import argparse
from datetime import datetime

sys.path.insert(0, '/usr/local/lib/python3.12/dist-packages')

from moomoo import OpenSecTradeContext, TrdSide, OrderType, TrdEnv, TrdMarket, SecurityFirm, RET_OK

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


def place_market_sell(symbol, quantity, dry_run=False):
    """Place market sell order"""
    if dry_run:
        log(f"[DRY-RUN] Would sell {quantity} x {symbol}")
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
        trd_side=TrdSide.SELL,
        order_type=OrderType.MARKET,
        trd_env=TRD_ENV,
        acc_id=ACC_ID
    )

    trd_ctx.close()

    if ret == RET_OK:
        log(f"✅ SOLD: {quantity} x {symbol}")
        return True
    else:
        log(f"❌ FAILED to sell {symbol}: {data}")
        return False


def liquidate_all(dry_run=False, target_code=None, force=False):
    """Liquidate all positions"""
    positions = get_positions()

    if not positions:
        log("No positions to liquidate.")
        return

    # Filter if target specified
    if target_code:
        positions = [p for p in positions if p['code'] == target_code]
        if not positions:
            log(f"Position {target_code} not found.")
            return

    log("=" * 60)
    log("BabyMiles Liquidation Report")
    log("=" * 60)

    total_market_val = 0
    total_pl = 0

    log("\nPositions to liquidate:")
    log(f"{'Symbol':<15} {'Name':<20} {'Qty':<8} {'Avg Cost':<12} {'P/L %':<10} {'Market Val':<12}")
    log("-" * 80)

    for pos in positions:
        code = pos['code']
        name = pos['name'][:18]
        qty = pos['can_sell']
        avg = pos['avg_cost']
        pl_pct = pos['pl_ratio']  # Already percentage (0.57 means 0.57%)
        mkt_val = pos['market_val']

        total_market_val += mkt_val
        total_pl += pos['pl_val']

        log(f"{code:<15} {name:<20} {qty:<8} ${avg:<11.2f} {pl_pct:>+.2f}%     ${mkt_val:>11.2f}")

    log("-" * 80)
    log(f"{'TOTAL':<15} {'':<20} {'':<8} {'':<12} {'':<10} ${total_market_val:>11.2f}")
    log(f"Total P/L: ${total_pl:+.2f}")
    log("=" * 60)

    if dry_run:
        log("\n[DRY-RUN] No orders placed.")
        return

    # Confirmation
    if not force:
        log("\n⚠️  WARNING: This will SELL ALL listed positions at MARKET price!")
        confirm = input("Type 'LIQUIDATE' to confirm: ")
        if confirm.strip() != 'LIQUIDATE':
            log("❌ Liquidation cancelled.")
            return

    # Execute
    log("\n🚀 Executing liquidation...")
    success_count = 0
    fail_count = 0

    for pos in positions:
        code = pos['code']
        qty = pos['can_sell']

        if qty <= 0:
            log(f"Skipping {code} (qty=0)")
            continue

        if place_market_sell(code, qty, dry_run=False):
            success_count += 1
        else:
            fail_count += 1

    log("\n" + "=" * 60)
    log(f"Liquidation complete: {success_count} succeeded, {fail_count} failed")
    log("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='BabyMiles One-Click Liquidate')
    parser.add_argument('--confirmed', action='store_true', help='Required flag for live trading')
    parser.add_argument('--code', type=str, help='Liquidate specific stock only (e.g. US.SMH)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be sold without placing orders')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    if args.dry_run:
        liquidate_all(dry_run=True, target_code=args.code)
        return

    if not args.confirmed:
        log("❌ Error: --confirmed flag required for live trading.")
        log("   Add --dry-run to preview, or --confirmed to execute.")
        return

    liquidate_all(dry_run=False, target_code=args.code, force=args.force)


if __name__ == '__main__':
    main()
