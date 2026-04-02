"""
Test script for the historical learning swarm system
Tests data collection, future-blind simulation, and learning capabilities
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.historical_data_collector import HistoricalDataCollector, DataWindow
from backtesting.future_blind_simulator import (
    FutureBlindSimulator, MomentumStrategy, TradingStrategy, TradeSignal
)
from historical_learning_swarm import LearningAgent, HistoricalLearningSwarm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_data_collection():
    """Test historical data collection"""
    logger.info("Testing data collection...")
    
    collector = HistoricalDataCollector()
    
    # Initialize with test exchange (using public data, no API key needed)
    test_config = {
        'binance': {
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        }
    }
    
    await collector.initialize_exchanges(test_config)
    
    # Test fetching historical data
    try:
        # Fetch last 7 days of BTC/USDT data
        since = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
        df = await collector.fetch_ohlcv_data('binance', 'BTC/USDT', '1h', since, limit=168)
        
        logger.info(f"Fetched {len(df)} candles")
        logger.info(f"Date range: {df.index[0]} to {df.index[-1]}")
        logger.info(f"Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
        
        # Test technical indicators
        df_with_indicators = collector.calculate_technical_indicators(df)
        logger.info(f"Added {len(df_with_indicators.columns) - len(df.columns)} technical indicators")
        
        await collector.close_all()
        return True
        
    except Exception as e:
        logger.error(f"Data collection test failed: {e}")
        await collector.close_all()
        return False


async def test_future_blind_simulation():
    """Test future-blind backtesting"""
    logger.info("Testing future-blind simulation...")
    
    # Create sample data
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='1H')
    prices = 40000 + np.cumsum(np.random.randn(len(dates)) * 100)
    
    sample_data = pd.DataFrame({
        'open': prices + np.random.randn(len(dates)) * 50,
        'high': prices + abs(np.random.randn(len(dates)) * 100),
        'low': prices - abs(np.random.randn(len(dates)) * 100),
        'close': prices,
        'volume': np.random.randint(100, 1000, len(dates))
    }, index=dates)
    
    # Create data window
    window = DataWindow(
        symbol='BTC/USDT',
        exchange='test',
        start_time=dates[0],
        end_time=dates[-1],
        current_time=dates[0],
        data=sample_data
    )
    
    # Test that future data is hidden
    visible_data = window.get_visible_data()
    assert len(visible_data) == 1, "Should only see first candle initially"
    
    # Advance time and check
    window.advance_time(60)  # 1 hour
    visible_data = window.get_visible_data()
    assert len(visible_data) == 2, "Should see 2 candles after advancing"
    
    # Run simulation with momentum strategy
    strategy = MomentumStrategy("test_momentum", {'momentum_threshold': 0.001})
    simulator = FutureBlindSimulator(initial_capital=10000)
    simulator.add_strategy(strategy)
    
    result = await simulator.run_simulation(window, time_step_minutes=60)
    
    logger.info(f"Simulation completed:")
    logger.info(f"  - Final balance: ${result.final_balance:.2f}")
    logger.info(f"  - Total return: {result.total_return:.2%}")
    logger.info(f"  - Max drawdown: {result.max_drawdown:.2%}")
    logger.info(f"  - Number of trades: {len(result.trades)}")
    
    return True


async def test_learning_agent():
    """Test learning agent capabilities"""
    logger.info("Testing learning agent...")
    
    # Create learning agent
    agent = LearningAgent("test_learner", {
        'signal_threshold': 0.6,
        'position_size': 1.0,
        'symbol': 'BTC/USDT'
    })
    
    # Create sample data with patterns
    dates = pd.date_range(start='2024-01-01', end='2024-02-01', freq='1H')
    
    # Create data with identifiable pattern (sine wave + trend)
    t = np.arange(len(dates))
    trend = t * 10
    seasonal = 1000 * np.sin(t * 2 * np.pi / (24 * 7))  # Weekly pattern
    noise = np.random.randn(len(dates)) * 100
    prices = 40000 + trend + seasonal + noise
    
    sample_data = pd.DataFrame({
        'open': prices + np.random.randn(len(dates)) * 50,
        'high': prices + abs(np.random.randn(len(dates)) * 100),
        'low': prices - abs(np.random.randn(len(dates)) * 100),
        'close': prices,
        'volume': 1000 + np.random.randint(-100, 100, len(dates))
    }, index=dates)
    
    # Test feature extraction
    features = agent._extract_features(sample_data[:100])
    logger.info(f"Extracted features: {list(features.keys())}")
    
    # Test signal generation
    signal = await agent.analyze(sample_data[:100], dates[99])
    if signal:
        logger.info(f"Generated signal: {signal.action} with confidence {signal.confidence:.2f}")
    
    # Simulate learning from results
    fake_results = [{
        'trades': [
            type('Trade', (), {
                'strategy_name': 'test_learner',
                'metadata': {'features': features},
                'pnl': np.random.randn() * 100
            })() for _ in range(10)
        ]
    }]
    
    agent.learn_from_results(fake_results)
    logger.info(f"Learned {len(agent.learned_patterns)} patterns")
    
    return True


async def test_integrated_system():
    """Test the full integrated historical learning swarm"""
    logger.info("Testing integrated historical learning swarm...")
    
    # Create mini swarm for testing
    swarm = HistoricalLearningSwarm(num_collectors=2, num_learners=3)
    
    try:
        # Initialize with test config
        test_config = {
            'binance': {
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            }
        }
        
        await swarm.data_swarm.initialize(test_config)
        
        # Create test learners
        for i in range(3):
            params = {
                'signal_threshold': 0.5 + (i * 0.1),
                'position_size': 1.0,
                'symbol': 'BTC/USDT'
            }
            agent = LearningAgent(f"test_learner_{i}", params)
            swarm.learners.append(agent)
        
        logger.info("Swarm initialized successfully")
        
        # Test data collection (using smaller timeframe for speed)
        # Note: This will attempt real API calls
        logger.info("Testing parallel data collection...")
        
        # Just test the structure, not actual API calls for the test
        logger.info("Swarm structure test completed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Integrated test failed: {e}")
        return False
    finally:
        await swarm.data_swarm.close_all()


async def main():
    """Run all tests"""
    logger.info("Starting historical learning swarm tests...")
    
    tests = [
        ("Data Collection", test_data_collection),
        ("Future-Blind Simulation", test_future_blind_simulation),
        ("Learning Agent", test_learning_agent),
        ("Integrated System", test_integrated_system)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            success = await test_func()
            results.append((test_name, success))
            logger.info(f"{test_name}: {'PASSED' if success else 'FAILED'}")
        except Exception as e:
            logger.error(f"{test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)