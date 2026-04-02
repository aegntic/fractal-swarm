#!/usr/bin/env python3
"""
Demo Enhanced Analysis - Uses synthetic data for demonstration
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import logging
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DemoDataGenerator:
    """Generates synthetic market data for demonstration"""
    
    def __init__(self):
        self.data_dir = "data/demo"
        os.makedirs(self.data_dir, exist_ok=True)
        
    def generate_ohlcv_data(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """Generate synthetic OHLCV data"""
        # Create time index
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        date_range = pd.date_range(start=start_date, end=end_date, freq='1h')
        
        # Generate price data with realistic patterns
        np.random.seed(42)  # For reproducibility
        
        # Base price levels
        base_prices = {
            'BTC/USDT': 30000,
            'ETH/USDT': 2000,
            'SOL/USDT': 50
        }
        
        base_price = base_prices.get(symbol, 100)
        
        # Generate returns with volatility
        returns = np.random.normal(0.0002, 0.02, len(date_range))
        
        # Add trend
        trend = np.linspace(0, 0.5, len(date_range))
        returns = returns + trend / len(date_range)
        
        # Generate prices
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Generate OHLCV
        data = []
        for i, (timestamp, price) in enumerate(zip(date_range, prices)):
            # Add intraday volatility
            high = price * (1 + abs(np.random.normal(0, 0.01)))
            low = price * (1 - abs(np.random.normal(0, 0.01)))
            open_price = price * (1 + np.random.normal(0, 0.005))
            close = price
            volume = np.random.lognormal(10, 1.5)
            
            data.append({
                'timestamp': timestamp,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        # Add technical indicators
        df = self.add_indicators(df)
        
        return df
    
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators"""
        # Returns
        df['returns'] = df['close'].pct_change()
        
        # Moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_percent'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Volume
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(14).mean()
        
        return df


class SimplifiedBacktester:
    """Simplified backtester for demonstration"""
    
    def __init__(self):
        self.results = []
        
    def run_strategy(self, data: Dict[str, pd.DataFrame], strategy_params: Dict) -> Dict:
        """Run a simple strategy backtest"""
        initial_capital = 10000
        capital = initial_capital
        trades = 0
        wins = 0
        
        # Simple strategy: Buy when RSI < 30 and MACD > 0, Sell when RSI > 70
        for symbol, df in data.items():
            df = df.dropna()
            
            position = 0
            entry_price = 0
            
            for i in range(len(df)):
                row = df.iloc[i]
                
                # Buy signal
                if position == 0 and row['rsi'] < strategy_params.get('rsi_oversold', 30) and row['macd'] > 0:
                    position = capital * 0.1 / row['close']  # 10% position
                    entry_price = row['close']
                    capital -= position * entry_price
                    
                # Sell signal
                elif position > 0 and row['rsi'] > strategy_params.get('rsi_overbought', 70):
                    exit_price = row['close']
                    capital += position * exit_price
                    
                    # Track trade
                    trades += 1
                    if exit_price > entry_price:
                        wins += 1
                    
                    position = 0
        
        # Close any open positions
        if position > 0:
            capital += position * df.iloc[-1]['close']
        
        # Calculate metrics
        total_return = (capital - initial_capital) / initial_capital
        win_rate = wins / trades if trades > 0 else 0
        
        return {
            'initial_capital': initial_capital,
            'final_capital': capital,
            'total_return': total_return,
            'total_trades': trades,
            'win_rate': win_rate,
            'strategy_params': strategy_params
        }


async def main():
    """Main demo function"""
    logger.info("="*60)
    logger.info("CRYPTO SWARM TRADER - DEMO ANALYSIS")
    logger.info("="*60)
    
    # Generate synthetic data
    logger.info("\n[1/3] Generating Synthetic Historical Data...")
    generator = DemoDataGenerator()
    
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    data = {}
    
    for symbol in symbols:
        logger.info(f"Generating data for {symbol}")
        df = generator.generate_ohlcv_data(symbol, days=365)
        data[symbol] = df
        
        # Save to disk
        filename = f"{symbol.replace('/', '_')}_demo.csv"
        filepath = os.path.join(generator.data_dir, filename)
        df.to_csv(filepath)
        logger.info(f"  Generated {len(df)} hours of data")
    
    # Calculate correlations
    logger.info("\n[2/3] Analyzing Market Correlations...")
    returns_data = pd.DataFrame({
        symbol: df['returns'] for symbol, df in data.items()
    })
    correlation_matrix = returns_data.corr()
    
    logger.info("\nAsset Correlations:")
    logger.info(correlation_matrix.to_string())
    
    # Run backtests
    logger.info("\n[3/3] Running Strategy Backtests...")
    backtester = SimplifiedBacktester()
    
    # Test different parameter combinations
    param_variations = [
        {'rsi_oversold': 25, 'rsi_overbought': 75},
        {'rsi_oversold': 30, 'rsi_overbought': 70},
        {'rsi_oversold': 35, 'rsi_overbought': 65},
        {'rsi_oversold': 20, 'rsi_overbought': 80},
        {'rsi_oversold': 30, 'rsi_overbought': 75},
    ]
    
    results = []
    for i, params in enumerate(param_variations):
        logger.info(f"Testing strategy {i+1}/{len(param_variations)}")
        result = backtester.run_strategy(data, params)
        results.append(result)
    
    # Sort by return
    results.sort(key=lambda x: x['total_return'], reverse=True)
    
    # Display results
    logger.info("\n" + "="*60)
    logger.info("BACKTEST RESULTS")
    logger.info("="*60)
    
    for i, result in enumerate(results):
        logger.info(f"\nStrategy #{i+1}:")
        logger.info(f"  Parameters: RSI({result['strategy_params']['rsi_oversold']}/{result['strategy_params']['rsi_overbought']})")
        logger.info(f"  Initial Capital: ${result['initial_capital']:,.2f}")
        logger.info(f"  Final Capital: ${result['final_capital']:,.2f}")
        logger.info(f"  Total Return: {result['total_return']:.2%}")
        logger.info(f"  Total Trades: {result['total_trades']}")
        logger.info(f"  Win Rate: {result['win_rate']:.2%}")
    
    # Market statistics
    logger.info("\n" + "="*60)
    logger.info("MARKET STATISTICS")
    logger.info("="*60)
    
    for symbol, df in data.items():
        returns = df['returns'].dropna()
        logger.info(f"\n{symbol}:")
        logger.info(f"  Average Daily Return: {returns.mean()*24:.3%}")
        logger.info(f"  Daily Volatility: {returns.std()*np.sqrt(24):.3%}")
        logger.info(f"  Sharpe Ratio: {(returns.mean()/returns.std()*np.sqrt(24*365)):.2f}")
        logger.info(f"  Max Drawdown: {((df['close']/df['close'].cummax() - 1).min()):.2%}")
    
    logger.info("\n" + "="*60)
    logger.info("DEMO COMPLETE!")
    logger.info("="*60)
    logger.info("\nThis demo used synthetic data to demonstrate the analysis capabilities.")
    logger.info("With real API keys, the system would:")
    logger.info("  1. Collect actual historical data from exchanges")
    logger.info("  2. Run more sophisticated multi-timeframe strategies")
    logger.info("  3. Optimize parameters using machine learning")
    logger.info("  4. Generate detailed performance reports")
    
    # Save summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'symbols_analyzed': symbols,
        'data_points': sum(len(df) for df in data.values()),
        'strategies_tested': len(results),
        'best_return': results[0]['total_return'] if results else 0,
        'correlations': correlation_matrix.to_dict()
    }
    
    os.makedirs('simulation_results', exist_ok=True)
    with open('simulation_results/demo_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())