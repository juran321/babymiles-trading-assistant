#!/usr/bin/env python3
"""
K-Line Chart Generator for moomoo API
Usage: python draw_kline.py --code US.TSLA --start 2026-04-20 --end 2026-05-13 --output /tmp/chart.png
"""

import sys
import argparse
sys.path.insert(0, '/usr/local/lib/python3.12/dist-packages')

from moomoo import OpenQuoteContext, RET_OK
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def draw_kline(code, start_date, end_date, output_path, ktype='K_DAY'):
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    
    try:
        ret, data, page_req_key = quote_ctx.request_history_kline(
            code, start=start_date, end=end_date, ktype=ktype
        )
        
        if ret != RET_OK:
            print(f"Failed to get kline data: {data}")
            return
        
        df = pd.DataFrame(data)
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                       gridspec_kw={'height_ratios': [3, 1]})
        
        # Plot candlesticks
        for idx, row in df.iterrows():
            color = '#ff4444' if row['close'] >= row['open'] else '#00aa00'
            # High-low line
            ax1.plot([idx, idx], [row['low'], row['high']], 
                    color=color, linewidth=1.5)
            # Open-close body
            height = abs(row['close'] - row['open'])
            bottom = min(row['close'], row['open'])
            ax1.bar(idx, height, bottom=bottom, color=color, width=0.6)
        
        # Moving averages
        if len(df) >= 5:
            df['MA5'] = df['close'].rolling(window=5).mean()
            ax1.plot(df.index, df['MA5'], label='MA5', 
                    color='orange', linewidth=1.5, alpha=0.8)
        if len(df) >= 10:
            df['MA10'] = df['close'].rolling(window=10).mean()
            ax1.plot(df.index, df['MA10'], label='MA10', 
                    color='blue', linewidth=1.5, alpha=0.8)
        if len(df) >= 20:
            df['MA20'] = df['close'].rolling(window=20).mean()
            ax1.plot(df.index, df['MA20'], label='MA20', 
                    color='purple', linewidth=1.5, alpha=0.8)
        
        # Formatting
        ax1.set_title(f'{code} K-Line Chart ({start_date} to {end_date})', 
                     fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price', fontsize=12)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Volume
        colors = ['#ff4444' if c >= o else '#00aa00' 
                 for c, o in zip(df['close'], df['open'])]
        ax2.bar(df.index, df['volume'], color=colors, width=0.6, alpha=0.7)
        ax2.set_ylabel('Volume', fontsize=12)
        ax2.set_xlabel('Trading Days', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Chart saved to: {output_path}")
        
    finally:
        quote_ctx.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Draw K-line chart')
    parser.add_argument('--code', required=True, help='Stock code (e.g., US.TSLA)')
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', default='/tmp/kline_chart.png', help='Output path')
    parser.add_argument('--ktype', default='K_DAY', help='K-line type')
    
    args = parser.parse_args()
    draw_kline(args.code, args.start, args.end, args.output, args.ktype)
