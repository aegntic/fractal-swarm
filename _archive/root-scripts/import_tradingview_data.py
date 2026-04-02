#!/usr/bin/env python3
"""
Import TradingView CSV exports for backtesting
"""

import argparse
import os
import sys
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingview_integration import TradingViewDataImporter
from enhanced_simulation_runner import EnhancedSimulationRunner


def main():
    parser = argparse.ArgumentParser(description='Import TradingView data for backtesting')
    parser.add_argument('--file', '-f', required=True, help='Path to TradingView CSV export')
    parser.add_argument('--symbol', '-s', help='Symbol (auto-detected if not provided)')
    parser.add_argument('--backtest', '-b', action='store_true', help='Run backtest after import')
    parser.add_argument('--strategy', '-st', default='momentum', 
                       choices=['momentum', 'mean_reversion', 'breakout'],
                       help='Strategy to use for backtesting')
    
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        sys.exit(1)
    
    print(f"Importing TradingView data from: {args.file}")
    
    # Import data
    importer = TradingViewDataImporter()
    result = importer.process_tradingview_export(args.file)
    
    print("\nImport Summary:")
    print(f"  Symbol: {result['symbol']}")
    print(f"  Timeframe: {result['timeframe']}")
    print(f"  Data points: {result['data_points']}")
    print(f"  Date range: {result['date_range']}")
    print(f"  Indicators: {', '.join(result['indicators'][:10])}")
    print(f"  Saved to: {result['output_file']}")
    
    # Run backtest if requested
    if args.backtest:
        print("\nRunning backtest...")
        run_backtest(result['output_file'], result['symbol'], args.strategy)


def run_backtest(data_file: str, symbol: str, strategy: str):
    """Run a simple backtest on imported data"""
    import pickle
    
    # Load data
    with open(data_file, 'rb') as f:
        df = pickle.load(f)
    
    print(f"\nBacktesting {strategy} strategy on {symbol}")
    print(f"Data range: {df.index[0]} to {df.index[-1]}")
    
    # Simple backtest logic
    initial_capital = 10000
    capital = initial_capital
    position = 0
    trades = []
    
    # Strategy parameters
    if strategy == 'momentum':
        # Buy when price crosses above SMA and RSI < 70
        # Sell when price crosses below SMA or RSI > 70
        for i in range(50, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            
            if position == 0:  # No position
                if (row['close'] > row.get('sma_50', row['sma_20']) and 
                    prev_row['close'] <= prev_row.get('sma_50', prev_row['sma_20']) and
                    row.get('rsi', 50) < 70):
                    # Buy signal
                    position = capital * 0.95 / row['close']
                    capital *= 0.05  # Keep 5% as reserve
                    trades.append({
                        'time': df.index[i],
                        'action': 'buy',
                        'price': row['close'],
                        'size': position
                    })
                    
            else:  # Have position
                if (row['close'] < row.get('sma_50', row['sma_20']) or 
                    row.get('rsi', 50) > 70):
                    # Sell signal
                    capital += position * row['close'] * 0.999  # 0.1% fee
                    trades.append({
                        'time': df.index[i],
                        'action': 'sell',
                        'price': row['close'],
                        'size': position
                    })
                    position = 0
    
    # Close any remaining position
    if position > 0:
        capital += position * df.iloc[-1]['close'] * 0.999
    
    # Calculate results
    total_return = (capital - initial_capital) / initial_capital
    num_trades = len([t for t in trades if t['action'] == 'buy'])
    
    # Calculate buy and hold
    buy_hold_return = (df.iloc[-1]['close'] - df.iloc[50]['close']) / df.iloc[50]['close']
    
    print("\nBacktest Results:")
    print(f"  Initial Capital: ${initial_capital:,.2f}")
    print(f"  Final Capital: ${capital:,.2f}")
    print(f"  Total Return: {total_return:.2%}")
    print(f"  Number of Trades: {num_trades}")
    print(f"  Buy & Hold Return: {buy_hold_return:.2%}")
    print(f"  Strategy vs B&H: {total_return - buy_hold_return:.2%}")
    
    # Save trades
    if trades:
        trades_df = pd.DataFrame(trades)
        trades_file = data_file.replace('.pkl', '_trades.csv')
        trades_df.to_csv(trades_file, index=False)
        print(f"\nTrades saved to: {trades_file}")


if __name__ == "__main__":
    main()