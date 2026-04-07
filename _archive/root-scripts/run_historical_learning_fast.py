"""
Fast demo of historical learning swarm with polymorphic strategies
Reduced data size for quicker execution
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
    def generate_price_data(symbol: str, days: int = 7):
        """Generate realistic price movements - reduced to hourly candles"""
        base_price = {'BTC/USDT': 40000, 'ETH/USDT': 2500, 'SOL/USDT': 100}.get(symbol, 100)
        timestamps = []
        prices = []
        volumes = []
        
        current_time = datetime.now() - timedelta(days=days)
        current_price = base_price
        
        # Generate hourly candles instead of minute candles
        for _ in range(days * 24):  # Hourly candles
            # Random walk with trend
            change = random.gauss(0, 0.01)  # 1% std dev
            trend = 0.0001  # Slight upward trend
            current_price *= (1 + change + trend)
            
            timestamps.append(current_time)
            prices.append(current_price)
            volumes.append(random.uniform(1000, 10000) * base_price)
            
            current_time += timedelta(hours=1)
        
        return {
            'timestamp': timestamps,
            'close': prices,
            'volume': volumes,
            'high': [p * 1.002 for p in prices],
            'low': [p * 0.998 for p in prices],
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
        if len(prices) < 20:
            return {'action': 'hold', 'confidence': 0}
        
        # Simple momentum-based decision
        recent_return = (prices[-1] - prices[-5]) / prices[-5]
        volatility = np.std(prices[-20:]) / np.mean(prices[-20:])
        
        signal_strength = 0
        
        # Momentum signal
        if recent_return > self.genome['momentum_threshold']:
            signal_strength += self.genome['momentum_weight']
        elif recent_return < -self.genome['momentum_threshold']:
            signal_strength -= self.genome['momentum_weight']
        
        # Volatility adjustment
        if volatility < self.genome['low_vol_threshold']:
            signal_strength *= self.genome['low_vol_multiplier']
        elif volatility > self.genome['high_vol_threshold']:
            signal_strength *= self.genome['high_vol_multiplier']
        
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
        mutation_rate = 0.2
        for key, value in self.genome.items():
            if random.random() < mutation_rate:
                if isinstance(value, float):
                    self.genome[key] *= random.uniform(0.85, 1.15)
        
        logger.info(f"Strategy {self.name} mutated (adaptation #{self.adaptation_count})")

class LearningSwarmDemo:
    """Demonstrates historical learning swarm with polymorphic strategies"""
    
    def __init__(self, num_strategies: int = 5):
        self.strategies = []
        self.num_strategies = num_strategies
        self.generation = 0
        
    def initialize_strategies(self):
        """Create initial population of strategies with diverse genomes"""
        base_genomes = [
            {
                'momentum_threshold': 0.02,
                'momentum_weight': 0.7,
                'low_vol_threshold': 0.01,
                'high_vol_threshold': 0.05,
                'low_vol_multiplier': 1.5,
                'high_vol_multiplier': 0.5,
                'action_threshold': 0.5
            },
            {
                'momentum_threshold': 0.01,
                'momentum_weight': 0.5,
                'low_vol_threshold': 0.02,
                'high_vol_threshold': 0.04,
                'low_vol_multiplier': 1.2,
                'high_vol_multiplier': 0.8,
                'action_threshold': 0.4
            }
        ]
        
        # Create strategies with variations
        for i in range(self.num_strategies):
            base = base_genomes[i % len(base_genomes)].copy()
            
            # Add random variations
            for key in base:
                base[key] *= random.uniform(0.8, 1.2)
            
            strategy = PolymorphicStrategy(f"poly_strat_{i}", base)
            self.strategies.append(strategy)
        
        logger.info(f"Initialized {self.num_strategies} polymorphic strategies")
    
    async def run_learning_cycle(self, symbols: List[str], days: int = 7):
        """Run a complete learning cycle"""
        logger.info(f"\n🔄 Generation {self.generation} Learning Cycle")
        
        # Generate simulated data
        market_data = {}
        for symbol in symbols:
            market_data[symbol] = SimulatedDataProvider.generate_price_data(symbol, days)
            logger.info(f"  📊 Generated {len(market_data[symbol]['close'])} hourly candles for {symbol}")
        
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
        logger.info(f"\n📈 Generation {self.generation} Performance:")
        for i, result in enumerate(results):
            emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "  "
            logger.info(f"{emoji} {result['strategy']}: "
                       f"Return={result['total_return']:.1%}, "
                       f"Sharpe={result['sharpe_ratio']:.2f}, "
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
            for i in range(20, len(data['close'])):
                market_snapshot = {
                    'close': data['close'][:i+1],
                    'volume': data['volume'][:i+1]
                }
                
                signal = strategy.analyze(market_snapshot)
                
                if signal['action'] == 'buy' and position == 0:
                    position = capital / data['close'][i]
                    trades.append({
                        'type': 'buy',
                        'price': data['close'][i],
                        'time': i
                    })
                elif signal['action'] == 'sell' and position > 0:
                    capital = position * data['close'][i]
                    position = 0
                    trades.append({
                        'type': 'sell',
                        'price': data['close'][i],
                        'time': i
                    })
        
        # Close any open position
        if position > 0:
            capital = position * data['close'][-1]
        
        # Calculate metrics
        total_return = (capital - 10000) / 10000
        
        # Calculate returns for Sharpe ratio
        returns = []
        if len(trades) > 1:
            for i in range(1, len(trades)):
                if trades[i]['type'] == 'sell' and trades[i-1]['type'] == 'buy':
                    ret = (trades[i]['price'] - trades[i-1]['price']) / trades[i-1]['price']
                    returns.append(ret)
        
        sharpe_ratio = 0
        if returns:
            sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        win_rate = sum(1 for r in returns if r > 0) / len(returns) if returns else 0
        
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
        top_performers = results[:2]
        
        # Create new generation
        new_strategies = []
        
        # Keep elite strategies
        for result in top_performers:
            strategy = next(s for s in self.strategies if s.name == result['strategy'])
            new_strategies.append(strategy)
        
        # Create offspring
        while len(new_strategies) < self.num_strategies:
            # Clone and mutate top performer
            parent = random.choice(top_performers)['strategy']
            parent_strategy = next(s for s in self.strategies if s.name == parent)
            
            child_genome = parent_strategy.genome.copy()
            child = PolymorphicStrategy(f"poly_strat_g{self.generation}_{len(new_strategies)}", child_genome)
            child.mutate()
            new_strategies.append(child)
        
        self.strategies = new_strategies
        logger.info(f"  🧬 Evolved {len(self.strategies)} strategies to next generation")

async def main():
    """Run the historical learning swarm demonstration"""
    logger.info("🚀 Historical Learning Swarm - Polymorphic Strategy Optimization")
    logger.info("=" * 60)
    
    swarm = LearningSwarmDemo(num_strategies=5)
    swarm.initialize_strategies()
    
    # Run multiple learning cycles
    for cycle in range(3):
        await swarm.run_learning_cycle(['BTC/USDT', 'ETH/USDT'], days=7)
        await asyncio.sleep(0.5)
    
    # Show final results
    logger.info("\n🏆 Final Strategy Evolution Summary")
    logger.info("=" * 60)
    
    best_strategies = sorted(swarm.strategies, 
                           key=lambda s: s.performance_history[-1]['sharpe_ratio'] if s.performance_history else 0, 
                           reverse=True)[:3]
    
    for i, strategy in enumerate(best_strategies):
        if strategy.performance_history:
            perf = strategy.performance_history[-1]
            logger.info(f"\n{'🥇' if i==0 else '🥈' if i==1 else '🥉'} {strategy.name}")
            logger.info(f"  • Adaptations: {strategy.adaptation_count}")
            logger.info(f"  • Final Return: {perf['total_return']:.1%}")
            logger.info(f"  • Sharpe Ratio: {perf['sharpe_ratio']:.2f}")
            logger.info(f"  • Win Rate: {perf['win_rate']:.0%}")
            logger.info("  • Evolved Genome:")
            for key, value in strategy.genome.items():
                logger.info(f"    - {key}: {value:.3f}")

if __name__ == "__main__":
    asyncio.run(main())