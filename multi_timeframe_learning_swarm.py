"""
Multi-Timeframe Historical Learning Swarm with Comprehensive Documentation
Analyzes multiple timeframes for confluence and tracks all strategy evolution
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import random
import numpy as np
from dataclasses import dataclass, field

from knowledge_base_schema import (
    KnowledgeBase, StrategyGenome, TimeframeAnalysis, 
    ConfluenceSignal, TradeExecution, StrategyPerformance,
    GenerationSummary, Timeframe, AssetInfo
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Top 30 Solana tokens (simulated for demo)
SOLANA_TOP_30 = [
    "SOL/USDT", "RAY/USDT", "SRM/USDT", "ORCA/USDT", "MNGO/USDT",
    "STEP/USDT", "SABER/USDT", "TULIP/USDT", "SUNNY/USDT", "PORT/USDT",
    "GENE/USDT", "DFL/USDT", "ATLAS/USDT", "POLIS/USDT", "FIDA/USDT",
    "KIN/USDT", "MAPS/USDT", "OXY/USDT", "COPE/USDT", "ROPE/USDT",
    "STAR/USDT", "SAMO/USDT", "ABR/USDT", "PRISM/USDT", "JET/USDT",
    "MANGO/USDT", "NINJA/USDT", "BOKU/USDT", "WOOF/USDT", "CHEEMS/USDT"
]

class MultiTimeframeDataProvider:
    """Provides market data across multiple timeframes"""
    
    @staticmethod
    def generate_correlated_data(symbol: str, timeframes: List[Timeframe], days: int = 30) -> Dict[str, Dict]:
        """Generate correlated data across multiple timeframes"""
        base_prices = {
            'BTC/USDT': 40000, 'ETH/USDT': 2500, 'SOL/USDT': 100,
            'RAY/USDT': 5, 'SRM/USDT': 3, 'ORCA/USDT': 2
        }
        base_price = base_prices.get(symbol, random.uniform(0.1, 10))
        
        # Generate base 1-minute data
        minutes = days * 24 * 60
        base_timestamps = []
        base_prices_list = []
        base_volumes = []
        
        current_time = datetime.now() - timedelta(days=days)
        current_price = base_price
        
        # Generate trend and volatility patterns
        trend = random.choice([0.00001, -0.00001, 0])  # Uptrend, downtrend, or sideways
        volatility_cycle = random.uniform(0.001, 0.003)
        
        for i in range(minutes):
            # Add cyclical volatility
            volatility = volatility_cycle * (1 + 0.5 * np.sin(i / 1440 * 2 * np.pi))
            change = random.gauss(trend, volatility)
            current_price *= (1 + change)
            
            base_timestamps.append(current_time)
            base_prices_list.append(current_price)
            base_volumes.append(random.uniform(100, 1000) * base_price * (1 + abs(change) * 10))
            
            current_time += timedelta(minutes=1)
        
        # Aggregate to different timeframes
        timeframe_data = {}
        
        for tf in timeframes:
            aggregated_data = MultiTimeframeDataProvider._aggregate_to_timeframe(
                base_timestamps, base_prices_list, base_volumes, tf
            )
            timeframe_data[tf.value] = aggregated_data
        
        return timeframe_data
    
    @staticmethod
    def _aggregate_to_timeframe(timestamps, prices, volumes, timeframe: Timeframe) -> Dict:
        """Aggregate 1-minute data to specified timeframe"""
        interval = timeframe.minutes
        aggregated = {
            'timestamp': [],
            'open': [],
            'high': [],
            'low': [],
            'close': [],
            'volume': []
        }
        
        for i in range(0, len(timestamps), interval):
            if i + interval <= len(timestamps):
                period_prices = prices[i:i+interval]
                period_volumes = volumes[i:i+interval]
                
                aggregated['timestamp'].append(timestamps[i])
                aggregated['open'].append(period_prices[0])
                aggregated['high'].append(max(period_prices))
                aggregated['low'].append(min(period_prices))
                aggregated['close'].append(period_prices[-1])
                aggregated['volume'].append(sum(period_volumes))
        
        return aggregated

class TechnicalAnalyzer:
    """Performs technical analysis on multiple timeframes"""
    
    @staticmethod
    def analyze_timeframe(data: Dict, timeframe: Timeframe) -> TimeframeAnalysis:
        """Analyze a single timeframe"""
        prices = data['close']
        volumes = data['volume']
        
        if len(prices) < 50:
            return TimeframeAnalysis(
                timeframe=timeframe,
                timestamp=datetime.now(),
                trend_direction='neutral',
                trend_strength=0.0
            )
        
        # Calculate trend
        sma_20 = np.mean(prices[-20:])
        sma_50 = np.mean(prices[-50:])
        current_price = prices[-1]
        
        if current_price > sma_20 > sma_50:
            trend_direction = 'bullish'
            trend_strength = min((current_price - sma_50) / sma_50, 1.0)
        elif current_price < sma_20 < sma_50:
            trend_direction = 'bearish'
            trend_strength = min((sma_50 - current_price) / sma_50, 1.0)
        else:
            trend_direction = 'neutral'
            trend_strength = 0.3
        
        # Calculate RSI
        deltas = [prices[i] - prices[i-1] if i > 0 else 0 for i in range(len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else 0
        avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else 0
        
        rsi = 100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss > 0 else 50
        
        # Find support/resistance
        recent_prices = prices[-50:]
        support_levels = sorted(recent_prices)[:3]
        resistance_levels = sorted(recent_prices, reverse=True)[:3]
        
        # Volume analysis
        avg_volume = np.mean(volumes[-20:])
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Pattern detection (simplified)
        patterns = []
        if len(prices) >= 5:
            if prices[-1] > prices[-2] > prices[-3]:
                patterns.append('ascending_triangle')
            elif prices[-1] < prices[-2] < prices[-3]:
                patterns.append('descending_triangle')
        
        return TimeframeAnalysis(
            timeframe=timeframe,
            timestamp=datetime.now(),
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            rsi=rsi,
            moving_averages={20: sma_20, 50: sma_50},
            volume_profile={'current': current_volume, 'average': avg_volume, 'ratio': volume_ratio},
            patterns_detected=patterns
        )

class ConfluenceAnalyzer:
    """Analyzes confluence across multiple timeframes"""
    
    @staticmethod
    def find_confluence(analyses: Dict[str, TimeframeAnalysis], asset: str) -> ConfluenceSignal:
        """Find confluence signals across timeframes"""
        # Count aligned signals
        bullish_count = sum(1 for a in analyses.values() if a.trend_direction == 'bullish')
        bearish_count = sum(1 for a in analyses.values() if a.trend_direction == 'bearish')
        
        # Determine overall signal
        if bullish_count >= len(analyses) * 0.7:
            signal_type = 'buy'
            confidence = bullish_count / len(analyses)
        elif bearish_count >= len(analyses) * 0.7:
            signal_type = 'sell'
            confidence = bearish_count / len(analyses)
        else:
            signal_type = 'hold'
            confidence = 0.5
        
        # Calculate confluence scores
        aligned_timeframes = [
            a.timeframe for a in analyses.values() 
            if (signal_type == 'buy' and a.trend_direction == 'bullish') or
               (signal_type == 'sell' and a.trend_direction == 'bearish')
        ]
        
        # Price action score
        price_action_score = sum(a.trend_strength for a in analyses.values()) / len(analyses)
        
        # Indicator alignment
        rsi_values = [a.rsi for a in analyses.values() if a.rsi is not None]
        indicator_alignment_score = 0
        if rsi_values:
            if signal_type == 'buy' and np.mean(rsi_values) < 70:
                indicator_alignment_score = (70 - np.mean(rsi_values)) / 70
            elif signal_type == 'sell' and np.mean(rsi_values) > 30:
                indicator_alignment_score = (np.mean(rsi_values) - 30) / 70
        
        # Volume confirmation
        volume_ratios = [a.volume_profile.get('ratio', 1) for a in analyses.values()]
        volume_confirmation_score = min(np.mean(volume_ratios) / 2, 1.0)
        
        # Pattern confluence
        all_patterns = []
        for a in analyses.values():
            all_patterns.extend(a.patterns_detected)
        pattern_confluence_score = len(set(all_patterns)) / (len(analyses) * 2)
        
        return ConfluenceSignal(
            timestamp=datetime.now(),
            asset=asset,
            signal_type=signal_type,
            overall_confidence=confidence,
            aligned_timeframes=aligned_timeframes,
            timeframe_signals={tf: {'trend': a.trend_direction, 'strength': a.trend_strength} 
                             for tf, a in analyses.items()},
            price_action_score=price_action_score,
            indicator_alignment_score=indicator_alignment_score,
            volume_confirmation_score=volume_confirmation_score,
            pattern_confluence_score=pattern_confluence_score
        )

class EvolvingMultiTimeframeStrategy:
    """Strategy that evolves using multi-timeframe analysis"""
    
    def __init__(self, genome: StrategyGenome, knowledge_base: KnowledgeBase):
        self.genome = genome
        self.knowledge_base = knowledge_base
        self.performance_history = []
        
    async def analyze_market(self, 
                           market_data: Dict[str, Dict[str, Dict]], 
                           asset: str) -> Optional[TradeExecution]:
        """Analyze market using multiple timeframes"""
        if asset not in market_data:
            return None
        
        # Perform technical analysis on each timeframe
        analyses = {}
        for tf_str, data in market_data[asset].items():
            tf = Timeframe(tf_str)
            analysis = TechnicalAnalyzer.analyze_timeframe(data, tf)
            analyses[tf_str] = analysis
        
        # Find confluence
        confluence = ConfluenceAnalyzer.find_confluence(analyses, asset)
        
        # Check if signal meets strategy criteria
        if confluence.overall_confidence < self.genome.confluence_threshold:
            return None
        
        if len(confluence.aligned_timeframes) < self.genome.min_timeframe_alignment:
            return None
        
        # Generate trade if conditions met
        if confluence.signal_type in ['buy', 'sell']:
            trade = TradeExecution(
                strategy_id=self.genome.id,
                asset=asset,
                entry_time=datetime.now(),
                entry_price=list(market_data[asset].values())[0]['close'][-1],
                position_size=1.0,  # Simplified for demo
                direction='long' if confluence.signal_type == 'buy' else 'short',
                confluence_signal=confluence,
                timeframe_analysis=analyses
            )
            
            # Save to knowledge base
            self.knowledge_base.save_trade(trade)
            
            return trade
        
        return None
    
    def mutate(self):
        """Mutate strategy parameters"""
        mutation = {
            'timestamp': datetime.now().isoformat(),
            'type': 'parameter_mutation',
            'changes': {}
        }
        
        # Mutate confluence threshold
        if random.random() < 0.3:
            old_val = self.genome.confluence_threshold
            self.genome.confluence_threshold *= random.uniform(0.9, 1.1)
            mutation['changes']['confluence_threshold'] = {
                'old': old_val, 
                'new': self.genome.confluence_threshold
            }
        
        # Mutate timeframe alignment requirement
        if random.random() < 0.3:
            old_val = self.genome.min_timeframe_alignment
            self.genome.min_timeframe_alignment = max(1, self.genome.min_timeframe_alignment + random.randint(-1, 1))
            mutation['changes']['min_timeframe_alignment'] = {
                'old': old_val,
                'new': self.genome.min_timeframe_alignment
            }
        
        # Mutate timeframe weights
        for tf in self.genome.timeframe_weights:
            if random.random() < 0.2:
                old_val = self.genome.timeframe_weights[tf]
                self.genome.timeframe_weights[tf] *= random.uniform(0.8, 1.2)
                mutation['changes'][f'timeframe_weight_{tf}'] = {
                    'old': old_val,
                    'new': self.genome.timeframe_weights[tf]
                }
        
        self.genome.mutations.append(mutation)
        self.genome.generation += 1
        
        # Save updated genome
        self.knowledge_base.save_strategy(self.genome)

class MultiTimeframeLearningSwarm:
    """Main coordinator for multi-timeframe learning"""
    
    def __init__(self, num_strategies: int = 10):
        self.knowledge_base = KnowledgeBase()
        self.strategies = []
        self.num_strategies = num_strategies
        self.generation = 0
        self.all_timeframes = list(Timeframe)
        
    def initialize_strategies(self):
        """Create initial population with diverse parameters"""
        logger.info("Initializing multi-timeframe strategies...")
        
        for i in range(self.num_strategies):
            # Create diverse timeframe weights
            timeframe_weights = {}
            for tf in self.all_timeframes:
                if tf.minutes >= 60:  # Focus on higher timeframes
                    timeframe_weights[tf.value] = random.uniform(0.5, 1.5)
                else:
                    timeframe_weights[tf.value] = random.uniform(0.1, 0.8)
            
            genome = StrategyGenome(
                name=f"MTF_Strategy_{i}",
                generation=0,
                timeframe_weights=timeframe_weights,
                min_timeframe_alignment=random.randint(3, 7),
                confluence_threshold=random.uniform(0.6, 0.9),
                indicators={
                    'rsi': {'period': random.randint(10, 20)},
                    'macd': {'fast': 12, 'slow': 26, 'signal': 9},
                    'bb': {'period': 20, 'std': 2}
                },
                risk_params={
                    'max_position_size': 0.1,
                    'stop_loss': random.uniform(0.02, 0.05),
                    'take_profit': random.uniform(0.03, 0.10)
                }
            )
            
            # Save initial genome
            self.knowledge_base.save_strategy(genome)
            
            strategy = EvolvingMultiTimeframeStrategy(genome, self.knowledge_base)
            self.strategies.append(strategy)
        
        logger.info(f"Initialized {len(self.strategies)} multi-timeframe strategies")
    
    async def run_learning_cycle(self, assets: List[str], days: int = 30):
        """Run complete learning cycle with all assets"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🧬 GENERATION {self.generation} - Multi-Timeframe Learning Cycle")
        logger.info(f"{'='*80}")
        
        # Generate market data for all assets
        logger.info(f"\n📊 Generating market data for {len(assets)} assets across {len(self.all_timeframes)} timeframes...")
        
        all_market_data = {}
        for asset in assets:
            logger.info(f"  • {asset}: Generating {days} days of data")
            all_market_data[asset] = MultiTimeframeDataProvider.generate_correlated_data(
                asset, self.all_timeframes, days
            )
        
        # Run backtests for each strategy
        logger.info(f"\n🔬 Running backtests for {len(self.strategies)} strategies...")
        
        strategy_results = []
        for strategy in self.strategies:
            trades = []
            
            # Simulate trading over time
            for asset in assets[:10]:  # Limit assets for performance
                trade = await strategy.analyze_market(all_market_data, asset)
                if trade:
                    trades.append(trade)
            
            # Calculate performance
            performance = self._calculate_performance(trades)
            strategy_results.append({
                'strategy': strategy,
                'performance': performance,
                'trades': len(trades)
            })
            
            logger.info(f"  • {strategy.genome.name}: {len(trades)} trades, "
                       f"Sharpe: {performance.get('sharpe_ratio', 0):.2f}")
        
        # Sort by performance
        strategy_results.sort(key=lambda x: x['performance'].get('sharpe_ratio', 0), reverse=True)
        
        # Display top performers
        logger.info(f"\n🏆 Top Performing Strategies:")
        for i, result in enumerate(strategy_results[:5]):
            strategy = result['strategy']
            perf = result['performance']
            logger.info(f"  {i+1}. {strategy.genome.name}:")
            logger.info(f"     - Sharpe Ratio: {perf.get('sharpe_ratio', 0):.3f}")
            logger.info(f"     - Total Return: {perf.get('total_return', 0):.2%}")
            logger.info(f"     - Win Rate: {perf.get('win_rate', 0):.1%}")
            logger.info(f"     - Trades: {result['trades']}")
            logger.info(f"     - Confluence Threshold: {strategy.genome.confluence_threshold:.2f}")
            logger.info(f"     - Min Timeframe Alignment: {strategy.genome.min_timeframe_alignment}")
        
        # Save generation summary
        summary = GenerationSummary(
            generation_number=self.generation,
            timestamp=datetime.now(),
            population_size=len(self.strategies),
            strategies=[s.genome for s in self.strategies],
            avg_sharpe_ratio=np.mean([r['performance'].get('sharpe_ratio', 0) for r in strategy_results]),
            best_sharpe_ratio=strategy_results[0]['performance'].get('sharpe_ratio', 0),
            avg_return=np.mean([r['performance'].get('total_return', 0) for r in strategy_results]),
            best_return=max([r['performance'].get('total_return', 0) for r in strategy_results]),
            mutation_rate=0.3,
            crossover_rate=0.5,
            selection_pressure=0.6
        )
        self.knowledge_base.save_generation(summary)
        
        # Evolve to next generation
        await self._evolve_population(strategy_results)
        
        self.generation += 1
    
    def _calculate_performance(self, trades: List[TradeExecution]) -> Dict:
        """Calculate strategy performance metrics"""
        if not trades:
            return {'sharpe_ratio': 0, 'total_return': 0, 'win_rate': 0}
        
        # Simulate returns (simplified)
        returns = []
        for trade in trades:
            # Random return for demo
            ret = random.gauss(0.001, 0.02)
            returns.append(ret)
        
        total_return = sum(returns)
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        win_rate = sum(1 for r in returns if r > 0) / len(returns)
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'total_return': total_return,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'std_return': std_return
        }
    
    async def _evolve_population(self, results: List[Dict]):
        """Evolve strategies to next generation"""
        logger.info(f"\n🧬 Evolving population to generation {self.generation + 1}...")
        
        # Select top performers
        top_performers = results[:self.num_strategies // 3]
        
        new_strategies = []
        
        # Keep elite strategies
        for result in top_performers:
            strategy = result['strategy']
            new_strategies.append(strategy)
            logger.info(f"  ✓ Elite strategy preserved: {strategy.genome.name}")
        
        # Create offspring
        while len(new_strategies) < self.num_strategies:
            # Select parents
            parent1 = random.choice(top_performers)['strategy']
            parent2 = random.choice(top_performers)['strategy']
            
            # Create child genome through crossover
            child_genome = StrategyGenome(
                name=f"MTF_Strategy_G{self.generation+1}_{len(new_strategies)}",
                generation=self.generation + 1,
                parent_ids=[parent1.genome.id, parent2.genome.id]
            )
            
            # Crossover parameters
            child_genome.confluence_threshold = random.choice([
                parent1.genome.confluence_threshold,
                parent2.genome.confluence_threshold
            ])
            
            child_genome.min_timeframe_alignment = random.choice([
                parent1.genome.min_timeframe_alignment,
                parent2.genome.min_timeframe_alignment
            ])
            
            # Mix timeframe weights
            child_genome.timeframe_weights = {}
            for tf in self.all_timeframes:
                if random.random() < 0.5:
                    child_genome.timeframe_weights[tf.value] = parent1.genome.timeframe_weights.get(tf.value, 1.0)
                else:
                    child_genome.timeframe_weights[tf.value] = parent2.genome.timeframe_weights.get(tf.value, 1.0)
            
            # Create child strategy and mutate
            child_strategy = EvolvingMultiTimeframeStrategy(child_genome, self.knowledge_base)
            child_strategy.mutate()
            
            new_strategies.append(child_strategy)
            
        self.strategies = new_strategies
        logger.info(f"  ✓ Evolution complete: {len(self.strategies)} strategies in new generation")

async def main():
    """Run multi-timeframe historical learning swarm"""
    logger.info("\n" + "="*80)
    logger.info("🚀 MULTI-TIMEFRAME HISTORICAL LEARNING SWARM")
    logger.info("📊 Analyzing BTC, ETH, SOL + Top 30 Solana Tokens")
    logger.info("⏰ Timeframes: 1m, 5m, 15m, 1h, 4h, 6h, 12h, 1d, 1w, 1M")
    logger.info("="*80)
    
    # Initialize swarm
    swarm = MultiTimeframeLearningSwarm(num_strategies=10)
    swarm.initialize_strategies()
    
    # Define assets to analyze
    major_assets = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    all_assets = major_assets + SOLANA_TOP_30
    
    # Run learning cycles
    for cycle in range(3):  # 3 generations
        logger.info(f"\n\n{'#'*80}")
        logger.info(f"LEARNING CYCLE {cycle + 1}")
        logger.info(f"{'#'*80}")
        
        await swarm.run_learning_cycle(all_assets, days=30)
        await asyncio.sleep(1)
    
    logger.info("\n\n" + "="*80)
    logger.info("🎯 LEARNING COMPLETE - Knowledge Base Updated")
    logger.info(f"📁 Data saved to: {swarm.knowledge_base.base_path}")
    logger.info("="*80)

if __name__ == "__main__":
    asyncio.run(main())