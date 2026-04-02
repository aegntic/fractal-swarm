"""
Historical Learning Swarm Integration
Connects historical data collection and backtesting with the main swarm coordinator
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from dataclasses import dataclass
import pandas as pd
import numpy as np

from agents.historical_data_collector import HistoricalDataCollector, HistoricalDataSwarm, DataWindow
from backtesting.future_blind_simulator import (
    FutureBlindSimulator, TradingStrategy, TradeSignal, 
    ParallelBacktestRunner, MomentumStrategy
)
from swarm_coordinator import SwarmCoordinator
from config import REDIS_CONFIG, EXCHANGE_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LearningAgent(TradingStrategy):
    """Agent that learns from historical data patterns"""
    
    def __init__(self, name: str, params: Dict = None):
        super().__init__(name, params)
        self.learned_patterns = {}
        self.performance_history = []
        
    async def analyze(self, data: pd.DataFrame, current_time: datetime) -> Optional[TradeSignal]:
        """Analyze data using learned patterns"""
        # Calculate features
        features = self._extract_features(data)
        
        # Match against learned patterns
        signal_strength = self._evaluate_patterns(features)
        
        if abs(signal_strength) > self.params.get('signal_threshold', 0.6):
            action = 'buy' if signal_strength > 0 else 'sell'
            confidence = min(abs(signal_strength), 1.0)
            
            return TradeSignal(
                timestamp=current_time,
                symbol=self.params.get('symbol', 'BTC/USDT'),
                action=action,
                confidence=confidence,
                size=self.params.get('position_size', 1.0),
                strategy_name=self.name,
                metadata={'signal_strength': signal_strength, 'features': features}
            )
        
        return None
    
    def _extract_features(self, data: pd.DataFrame) -> Dict:
        """Extract relevant features from market data"""
        if len(data) < 50:
            return {}
            
        # Price features
        close_prices = data['close']
        returns = close_prices.pct_change()
        
        features = {
            'momentum_5': returns.rolling(5).mean().iloc[-1],
            'momentum_20': returns.rolling(20).mean().iloc[-1],
            'volatility': returns.rolling(20).std().iloc[-1],
            'volume_ratio': (data['volume'].iloc[-1] / data['volume'].rolling(20).mean().iloc[-1]),
            'price_position': (close_prices.iloc[-1] - close_prices.rolling(20).min().iloc[-1]) / 
                            (close_prices.rolling(20).max().iloc[-1] - close_prices.rolling(20).min().iloc[-1])
        }
        
        # Technical indicators
        sma_20 = close_prices.rolling(20).mean().iloc[-1]
        sma_50 = close_prices.rolling(50).mean().iloc[-1] if len(data) >= 50 else sma_20
        
        features['sma_crossover'] = (close_prices.iloc[-1] - sma_20) / sma_20
        features['trend_strength'] = (sma_20 - sma_50) / sma_50 if sma_50 > 0 else 0
        
        # RSI
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['rsi'] = (100 - (100 / (1 + rs))).iloc[-1]
        
        return features
    
    def _evaluate_patterns(self, features: Dict) -> float:
        """Evaluate features against learned patterns"""
        if not self.learned_patterns or not features:
            return 0.0
            
        signal_scores = []
        
        for pattern_name, pattern_data in self.learned_patterns.items():
            similarity = self._calculate_similarity(features, pattern_data['features'])
            expected_return = pattern_data['avg_return']
            confidence = pattern_data['confidence']
            
            # Weight by similarity, expected return, and confidence
            score = similarity * expected_return * confidence
            signal_scores.append(score)
        
        # Aggregate scores
        if signal_scores:
            return np.mean(signal_scores)
        return 0.0
    
    def _calculate_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity between two feature sets"""
        common_keys = set(features1.keys()) & set(features2.keys())
        if not common_keys:
            return 0.0
            
        differences = []
        for key in common_keys:
            # Normalize difference to [0, 1]
            diff = abs(features1[key] - features2[key])
            normalized_diff = 1 / (1 + diff)  # Convert to similarity
            differences.append(normalized_diff)
        
        return np.mean(differences)
    
    def learn_from_results(self, simulation_results: List[Dict]):
        """Update learned patterns based on backtest results"""
        # Group trades by features
        pattern_groups = {}
        
        for result in simulation_results:
            for trade in result.get('trades', []):
                if trade.strategy_name == self.name:
                    features = trade.metadata.get('features', {})
                    feature_key = self._hash_features(features)
                    
                    if feature_key not in pattern_groups:
                        pattern_groups[feature_key] = {
                            'features': features,
                            'trades': [],
                            'returns': []
                        }
                    
                    pattern_groups[feature_key]['trades'].append(trade)
                    if hasattr(trade, 'pnl') and trade.pnl is not None:
                        pattern_groups[feature_key]['returns'].append(trade.pnl)
        
        # Update learned patterns
        self.learned_patterns = {}
        for pattern_key, pattern_data in pattern_groups.items():
            if len(pattern_data['returns']) >= 5:  # Minimum trades for pattern
                avg_return = np.mean(pattern_data['returns'])
                std_return = np.std(pattern_data['returns'])
                win_rate = sum(1 for r in pattern_data['returns'] if r > 0) / len(pattern_data['returns'])
                
                # Only keep profitable patterns with good win rate
                if avg_return > 0 and win_rate > 0.5:
                    self.learned_patterns[pattern_key] = {
                        'features': pattern_data['features'],
                        'avg_return': avg_return,
                        'std_return': std_return,
                        'win_rate': win_rate,
                        'confidence': min(win_rate * (1 - std_return / abs(avg_return)), 1.0),
                        'num_trades': len(pattern_data['trades'])
                    }
        
        logger.info(f"Agent {self.name} learned {len(self.learned_patterns)} profitable patterns")
    
    def _hash_features(self, features: Dict) -> str:
        """Create a hash key for feature set"""
        # Discretize features for grouping
        discretized = {}
        for key, value in features.items():
            if isinstance(value, (int, float)):
                # Round to 2 decimal places for grouping
                discretized[key] = round(value, 2)
            else:
                discretized[key] = value
        
        return json.dumps(discretized, sort_keys=True)


class HistoricalLearningSwarm:
    """Main coordinator for historical learning swarm"""
    
    def __init__(self, num_collectors: int = 5, num_learners: int = 10):
        self.data_swarm = HistoricalDataSwarm(num_collectors)
        self.learners = []
        self.num_learners = num_learners
        self.backtest_runner = ParallelBacktestRunner()
        self.swarm_coordinator = None
        
    async def initialize(self):
        """Initialize the learning swarm"""
        # Initialize data collectors
        exchange_configs = {
            'binance': {
                'apiKey': os.getenv('BINANCE_API_KEY'),
                'secret': os.getenv('BINANCE_SECRET'),
                'enableRateLimit': True
            },
            'coinbase': {
                'apiKey': os.getenv('COINBASE_API_KEY'),
                'secret': os.getenv('COINBASE_SECRET'),
                'enableRateLimit': True
            }
        }
        
        await self.data_swarm.initialize(exchange_configs)
        
        # Create learning agents with different parameters
        for i in range(self.num_learners):
            params = {
                'signal_threshold': 0.5 + (i * 0.05),  # Vary thresholds
                'position_size': 1.0,
                'symbol': 'BTC/USDT',
                'lookback_period': 20 + (i * 5)  # Vary lookback
            }
            
            agent = LearningAgent(f"learner_{i}", params)
            self.learners.append(agent)
        
        # Initialize main swarm coordinator
        self.swarm_coordinator = SwarmCoordinator()
        
        logger.info(f"Initialized learning swarm with {num_collectors} collectors and {num_learners} learners")
    
    async def collect_and_learn(self, symbols: List[str], days_back: int = 30):
        """Collect historical data and run learning simulations"""
        logger.info(f"Starting data collection for {symbols} going back {days_back} days")
        
        # Phase 1: Collect historical data
        collection_tasks = []
        for symbol in symbols:
            for exchange in ['binance', 'coinbase']:
                for timeframe in ['1m', '5m', '15m']:
                    collection_tasks.append((exchange, symbol, timeframe))
        
        historical_data = await self.data_swarm.collect_parallel(collection_tasks)
        logger.info(f"Collected {len(historical_data)} datasets")
        
        # Phase 2: Create data windows for backtesting
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        data_windows = []
        for key, df in historical_data.items():
            if '1m' in key:  # Use 1-minute data for backtesting
                exchange, symbol, _ = key.split(':')
                window = DataWindow(
                    symbol=symbol,
                    exchange=exchange,
                    start_time=start_date,
                    end_time=end_date,
                    current_time=start_date,
                    data=df
                )
                data_windows.append(window)
        
        # Phase 3: Run initial backtests
        logger.info("Running initial backtests...")
        initial_results = await self._run_learning_cycle(data_windows[:5])  # Start with subset
        
        # Phase 4: Learn from results and iterate
        for iteration in range(3):  # 3 learning iterations
            logger.info(f"Learning iteration {iteration + 1}")
            
            # Update agent patterns
            for agent in self.learners:
                agent.learn_from_results(initial_results)
            
            # Run new backtests with learned patterns
            test_windows = data_windows[5:10] if len(data_windows) > 10 else data_windows
            results = await self._run_learning_cycle(test_windows)
            
            # Evaluate performance improvement
            avg_return = np.mean([r['total_return'] for r in results])
            logger.info(f"Iteration {iteration + 1} average return: {avg_return:.2%}")
        
        # Phase 5: Deploy best performing agents
        await self._deploy_best_agents()
    
    async def _run_learning_cycle(self, data_windows: List[DataWindow]) -> List[Dict]:
        """Run backtests for all learning agents"""
        results = []
        
        for window in data_windows:
            for agent in self.learners:
                simulator = FutureBlindSimulator(initial_capital=10000)
                simulator.add_strategy(agent)
                
                # Clone window to avoid interference
                window_copy = DataWindow(
                    symbol=window.symbol,
                    exchange=window.exchange,
                    start_time=window.start_time,
                    end_time=window.end_time,
                    current_time=window.start_time,
                    data=window.data.copy()
                )
                
                result = await simulator.run_simulation(window_copy)
                results.append({
                    'agent': agent.name,
                    'symbol': window.symbol,
                    'exchange': window.exchange,
                    'total_return': result.total_return,
                    'sharpe_ratio': result.sharpe_ratio,
                    'max_drawdown': result.max_drawdown,
                    'trades': result.trades
                })
        
        return results
    
    async def _deploy_best_agents(self):
        """Deploy the best performing agents to production swarm"""
        # Analyze agent performance
        agent_performance = {}
        
        for agent in self.learners:
            if agent.performance_history:
                avg_return = np.mean([p['total_return'] for p in agent.performance_history])
                avg_sharpe = np.mean([p['sharpe_ratio'] for p in agent.performance_history])
                
                agent_performance[agent.name] = {
                    'avg_return': avg_return,
                    'avg_sharpe': avg_sharpe,
                    'learned_patterns': len(agent.learned_patterns)
                }
        
        # Select top performers
        sorted_agents = sorted(
            agent_performance.items(),
            key=lambda x: x[1]['avg_sharpe'],
            reverse=True
        )
        
        top_agents = sorted_agents[:3]  # Deploy top 3
        
        logger.info(f"Deploying top performing agents: {[a[0] for a in top_agents]}")
        
        # TODO: Integrate with main swarm coordinator
        # This would create production trading agents based on learned patterns
    
    async def continuous_learning_loop(self):
        """Run continuous learning loop"""
        while True:
            try:
                # Collect and learn from recent data
                await self.collect_and_learn(['BTC/USDT', 'ETH/USDT'], days_back=7)
                
                # Wait before next cycle
                await asyncio.sleep(3600)  # Run hourly
                
            except Exception as e:
                logger.error(f"Learning loop error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error


async def main():
    """Main entry point for historical learning swarm"""
    learning_swarm = HistoricalLearningSwarm(num_collectors=3, num_learners=5)
    
    try:
        await learning_swarm.initialize()
        await learning_swarm.collect_and_learn(
            symbols=['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
            days_back=30
        )
        
        # Start continuous learning
        await learning_swarm.continuous_learning_loop()
        
    except KeyboardInterrupt:
        logger.info("Shutting down learning swarm...")
    finally:
        await learning_swarm.data_swarm.close_all()


if __name__ == "__main__":
    asyncio.run(main())