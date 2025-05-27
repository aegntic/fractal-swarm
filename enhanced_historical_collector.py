"""
Enhanced Historical Data Collector for BTC, ETH, and SOL
Collects extensive historical data and runs comprehensive backtesting simulations
"""

import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Tuple
import logging
import pickle
from redis import Redis
import aiofiles
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedDataCollector:
    """Collects and stores historical data for multiple cryptocurrencies"""
    
    def __init__(self):
        self.exchanges = {}
        self.data_dir = "data/historical"
        self.redis = Redis(host='localhost', port=6379, db=0)
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Target pairs
        self.target_pairs = [
            'BTC/USDT',
            'ETH/USDT', 
            'SOL/USDT'
        ]
        
        # Timeframes to collect
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
        
    async def initialize_exchanges(self):
        """Initialize exchange connections"""
        # Initialize multiple exchanges for redundancy
        exchanges_config = {
            'binance': {
                'apiKey': os.getenv('BINANCE_API_KEY'),
                'secret': os.getenv('BINANCE_SECRET'),
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            },
            'bybit': {
                'apiKey': os.getenv('BYBIT_API_KEY'),
                'secret': os.getenv('BYBIT_SECRET'),
                'enableRateLimit': True
            },
            'kucoin': {
                'apiKey': os.getenv('KUCOIN_API_KEY'),
                'secret': os.getenv('KUCOIN_SECRET'),
                'password': os.getenv('KUCOIN_PASSPHRASE'),
                'enableRateLimit': True
            }
        }
        
        for name, config in exchanges_config.items():
            try:
                if name == 'binance':
                    self.exchanges[name] = ccxt.binance(config)
                elif name == 'bybit':
                    self.exchanges[name] = ccxt.bybit(config)
                elif name == 'kucoin':
                    self.exchanges[name] = ccxt.kucoin(config)
                    
                await self.exchanges[name].load_markets()
                logger.info(f"Initialized {name} exchange")
            except Exception as e:
                logger.warning(f"Could not initialize {name}: {e}")
    
    async def fetch_all_historical_data(self, days_back: int = 365):
        """Fetch historical data for all pairs and timeframes"""
        logger.info(f"Starting historical data collection for past {days_back} days")
        
        for pair in self.target_pairs:
            logger.info(f"Collecting data for {pair}")
            
            for timeframe in self.timeframes:
                # Try multiple exchanges in order of preference
                for exchange_name in ['binance', 'bybit', 'kucoin']:
                    if exchange_name not in self.exchanges:
                        continue
                        
                    try:
                        df = await self.fetch_historical_ohlcv(
                            exchange_name, pair, timeframe, days_back
                        )
                        
                        if not df.empty:
                            # Save to disk
                            filename = f"{pair.replace('/', '_')}_{timeframe}_{exchange_name}.pkl"
                            filepath = os.path.join(self.data_dir, filename)
                            
                            async with aiofiles.open(filepath, 'wb') as f:
                                await f.write(pickle.dumps(df))
                            
                            logger.info(f"Saved {len(df)} candles for {pair} {timeframe}")
                            
                            # Also cache in Redis
                            cache_key = f"hist:{exchange_name}:{pair}:{timeframe}"
                            self.redis.setex(cache_key, 86400 * 7, pickle.dumps(df))
                            
                            break  # Success, move to next timeframe
                            
                    except Exception as e:
                        logger.error(f"Error fetching {pair} {timeframe} from {exchange_name}: {e}")
                        continue
    
    async def fetch_historical_ohlcv(self, exchange_name: str, symbol: str, 
                                   timeframe: str, days_back: int) -> pd.DataFrame:
        """Fetch historical OHLCV data with pagination"""
        exchange = self.exchanges[exchange_name]
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)
        
        all_candles = []
        since = int(start_time.timestamp() * 1000)
        
        # Fetch data in chunks
        while True:
            try:
                candles = await exchange.fetch_ohlcv(
                    symbol, timeframe, since=since, limit=1000
                )
                
                if not candles:
                    break
                
                all_candles.extend(candles)
                
                # Update since to last candle timestamp
                since = candles[-1][0] + 1
                
                # Break if we've reached current time
                if since >= int(end_time.timestamp() * 1000):
                    break
                    
                # Rate limit protection
                await asyncio.sleep(exchange.rateLimit / 1000)
                
            except Exception as e:
                logger.error(f"Error in fetch loop: {e}")
                break
        
        if not all_candles:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        # Add technical indicators
        df = self.add_technical_indicators(df)
        
        return df
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add comprehensive technical indicators"""
        # Price-based indicators
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Moving averages
        for period in [7, 14, 21, 50, 100, 200]:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        
        # MACD
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
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
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        df['bb_percent'] = (df['close'] - df['bb_lower']) / df['bb_width']
        
        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(14).mean()
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        df['obv'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        
        # Volatility
        df['volatility'] = df['returns'].rolling(window=20).std()
        df['volatility_ratio'] = df['volatility'] / df['volatility'].rolling(window=100).mean()
        
        # Support and Resistance levels
        df['resistance'] = df['high'].rolling(window=20).max()
        df['support'] = df['low'].rolling(window=20).min()
        
        # Price position
        df['price_position'] = (df['close'] - df['support']) / (df['resistance'] - df['support'])
        
        return df
    
    async def get_correlation_matrix(self) -> pd.DataFrame:
        """Calculate correlation matrix between assets"""
        returns_data = {}
        
        for pair in self.target_pairs:
            # Load daily data
            filename = f"{pair.replace('/', '_')}_1d_binance.pkl"
            filepath = os.path.join(self.data_dir, filename)
            
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    df = pickle.load(f)
                    returns_data[pair] = df['returns']
        
        # Create correlation matrix
        returns_df = pd.DataFrame(returns_data)
        correlation_matrix = returns_df.corr()
        
        return correlation_matrix
    
    async def get_market_statistics(self) -> Dict:
        """Calculate comprehensive market statistics"""
        stats = {}
        
        for pair in self.target_pairs:
            pair_stats = {}
            
            # Load different timeframes
            for timeframe in ['1d', '4h', '1h']:
                filename = f"{pair.replace('/', '_')}_{timeframe}_binance.pkl"
                filepath = os.path.join(self.data_dir, filename)
                
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        df = pickle.load(f)
                    
                    # Calculate statistics
                    pair_stats[timeframe] = {
                        'mean_return': df['returns'].mean(),
                        'volatility': df['returns'].std(),
                        'sharpe_ratio': df['returns'].mean() / df['returns'].std() if df['returns'].std() > 0 else 0,
                        'max_drawdown': (df['close'] / df['close'].cummax() - 1).min(),
                        'avg_volume': df['volume'].mean(),
                        'trend_strength': abs(df['ema_50'].iloc[-1] - df['ema_200'].iloc[-1]) / df['close'].iloc[-1] if 'ema_200' in df.columns else 0
                    }
            
            stats[pair] = pair_stats
        
        return stats
    
    async def close_all(self):
        """Close all exchange connections"""
        for exchange in self.exchanges.values():
            await exchange.close()


async def main():
    """Main function to collect historical data"""
    collector = EnhancedDataCollector()
    
    try:
        # Initialize exchanges
        await collector.initialize_exchanges()
        
        # Collect historical data
        await collector.fetch_all_historical_data(days_back=365)
        
        # Calculate correlations
        correlation_matrix = await collector.get_correlation_matrix()
        logger.info(f"Asset Correlations:\n{correlation_matrix}")
        
        # Get market statistics
        stats = await collector.get_market_statistics()
        logger.info(f"Market Statistics: {json.dumps(stats, indent=2)}")
        
        # Save metadata
        metadata = {
            'collection_date': datetime.now().isoformat(),
            'pairs': collector.target_pairs,
            'timeframes': collector.timeframes,
            'days_collected': 365,
            'statistics': stats
        }
        
        with open(os.path.join(collector.data_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info("Historical data collection completed successfully!")
        
    finally:
        await collector.close_all()


if __name__ == "__main__":
    asyncio.run(main())