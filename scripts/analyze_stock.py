#!/usr/bin/env python3
"""
Comprehensive stock analysis script for moomoo OpenAPI.
Orchestrates multiple skills to produce a unified analysis report.

Usage:
    python3 analyze_stock.py US.TSLA
    python3 analyze_stock.py US.TSLA --json
    python3 analyze_stock.py US.TSLA --report
"""

import sys
import json
import subprocess
import argparse
from datetime import datetime

sys.path.insert(0, '/usr/local/lib/python3.12/dist-packages')

from moomoo import OpenQuoteContext


def get_snapshot(symbol):
    """Fetch real-time market snapshot."""
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    ret, data = quote_ctx.get_market_snapshot([symbol])
    quote_ctx.close()
    
    if ret != 0:
        return None
    
    row = data.iloc[0]
    return {
        'code': symbol,
        'last_price': float(row.get('last_price', 0)),
        'open_price': float(row.get('open_price', 0)),
        'high_price': float(row.get('high_price', 0)),
        'low_price': float(row.get('low_price', 0)),
        'prev_close': float(row.get('prev_close_price', 0)),
        'volume': int(row.get('volume', 0)),
        'turnover': float(row.get('turnover', 0)),
        'change': float(row.get('change_val', 0)),
        'change_pct': float(row.get('change_rate', 0)),
    }


def get_kline_summary(symbol):
    """Fetch K-line summary (last 17 days)."""
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    ret, data, page = quote_ctx.request_history_kline(
        symbol, start='2026-04-20', end='2026-05-13', ktype='K_DAY'
    )
    quote_ctx.close()
    
    if ret != 0 or data is None or len(data) == 0:
        return None
    
    return {
        'days': len(data),
        'latest_close': float(data.iloc[-1]['close']),
        'period_high': float(data['high'].max()),
        'period_low': float(data['low'].min()),
        'ma5': float(data['close'].tail(5).mean()),
        'ma10': float(data['close'].tail(10).mean()),
    }


def get_capital_anomaly(symbol):
    """Fetch capital flow anomaly from moomoo-capital-anomaly skill."""
    try:
        result = subprocess.run(
            ['python3', 'scripts/handle_capital_anomaly.py', symbol, '--json'],
            cwd='/root/.hermes/skills/moomoo-capital-anomaly',
            capture_output=True, text=True, timeout=30
        )
        return result.stdout if result.returncode == 0 else None
    except:
        return None


def get_derivatives_anomaly(symbol):
    """Fetch options anomaly from moomoo-derivatives-anomaly skill."""
    try:
        result = subprocess.run(
            ['python3', 'scripts/handle_derivatives_anomaly.py', symbol, '--json'],
            cwd='/root/.hermes/skills/moomoo-derivatives-anomaly',
            capture_output=True, text=True, timeout=30
        )
        return result.stdout if result.returncode == 0 else None
    except:
        return None


def get_option_chain(symbol):
    """Fetch option chain data via OpenQuoteContext."""
    try:
        quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
        
        ret, dates = quote_ctx.get_option_expiration_date(code=symbol)
        
        option_data = {
            'expiration_dates': [],
            'chain': []
        }
        
        if ret == 0 and dates is not None and len(dates) > 0:
            nearest_date = dates.iloc[0]['strike_time']
            option_data['expiration_dates'] = dates['strike_time'].tolist()[:3]
            
            ret, chain = quote_ctx.get_option_chain(
                code=symbol,
                start=nearest_date,
                end=nearest_date
            )
            
            if ret == 0 and chain is not None:
                calls = chain[chain['option_type'] == 'CALL'].head(5)
                puts = chain[chain['option_type'] == 'PUT'].head(5)
                
                option_data['chain'] = {
                    'calls': calls[['strike_price', 'last_price', 'volume', 'open_interest']].to_dict('records') if len(calls) > 0 else [],
                    'puts': puts[['strike_price', 'last_price', 'volume', 'open_interest']].to_dict('records') if len(puts) > 0 else []
                }
        
        quote_ctx.close()
        return option_data
        
    except Exception as e:
        return None


def get_news(symbol):
    """Fetch news from moomoo news API."""
    try:
        import urllib.request
        import urllib.parse
        
        keyword = symbol.replace('US.', '')
        url = 'https://ai-news-search.moomoo.com/news_search?' + urllib.parse.urlencode({
            'keyword': keyword,
            'size': '10',
            'news_type': '1',
            'lang': 'en',
            'sort_type': '2'
        })
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'moomoo-news-search/0.0.2 (Skill)'
        })
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except:
        return None


def format_report(symbol, snapshot, kline, capital, derivatives, option_chain, news):
    """Format unified analysis report."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"📊 {symbol} Comprehensive Analysis Report")
    lines.append("=" * 60)
    lines.append("")
    
    # Real-time quote
    if snapshot:
        change_emoji = "📈" if snapshot['change'] >= 0 else "📉"
        lines.append("[Real-time Quote]")
        lines.append(f"Price: ${snapshot['last_price']:.2f} | Change: {snapshot['change_pct']:.2f}% {change_emoji}")
        lines.append(f"Open: ${snapshot['open_price']:.2f} | High: ${snapshot['high_price']:.2f} | Low: ${snapshot['low_price']:.2f}")
        lines.append(f"Prev Close: ${snapshot['prev_close']:.2f} | Volume: {snapshot['volume']:,} | Turnover: ${snapshot['turnover']/1e8:.1f}B")
        lines.append("")
    
    # K-line
    if kline:
        lines.append("[K-line Trend]")
        lines.append(f"Last {kline['days']} days")
        lines.append(f"Latest: ${kline['latest_close']:.2f} | Period High: ${kline['period_high']:.2f} | Period Low: ${kline['period_low']:.2f}")
        lines.append(f"MA5: ${kline['ma5']:.2f} | MA10: ${kline['ma10']:.2f}")
        if kline['ma5'] > kline['ma10']:
            lines.append("Trend: Bullish alignment 📈")
        else:
            lines.append("Trend: Bearish alignment 📉")
        lines.append("")
    
    # Capital flow
    if capital:
        lines.append("[Capital Flow]")
        if 'outflow' in capital.lower() or '净流出' in capital:
            lines.append("⚠️ Main force net outflow")
        elif 'inflow' in capital.lower() or '净流入' in capital:
            lines.append("✅ Main force net inflow")
        else:
            lines.append("➡️ Capital flow neutral")
        lines.append("")
    
    # Options anomaly
    if derivatives:
        lines.append("[Options Anomaly]")
        if 'call' in derivatives.lower() or '看涨' in derivatives:
            lines.append("📈 Call options active")
        if 'put' in derivatives.lower() or '看跌' in derivatives:
            lines.append("📉 Put options active")
        lines.append("")
    
    # Options chain
    if option_chain and option_chain.get('chain'):
        lines.append("[Options Chain]")
        
        if 'expiration_dates' in option_chain and option_chain['expiration_dates']:
            lines.append(f"Expiry: {', '.join(map(str, option_chain['expiration_dates'][:3]))}")
        
        chain = option_chain['chain']
        
        if chain.get('calls') and len(chain['calls']) > 0:
            lines.append("")
            lines.append("Call Options:")
            lines.append(f"{'Strike':<12} {'Price':<10} {'Volume':<10} {'OI':<10}")
            lines.append("-" * 45)
            for opt in chain['calls'][:5]:
                lines.append(f"${opt.get('strike_price', 0):<10.2f} ${opt.get('last_price', 0):<8.2f} {opt.get('volume', 0):<10} {opt.get('open_interest', 0):<10}")
        
        if chain.get('puts') and len(chain['puts']) > 0:
            lines.append("")
            lines.append("Put Options:")
            lines.append(f"{'Strike':<12} {'Price':<10} {'Volume':<10} {'OI':<10}")
            lines.append("-" * 45)
            for opt in chain['puts'][:5]:
                lines.append(f"${opt.get('strike_price', 0):<10.2f} ${opt.get('last_price', 0):<8.2f} {opt.get('volume', 0):<10} {opt.get('open_interest', 0):<10}")
        
        lines.append("")
    
    # News
    if news:
        lines.append("[Related News]")
        try:
            news_data = json.loads(news)
            if 'data' in news_data and news_data['data']:
                for i, item in enumerate(news_data['data'][:5], 1):
                    title = item.get('title', '').replace('<em>', '').replace('</em>', '')
                    pub_time = item.get('publish_time', '')
                    try:
                        dt = datetime.fromtimestamp(int(pub_time))
                        time_str = dt.strftime('%m/%d')
                    except:
                        time_str = ''
                    lines.append(f"{i}. [{time_str}] {title}")
        except:
            pass
        lines.append("")
    
    # Overall rating
    rating = 3
    if snapshot and snapshot['change_pct'] < -2:
        rating -= 1
    if capital and ('outflow' in capital.lower() or '净流出' in capital):
        rating -= 1
    if derivatives and ('put' in derivatives.lower() or '看跌' in derivatives) and not ('call' in derivatives.lower() or '看涨' in derivatives):
        rating -= 0.5
    rating = max(1, min(5, int(rating)))
    
    stars = "⭐" * rating + "☆" * (5 - rating)
    lines.append(f"[Overall Rating] {stars}")
    
    if rating >= 4:
        lines.append("Recommendation: Bullish, consider adding position")
    elif rating >= 3:
        lines.append("Recommendation: Neutral, hold or wait")
    else:
        lines.append("Recommendation: Cautious, watch for risks")
    
    lines.append("")
    lines.append("=" * 60)
    lines.append(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Comprehensive stock analysis via moomoo OpenAPI')
    parser.add_argument('symbol', help='Stock symbol (e.g. US.TSLA)')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    parser.add_argument('--report', action='store_true', help='Output Markdown report')
    args = parser.parse_args()
    
    symbol = args.symbol
    
    # Collect data from multiple sources
    snapshot = get_snapshot(symbol)
    kline = get_kline_summary(symbol)
    capital = get_capital_anomaly(symbol)
    derivatives = get_derivatives_anomaly(symbol)
    option_chain = get_option_chain(symbol)
    news = get_news(symbol)
    
    if args.json:
        result = {
            'symbol': symbol,
            'snapshot': snapshot,
            'kline': kline,
            'capital': capital,
            'derivatives': derivatives,
            'option_chain': option_chain,
            'news': news,
            'timestamp': datetime.now().isoformat()
        }
        print(json.dumps(result, indent=2, default=str))
    elif args.report:
        report = format_report(symbol, snapshot, kline, capital, derivatives, option_chain, news)
        print(report)
    else:
        report = format_report(symbol, snapshot, kline, capital, derivatives, option_chain, news)
        print(report)


if __name__ == '__main__':
    main()
