"""
Enhanced Multi-Timeframe Learning Swarm with Comprehensive Performance Tracking
Includes full statistics, opportunity cost analysis, and detailed trade records
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import random
import numpy as np
import uuid

from knowledge_base_schema import (
    KnowledgeBase, StrategyGenome, TimeframeAnalysis, 
    ConfluenceSignal, TradeExecution, Timeframe
)
from enhanced_performance_tracker import (
    TradeRecord, StrategyPerformanceMetrics, 
    PerformanceAnalyzer, EnhancedBacktester
)
from multi_timeframe_learning_swarm import (
    MultiTimeframeDataProvider, TechnicalAnalyzer, 
    ConfluenceAnalyzer, SOLANA_TOP_30
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTradingSimulator:
    """Simulates realistic trading with full statistics tracking"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades: List[TradeRecord] = []
        self.open_positions: Dict[str, TradeRecord] = {}
        
    async def simulate_trading(self, 
                             strategy: 'EnhancedMultiTimeframeStrategy',
                             market_data: Dict[str, Dict[str, Dict]],
                             days: int = 30) -> List[TradeRecord]:
        """Simulate trading over historical data"""
        # Reset for new simulation
        self.current_capital = self.initial_capital
        self.trades = []
        self.open_positions = {}
        
        # Get time series for simulation
        all_timestamps = set()
        for asset in market_data:
            if '1h' in market_data[asset]:  # Use hourly data for simulation
                timestamps = market_data[asset]['1h']['timestamp']
                all_timestamps.update(timestamps)
        
        sorted_timestamps = sorted(all_timestamps)
        
        # Simulate trading at each timestamp
        for timestamp in sorted_timestamps:
            # Update market data to current timestamp
            current_market_data = self._get_data_at_timestamp(market_data, timestamp)
            
            # Check for exit signals on open positions
            await self._check_exits(current_market_data, timestamp)
            
            # Look for new entry signals
            for asset in list(market_data.keys())[:10]:  # Limit to 10 assets for performance
                if asset not in self.open_positions and self.current_capital > 1000:
                    # Analyze market
                    signal = await strategy.analyze_market_enhanced(current_market_data, asset, timestamp)
                    
                    if signal and signal['action'] in ['buy', 'sell']:
                        # Calculate position size (risk 2% per trade)
                        position_size = self.current_capital * 0.02 / signal.get('stop_loss_distance', 0.02)
                        position_size = min(position_size, self.current_capital * 0.1)  # Max 10% per position
                        
                        # Create trade record
                        trade = TradeRecord(
                            id=str(uuid.uuid4()),
                            strategy_id=strategy.genome.id,
                            asset=asset,
                            entry_time=timestamp,
                            entry_price=signal['price'],
                            exit_time=None,  # Will be set when trade closes
                            exit_price=None,  # Will be set when trade closes
                            position_size=position_size,
                            direction='long' if signal['action'] == 'buy' else 'short',
                            stop_loss=signal.get('stop_loss'),
                            take_profit=signal.get('take_profit'),
                            risk_reward_ratio=signal.get('risk_reward_ratio', 2.0)
                        )
                        
                        self.open_positions[asset] = trade
                        self.current_capital -= position_size * 0.001  # Trading fees
        
        # Close any remaining open positions
        final_timestamp = sorted_timestamps[-1]
        await self._close_all_positions(market_data, final_timestamp)
        
        return self.trades
    
    def _get_data_at_timestamp(self, market_data: Dict, timestamp: datetime) -> Dict:
        """Get market data up to specified timestamp"""
        current_data = {}
        
        for asset in market_data:
            current_data[asset] = {}
            for timeframe, data in market_data[asset].items():
                # Find index for current timestamp
                timestamps = data['timestamp']
                idx = 0
                for i, ts in enumerate(timestamps):
                    if ts <= timestamp:
                        idx = i
                    else:
                        break
                
                # Get data up to current timestamp
                if idx > 0:
                    current_data[asset][timeframe] = {
                        'timestamp': timestamps[:idx+1],
                        'open': data['open'][:idx+1],
                        'high': data['high'][:idx+1],
                        'low': data['low'][:idx+1],
                        'close': data['close'][:idx+1],
                        'volume': data['volume'][:idx+1]
                    }
        
        return current_data
    
    async def _check_exits(self, market_data: Dict, timestamp: datetime):
        """Check exit conditions for open positions"""
        for asset, trade in list(self.open_positions.items()):
            if asset in market_data and '1h' in market_data[asset]:
                current_price = market_data[asset]['1h']['close'][-1]
                
                # Check stop loss and take profit
                should_exit = False
                exit_reason = None
                
                if trade.direction == 'long':
                    if trade.stop_loss and current_price <= trade.stop_loss:
                        should_exit = True
                        exit_reason = 'stop_loss'
                    elif trade.take_profit and current_price >= trade.take_profit:
                        should_exit = True
                        exit_reason = 'take_profit'
                    elif (timestamp - trade.entry_time).days > 5:  # Time-based exit
                        should_exit = True
                        exit_reason = 'time_limit'
                else:  # short
                    if trade.stop_loss and current_price >= trade.stop_loss:
                        should_exit = True
                        exit_reason = 'stop_loss'
                    elif trade.take_profit and current_price <= trade.take_profit:
                        should_exit = True
                        exit_reason = 'take_profit'
                
                if should_exit:
                    trade.exit_time = timestamp
                    trade.exit_price = current_price
                    trade.calculate_pnl()
                    
                    # Update capital
                    self.current_capital += trade.position_size + (trade.pnl_dollars or 0)
                    self.current_capital -= trade.position_size * 0.001  # Exit fees
                    
                    # Track high/low during trade
                    prices_during_trade = market_data[asset]['1h']['close']
                    if trade.direction == 'long':
                        max_price = max(prices_during_trade)
                        min_price = min(prices_during_trade)
                        trade.max_profit_dollars = trade.position_size * (max_price - trade.entry_price) / trade.entry_price
                        trade.max_drawdown_dollars = trade.position_size * (trade.entry_price - min_price) / trade.entry_price
                    
                    self.trades.append(trade)
                    del self.open_positions[asset]
    
    async def _close_all_positions(self, market_data: Dict, timestamp: datetime):
        """Close all open positions at end of simulation"""
        for asset, trade in list(self.open_positions.items()):
            if asset in market_data and '1h' in market_data[asset]:
                trade.exit_time = timestamp
                trade.exit_price = market_data[asset]['1h']['close'][-1]
                trade.calculate_pnl()
                self.trades.append(trade)

class EnhancedMultiTimeframeStrategy:
    """Enhanced strategy with comprehensive signal generation"""
    
    def __init__(self, genome: StrategyGenome, knowledge_base: KnowledgeBase):
        self.genome = genome
        self.knowledge_base = knowledge_base
        
    async def analyze_market_enhanced(self, 
                                    market_data: Dict[str, Dict[str, Dict]], 
                                    asset: str,
                                    current_time: datetime) -> Optional[Dict]:
        """Enhanced market analysis with risk management"""
        if asset not in market_data:
            return None
        
        # Perform technical analysis on each timeframe
        analyses = {}
        for tf_str, data in market_data[asset].items():
            if len(data.get('close', [])) > 50:
                tf = Timeframe(tf_str)
                analysis = TechnicalAnalyzer.analyze_timeframe(data, tf)
                analyses[tf_str] = analysis
        
        if not analyses:
            return None
        
        # Find confluence
        confluence = ConfluenceAnalyzer.find_confluence(analyses, asset)
        
        # Check if signal meets strategy criteria
        if confluence.overall_confidence < self.genome.confluence_threshold:
            return None
        
        if len(confluence.aligned_timeframes) < self.genome.min_timeframe_alignment:
            return None
        
        # Generate enhanced signal with risk management
        if confluence.signal_type in ['buy', 'sell']:
            current_price = list(market_data[asset].values())[0]['close'][-1]
            
            # Calculate stop loss and take profit based on ATR or recent volatility
            recent_prices = list(market_data[asset].values())[0]['close'][-20:]
            volatility = np.std(recent_prices) / np.mean(recent_prices)
            
            # Dynamic stop loss based on volatility
            stop_distance = volatility * 2  # 2x volatility
            take_profit_distance = stop_distance * 3  # 3:1 risk-reward
            
            if confluence.signal_type == 'buy':
                stop_loss = current_price * (1 - stop_distance)
                take_profit = current_price * (1 + take_profit_distance)
            else:  # sell
                stop_loss = current_price * (1 + stop_distance)
                take_profit = current_price * (1 - take_profit_distance)
            
            return {
                'action': confluence.signal_type,
                'price': current_price,
                'confidence': confluence.overall_confidence,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'stop_loss_distance': stop_distance,
                'risk_reward_ratio': 3.0,
                'confluence_score': {
                    'price_action': confluence.price_action_score,
                    'indicators': confluence.indicator_alignment_score,
                    'volume': confluence.volume_confirmation_score,
                    'patterns': confluence.pattern_confluence_score
                },
                'aligned_timeframes': len(confluence.aligned_timeframes),
                'timestamp': current_time
            }
        
        return None

class EnhancedLearningSwarm:
    """Enhanced learning swarm with full performance tracking"""
    
    def __init__(self, num_strategies: int = 10):
        self.knowledge_base = KnowledgeBase()
        self.strategies = []
        self.num_strategies = num_strategies
        self.generation = 0
        self.all_timeframes = list(Timeframe)
        self.performance_history = []
        
    def initialize_strategies(self):
        """Initialize strategies with diverse parameters"""
        logger.info("🚀 Initializing enhanced multi-timeframe strategies...")
        
        for i in range(self.num_strategies):
            # Create diverse genomes
            genome = StrategyGenome(
                name=f"Enhanced_MTF_Strategy_{i}",
                generation=0,
                timeframe_weights={tf.value: random.uniform(0.1, 1.5) for tf in self.all_timeframes},
                min_timeframe_alignment=random.randint(3, 7),
                confluence_threshold=random.uniform(0.6, 0.9),
                risk_params={
                    'max_position_size': 0.1,
                    'max_daily_loss': 0.05,
                    'risk_per_trade': 0.02
                }
            )
            
            self.knowledge_base.save_strategy(genome)
            strategy = EnhancedMultiTimeframeStrategy(genome, self.knowledge_base)
            self.strategies.append(strategy)
    
    async def run_enhanced_learning_cycle(self, assets: List[str], days: int = 30):
        """Run learning cycle with comprehensive performance tracking"""
        logger.info(f"\n{'='*100}")
        logger.info(f"🧬 GENERATION {self.generation} - Enhanced Learning Cycle with Full Statistics")
        logger.info(f"{'='*100}")
        
        # Generate market data
        logger.info(f"\n📊 Generating {days} days of market data for {len(assets)} assets...")
        all_market_data = {}
        
        # Track buy-and-hold prices for opportunity cost
        buy_hold_prices = {}
        
        for asset in assets[:15]:  # Limit for performance
            market_data = MultiTimeframeDataProvider.generate_correlated_data(
                asset, self.all_timeframes, days
            )
            all_market_data[asset] = market_data
            
            # Record start/end prices for buy-and-hold comparison
            if asset in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
                hourly_data = market_data['1h']
                buy_hold_prices[asset] = {
                    'start': hourly_data['close'][0],
                    'end': hourly_data['close'][-1]
                }
        
        # Run simulations for each strategy
        logger.info(f"\n💹 Running trading simulations for {len(self.strategies)} strategies...")
        
        strategy_results = []
        for i, strategy in enumerate(self.strategies):
            # Run simulation
            simulator = EnhancedTradingSimulator(initial_capital=10000)
            trades = await simulator.simulate_trading(strategy, all_market_data, days)
            
            # Analyze performance
            backtester = EnhancedBacktester(initial_capital=10000)
            backtester.set_buy_hold_prices(buy_hold_prices)
            
            if trades:
                performance_report = backtester.run_backtest_with_full_metrics(trades)
                
                strategy_results.append({
                    'strategy': strategy,
                    'trades': trades,
                    'performance': performance_report
                })
                
                # Save detailed performance to knowledge base
                self._save_performance_report(strategy.genome.id, performance_report)
            else:
                strategy_results.append({
                    'strategy': strategy,
                    'trades': [],
                    'performance': None
                })
            
            if i < 3:  # Show first 3 strategies
                self._display_strategy_performance(strategy.genome.name, performance_report, trades)
        
        # Display generation summary
        self._display_generation_summary(strategy_results, buy_hold_prices)
        
        # Save generation data
        self._save_generation_data(strategy_results)
        
        # Evolve population
        await self._evolve_with_performance_focus(strategy_results)
        
        self.generation += 1
    
    def _display_strategy_performance(self, name: str, report: Dict, trades: List[TradeRecord]):
        """Display comprehensive performance for a strategy"""
        if not report:
            logger.info(f"\n❌ {name}: No trades executed")
            return
        
        logger.info(f"\n📈 {name} Performance:")
        logger.info(f"   💰 Capital: ${report['capital']['initial']} → ${report['capital']['final']}")
        logger.info(f"   📊 Total Return: {report['capital']['total_growth_percentage']}")
        logger.info(f"   🎯 Win Rate: {report['trade_statistics']['win_rate']} ({report['trade_statistics']['winning_trades']}/{report['trade_statistics']['total_trades']})")
        logger.info(f"   💵 Net P&L: {report['dollar_pnl']['net_pnl']}")
        logger.info(f"   📉 Max Drawdown: {report['risk_metrics']['max_drawdown_percentage']}")
        logger.info(f"   📐 Sharpe Ratio: {report['risk_metrics']['sharpe_ratio']}")
        logger.info(f"   🆚 vs BTC: {report['opportunity_cost_analysis']['vs_btc']['opportunity_cost']} {'✅' if report['opportunity_cost_analysis']['vs_btc']['outperformed'] else '❌'}")
    
    def _display_generation_summary(self, results: List[Dict], buy_hold_prices: Dict):
        """Display comprehensive generation summary"""
        logger.info(f"\n{'='*100}")
        logger.info(f"📊 GENERATION {self.generation} SUMMARY")
        logger.info(f"{'='*100}")
        
        # Calculate aggregate statistics
        total_trades = sum(len(r['trades']) for r in results)
        profitable_strategies = sum(1 for r in results if r['performance'] and 
                                  float(r['performance']['capital']['total_growth_percentage'].strip('%')) > 0)
        
        # Buy and hold returns
        btc_return = (buy_hold_prices['BTC/USDT']['end'] - buy_hold_prices['BTC/USDT']['start']) / buy_hold_prices['BTC/USDT']['start']
        eth_return = (buy_hold_prices['ETH/USDT']['end'] - buy_hold_prices['ETH/USDT']['start']) / buy_hold_prices['ETH/USDT']['start']
        sol_return = (buy_hold_prices['SOL/USDT']['end'] - buy_hold_prices['SOL/USDT']['start']) / buy_hold_prices['SOL/USDT']['start']
        
        logger.info(f"\n🎯 Overall Statistics:")
        logger.info(f"   • Total Trades Executed: {total_trades}")
        logger.info(f"   • Profitable Strategies: {profitable_strategies}/{len(results)}")
        
        logger.info(f"\n📈 Buy & Hold Benchmark Returns:")
        logger.info(f"   • BTC: {btc_return:.2%}")
        logger.info(f"   • ETH: {eth_return:.2%}")
        logger.info(f"   • SOL: {sol_return:.2%}")
        
        # Top performers
        valid_results = [r for r in results if r['performance']]
        if valid_results:
            # Sort by Sharpe ratio
            sorted_by_sharpe = sorted(valid_results, 
                                    key=lambda x: float(x['performance']['risk_metrics']['sharpe_ratio']), 
                                    reverse=True)
            
            logger.info(f"\n🏆 Top 3 Strategies by Sharpe Ratio:")
            for i, result in enumerate(sorted_by_sharpe[:3]):
                perf = result['performance']
                logger.info(f"\n   {i+1}. {result['strategy'].genome.name}:")
                logger.info(f"      • Sharpe: {perf['risk_metrics']['sharpe_ratio']}")
                logger.info(f"      • Return: {perf['capital']['total_growth_percentage']}")
                logger.info(f"      • Trades: {perf['trade_statistics']['total_trades']}")
                logger.info(f"      • Win Rate: {perf['trade_statistics']['win_rate']}")
                logger.info(f"      • Max DD: {perf['risk_metrics']['max_drawdown_percentage']}")
                
                # Show if it beat buy-and-hold
                vs_btc = perf['opportunity_cost_analysis']['vs_btc']
                vs_eth = perf['opportunity_cost_analysis']['vs_eth']
                vs_sol = perf['opportunity_cost_analysis']['vs_sol']
                
                logger.info(f"      • Beat BTC: {'✅' if vs_btc['outperformed'] else '❌'} ({vs_btc['opportunity_cost']})")
                logger.info(f"      • Beat ETH: {'✅' if vs_eth['outperformed'] else '❌'} ({vs_eth['opportunity_cost']})")
                logger.info(f"      • Beat SOL: {'✅' if vs_sol['outperformed'] else '❌'} ({vs_sol['opportunity_cost']})")
    
    def _save_performance_report(self, strategy_id: str, report: Dict):
        """Save detailed performance report to knowledge base"""
        if report:
            filename = f"performance_gen{self.generation}_{strategy_id}.json"
            path = os.path.join(self.knowledge_base.base_path, 'performance', filename)
            with open(path, 'w') as f:
                json.dump(report, f, indent=2)
    
    def _save_generation_data(self, results: List[Dict]):
        """Save complete generation data"""
        generation_data = {
            'generation': self.generation,
            'timestamp': datetime.now().isoformat(),
            'strategies': []
        }
        
        for result in results:
            if result['performance']:
                strategy_data = {
                    'id': result['strategy'].genome.id,
                    'name': result['strategy'].genome.name,
                    'total_trades': len(result['trades']),
                    'performance_summary': {
                        'total_return': result['performance']['capital']['total_growth_percentage'],
                        'sharpe_ratio': result['performance']['risk_metrics']['sharpe_ratio'],
                        'win_rate': result['performance']['trade_statistics']['win_rate'],
                        'max_drawdown': result['performance']['risk_metrics']['max_drawdown_percentage'],
                        'vs_btc': result['performance']['opportunity_cost_analysis']['vs_btc']['opportunity_cost'],
                        'vs_eth': result['performance']['opportunity_cost_analysis']['vs_eth']['opportunity_cost'],
                        'vs_sol': result['performance']['opportunity_cost_analysis']['vs_sol']['opportunity_cost']
                    }
                }
                generation_data['strategies'].append(strategy_data)
        
        # Save to file
        filename = f"enhanced_gen_{self.generation}_full_stats.json"
        path = os.path.join(self.knowledge_base.base_path, 'generations', filename)
        with open(path, 'w') as f:
            json.dump(generation_data, f, indent=2)
    
    async def _evolve_with_performance_focus(self, results: List[Dict]):
        """Evolve strategies based on comprehensive performance metrics"""
        logger.info(f"\n🧬 Evolving population based on performance metrics...")
        
        # Filter valid results
        valid_results = [r for r in results if r['performance']]
        
        if not valid_results:
            logger.warning("No valid results for evolution")
            return
        
        # Multi-objective selection (Sharpe, Return, Opportunity Cost)
        def fitness_score(result):
            perf = result['performance']
            sharpe = float(perf['risk_metrics']['sharpe_ratio'])
            total_return = float(perf['capital']['total_growth_percentage'].strip('%')) / 100
            
            # Opportunity cost score (average vs BTC, ETH, SOL)
            opp_costs = [
                float(perf['opportunity_cost_analysis']['vs_btc']['opportunity_cost'].strip('%')) / 100,
                float(perf['opportunity_cost_analysis']['vs_eth']['opportunity_cost'].strip('%')) / 100,
                float(perf['opportunity_cost_analysis']['vs_sol']['opportunity_cost'].strip('%')) / 100
            ]
            avg_opp_cost = np.mean(opp_costs)
            
            # Combined fitness (weights can be adjusted)
            fitness = (sharpe * 0.4) + (total_return * 0.3) + (avg_opp_cost * 0.3)
            return fitness
        
        # Sort by fitness
        sorted_results = sorted(valid_results, key=fitness_score, reverse=True)
        
        # Select top performers for breeding
        elite_count = max(2, len(sorted_results) // 3)
        elite_strategies = [r['strategy'] for r in sorted_results[:elite_count]]
        
        # Create new generation
        new_strategies = []
        
        # Keep elite strategies
        for strategy in elite_strategies:
            new_strategies.append(strategy)
            logger.info(f"   ✓ Elite strategy preserved: {strategy.genome.name}")
        
        # Create offspring
        while len(new_strategies) < self.num_strategies:
            # Tournament selection
            parent1 = random.choice(elite_strategies)
            parent2 = random.choice(elite_strategies)
            
            # Create child genome
            child_genome = StrategyGenome(
                name=f"Enhanced_MTF_Strategy_G{self.generation+1}_{len(new_strategies)}",
                generation=self.generation + 1,
                parent_ids=[parent1.genome.id, parent2.genome.id]
            )
            
            # Crossover
            for tf in self.all_timeframes:
                if random.random() < 0.5:
                    child_genome.timeframe_weights[tf.value] = parent1.genome.timeframe_weights.get(tf.value, 1.0)
                else:
                    child_genome.timeframe_weights[tf.value] = parent2.genome.timeframe_weights.get(tf.value, 1.0)
            
            child_genome.confluence_threshold = random.choice([
                parent1.genome.confluence_threshold,
                parent2.genome.confluence_threshold
            ])
            
            child_genome.min_timeframe_alignment = random.choice([
                parent1.genome.min_timeframe_alignment,
                parent2.genome.min_timeframe_alignment
            ])
            
            # Mutation
            if random.random() < 0.3:
                child_genome.confluence_threshold *= random.uniform(0.9, 1.1)
            if random.random() < 0.3:
                child_genome.min_timeframe_alignment = max(1, child_genome.min_timeframe_alignment + random.randint(-1, 1))
            
            # Save and create strategy
            self.knowledge_base.save_strategy(child_genome)
            child_strategy = EnhancedMultiTimeframeStrategy(child_genome, self.knowledge_base)
            new_strategies.append(child_strategy)
        
        self.strategies = new_strategies
        logger.info(f"   ✓ Evolution complete: {len(self.strategies)} strategies in generation {self.generation + 1}")

async def main():
    """Run enhanced multi-timeframe learning with full statistics"""
    logger.info("\n" + "="*100)
    logger.info("🚀 ENHANCED MULTI-TIMEFRAME LEARNING WITH COMPREHENSIVE STATISTICS")
    logger.info("📊 Full Performance Tracking & Opportunity Cost Analysis")
    logger.info("="*100)
    
    # Initialize enhanced swarm
    swarm = EnhancedLearningSwarm(num_strategies=5)
    swarm.initialize_strategies()
    
    # Define assets
    major_assets = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    solana_tokens = SOLANA_TOP_30[:10]  # First 10 Solana tokens
    all_assets = major_assets + solana_tokens
    
    # Run learning cycles
    for cycle in range(3):
        logger.info(f"\n\n{'#'*100}")
        logger.info(f"LEARNING CYCLE {cycle + 1}")
        logger.info(f"{'#'*100}")
        
        await swarm.run_enhanced_learning_cycle(all_assets, days=30)
        await asyncio.sleep(1)
    
    logger.info("\n\n" + "="*100)
    logger.info("🎯 ENHANCED LEARNING COMPLETE")
    logger.info(f"📁 Full statistics saved to: {swarm.knowledge_base.base_path}")
    logger.info("📊 Performance reports include:")
    logger.info("   • Complete trade-by-trade records")
    logger.info("   • Dollar P&L for every trade")
    logger.info("   • Win/loss ratios and streaks")
    logger.info("   • Risk-adjusted returns (Sharpe, Sortino, Calmar)")
    logger.info("   • Opportunity cost vs BTC, ETH, SOL buy-and-hold")
    logger.info("   • Performance forecasts and confidence intervals")
    logger.info("="*100)

if __name__ == "__main__":
    asyncio.run(main())