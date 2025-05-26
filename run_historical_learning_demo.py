"""
Demo script to run historical learning swarm with simulated data
This demonstrates the polymorphic strategy optimization capabilities
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
import random
import numpy as np
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimulatedDataProvider:
    """Provides simulated market data for demonstration"""
    
    @staticmethod
    def generate_price_data(symbol: str, days: int = 30):
        """Generate realistic price movements"""
        base_price = {'BTC/USDT': 40000, 'ETH/USDT': 2500, 'SOL/USDT': 100}.get(symbol, 100)
        timestamps = []
        prices = []
        volumes = []
        
        current_time = datetime.now() - timedelta(days=days)
        current_price = base_price
        
        for _ in range(days * 24 * 60):  # 1-minute candles
            # Random walk with trend
            change = random.gauss(0, 0.002)  # 0.2% std dev
            trend = 0.00001  # Slight upward trend
            current_price *= (1 + change + trend)
            
            timestamps.append(current_time)
            prices.append(current_price)
            volumes.append(random.uniform(100, 1000) * base_price)
            
            current_time += timedelta(minutes=1)
        
        return {
            'timestamp': timestamps,
            'close': prices,
            'volume': volumes,
            'high': [p * 1.001 for p in prices],
            'low': [p * 0.999 for p in prices],
            'open': [prices[0]] + prices[:-1]
        }

class PolymorphicStrategy:
    """Demonstrates polymorphic strategy that evolves based on market conditions"""
    
    def __init__(self, name: str, genome: Dict):
        self.name = name
        self.genome = genome
        self.performance_history = []
        self.adaptation_count = 0
        
    def analyze(self, market_data: Dict) -> Dict:
        """Analyze market and generate signals"""
        prices = market_data['close']
        if len(prices) < 50:
            return {'action': 'hold', 'confidence': 0}
        
        # Calculate indicators based on genome
        sma_short = self._sma(prices, int(self.genome['sma_short']))
        sma_long = self._sma(prices, int(self.genome['sma_long']))
        rsi = self._rsi(prices, int(self.genome['rsi_period']))
        
        # Decision logic based on genome thresholds
        signal_strength = 0
        
        if sma_short[-1] > sma_long[-1] * (1 + self.genome['trend_threshold']):
            signal_strength += self.genome['trend_weight']
        elif sma_short[-1] < sma_long[-1] * (1 - self.genome['trend_threshold']):
            signal_strength -= self.genome['trend_weight']
            
        if rsi[-1] < self.genome['rsi_oversold']:
            signal_strength += self.genome['rsi_weight']
        elif rsi[-1] > self.genome['rsi_overbought']:
            signal_strength -= self.genome['rsi_weight']
        
        # Volume confirmation
        vol_ratio = market_data['volume'][-1] / np.mean(market_data['volume'][-20:])
        if vol_ratio > self.genome['volume_threshold']:
            signal_strength *= self.genome['volume_multiplier']
        
        # Generate action
        if signal_strength > self.genome['action_threshold']:
            return {'action': 'buy', 'confidence': min(abs(signal_strength), 1.0)}
        elif signal_strength < -self.genome['action_threshold']:
            return {'action': 'sell', 'confidence': min(abs(signal_strength), 1.0)}
        else:
            return {'action': 'hold', 'confidence': 0}
    
    def mutate(self):
        """Evolve strategy based on performance"""
        self.adaptation_count += 1
        
        # Mutate genome parameters
        mutation_rate = 0.1
        for key, value in self.genome.items():
            if random.random() < mutation_rate:
                if isinstance(value, float):
                    self.genome[key] *= random.uniform(0.9, 1.1)
                elif isinstance(value, int):
                    self.genome[key] = max(1, value + random.randint(-2, 2))
        
        logger.info(f"Strategy {self.name} mutated (adaptation #{self.adaptation_count})")
    
    def _sma(self, prices: List[float], period: int) -> List[float]:
        """Simple moving average"""
        sma = []
        for i in range(len(prices)):
            if i < period - 1:
                sma.append(prices[i])
            else:
                sma.append(np.mean(prices[i-period+1:i+1]))
        return sma
    
    def _rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """Relative Strength Index"""
        deltas = [prices[i] - prices[i-1] if i > 0 else 0 for i in range(len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gains = []
        avg_losses = []
        rsi_values = []
        
        for i in range(len(prices)):
            if i < period:
                avg_gains.append(np.mean(gains[:i+1]) if i > 0 else 0)
                avg_losses.append(np.mean(losses[:i+1]) if i > 0 else 0)
            else:
                avg_gains.append((avg_gains[-1] * (period - 1) + gains[i]) / period)
                avg_losses.append((avg_losses[-1] * (period - 1) + losses[i]) / period)
            
            if avg_losses[-1] == 0:
                rsi_values.append(100)
            else:
                rs = avg_gains[-1] / avg_losses[-1]
                rsi_values.append(100 - (100 / (1 + rs)))
        
        return rsi_values

class LearningSwarmDemo:
    """Demonstrates historical learning swarm with polymorphic strategies"""
    
    def __init__(self, num_strategies: int = 10):
        self.strategies = []
        self.num_strategies = num_strategies
        self.generation = 0
        
    def initialize_strategies(self):
        """Create initial population of strategies with diverse genomes"""
        base_genomes = [
            {
                'sma_short': 10, 'sma_long': 30, 'trend_threshold': 0.02,
                'trend_weight': 0.6, 'rsi_period': 14, 'rsi_oversold': 30,
                'rsi_overbought': 70, 'rsi_weight': 0.4, 'volume_threshold': 1.5,
                'volume_multiplier': 1.2, 'action_threshold': 0.5
            },
            {
                'sma_short': 5, 'sma_long': 20, 'trend_threshold': 0.01,
                'trend_weight': 0.4, 'rsi_period': 21, 'rsi_oversold': 25,
                'rsi_overbought': 75, 'rsi_weight': 0.6, 'volume_threshold': 2.0,
                'volume_multiplier': 1.5, 'action_threshold': 0.6
            },
            {
                'sma_short': 20, 'sma_long': 50, 'trend_threshold': 0.03,
                'trend_weight': 0.7, 'rsi_period': 9, 'rsi_oversold': 35,
                'rsi_overbought': 65, 'rsi_weight': 0.3, 'volume_threshold': 1.2,
                'volume_multiplier': 1.1, 'action_threshold': 0.4
            }
        ]
        
        # Create strategies with variations
        for i in range(self.num_strategies):
            base = base_genomes[i % len(base_genomes)].copy()
            
            # Add random variations
            for key in base:
                if isinstance(base[key], float):
                    base[key] *= random.uniform(0.8, 1.2)
                elif isinstance(base[key], int) and key != 'sma_short' and key != 'sma_long':
                    base[key] = max(1, base[key] + random.randint(-5, 5))
            
            strategy = PolymorphicStrategy(f"poly_strategy_{i}", base)
            self.strategies.append(strategy)
        
        logger.info(f"Initialized {self.num_strategies} polymorphic strategies")
    
    async def run_learning_cycle(self, symbols: List[str], days: int = 30):
        """Run a complete learning cycle"""
        logger.info(f"Starting learning cycle for generation {self.generation}")
        
        # Generate simulated data
        market_data = {}
        for symbol in symbols:
            market_data[symbol] = SimulatedDataProvider.generate_price_data(symbol, days)
            logger.info(f"Generated {len(market_data[symbol]['close'])} data points for {symbol}")
        
        # Backtest each strategy
        results = []
        for strategy in self.strategies:
            performance = await self.backtest_strategy(strategy, market_data)
            results.append({
                'strategy': strategy.name,
                'total_return': performance['total_return'],
                'sharpe_ratio': performance['sharpe_ratio'],
                'win_rate': performance['win_rate'],
                'trades': performance['num_trades']
            })
            strategy.performance_history.append(performance)
        
        # Sort by performance
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        
        # Display results
        logger.info("\n=== Generation {} Results ===".format(self.generation))
        for i, result in enumerate(results[:5]):  # Top 5
            logger.info(f"{i+1}. {result['strategy']}: "
                       f"Return={result['total_return']:.2%}, "
                       f"Sharpe={result['sharpe_ratio']:.2f}, "
                       f"Win Rate={result['win_rate']:.2%}, "
                       f"Trades={result['trades']}")
        
        # Evolve strategies
        await self.evolve_strategies(results)
        
        self.generation += 1
    
    async def backtest_strategy(self, strategy: PolymorphicStrategy, market_data: Dict) -> Dict:
        """Backtest a strategy on historical data"""
        capital = 10000
        position = 0
        trades = []
        
        for symbol, data in market_data.items():
            for i in range(50, len(data['close'])):  # Need 50 bars for indicators
                market_snapshot = {
                    'close': data['close'][:i+1],
                    'volume': data['volume'][:i+1],
                    'high': data['high'][:i+1],
                    'low': data['low'][:i+1]
                }
                
                signal = strategy.analyze(market_snapshot)
                
                if signal['action'] == 'buy' and position == 0:
                    position = capital / data['close'][i]
                    trades.append({
                        'type': 'buy',
                        'price': data['close'][i],
                        'time': i,
                        'confidence': signal['confidence']
                    })
                elif signal['action'] == 'sell' and position > 0:
                    capital = position * data['close'][i]
                    position = 0
                    trades.append({
                        'type': 'sell',
                        'price': data['close'][i],
                        'time': i,
                        'confidence': signal['confidence']
                    })
        
        # Close any open position
        if position > 0:
            capital = position * data['close'][-1]
        
        # Calculate metrics
        total_return = (capital - 10000) / 10000
        
        # Calculate daily returns for Sharpe ratio
        daily_returns = []
        if len(trades) > 1:
            for i in range(1, len(trades)):
                if trades[i]['type'] == 'sell' and trades[i-1]['type'] == 'buy':
                    ret = (trades[i]['price'] - trades[i-1]['price']) / trades[i-1]['price']
                    daily_returns.append(ret)
        
        sharpe_ratio = 0
        if daily_returns:
            sharpe_ratio = (np.mean(daily_returns) / np.std(daily_returns)) * np.sqrt(252) if np.std(daily_returns) > 0 else 0
        
        win_rate = sum(1 for r in daily_returns if r > 0) / len(daily_returns) if daily_returns else 0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate,
            'num_trades': len(trades),
            'final_capital': capital
        }
    
    async def evolve_strategies(self, results: List[Dict]):
        """Evolve strategies based on performance"""
        # Keep top performers
        top_performers = results[:self.num_strategies // 3]
        
        # Create new generation
        new_strategies = []
        
        # Keep elite strategies
        for result in top_performers:
            strategy = next(s for s in self.strategies if s.name == result['strategy'])
            new_strategies.append(strategy)
        
        # Create offspring through crossover and mutation
        while len(new_strategies) < self.num_strategies:
            # Select parents
            parent1 = random.choice(top_performers)['strategy']
            parent2 = random.choice(top_performers)['strategy']
            
            parent1_strategy = next(s for s in self.strategies if s.name == parent1)
            parent2_strategy = next(s for s in self.strategies if s.name == parent2)
            
            # Crossover
            child_genome = {}
            for key in parent1_strategy.genome:
                if random.random() < 0.5:
                    child_genome[key] = parent1_strategy.genome[key]
                else:
                    child_genome[key] = parent2_strategy.genome[key]
            
            # Create child and mutate
            child = PolymorphicStrategy(f"poly_strategy_gen{self.generation}_{len(new_strategies)}", child_genome)
            child.mutate()
            new_strategies.append(child)
        
        self.strategies = new_strategies
        logger.info(f"Evolved to generation {self.generation} with {len(self.strategies)} strategies")

async def main():
    """Run the historical learning swarm demonstration"""
    logger.info("=== Historical Learning Swarm Demo ===")
    logger.info("Demonstrating polymorphic strategy optimization through evolutionary learning")
    
    swarm = LearningSwarmDemo(num_strategies=10)
    swarm.initialize_strategies()
    
    # Run multiple learning cycles
    for cycle in range(5):
        logger.info(f"\n--- Learning Cycle {cycle + 1} ---")
        await swarm.run_learning_cycle(['BTC/USDT', 'ETH/USDT', 'SOL/USDT'], days=30)
        await asyncio.sleep(1)  # Brief pause between cycles
    
    # Show final results
    logger.info("\n=== Final Strategy Evolution Summary ===")
    best_strategies = sorted(swarm.strategies, 
                           key=lambda s: s.performance_history[-1]['sharpe_ratio'] if s.performance_history else 0, 
                           reverse=True)[:3]
    
    for i, strategy in enumerate(best_strategies):
        if strategy.performance_history:
            perf = strategy.performance_history[-1]
            logger.info(f"\nTop {i+1}: {strategy.name}")
            logger.info(f"  - Adaptations: {strategy.adaptation_count}")
            logger.info(f"  - Final Return: {perf['total_return']:.2%}")
            logger.info(f"  - Sharpe Ratio: {perf['sharpe_ratio']:.2f}")
            logger.info(f"  - Genome: {json.dumps(strategy.genome, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())