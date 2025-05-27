"""
Enhanced Simulation Runner for Crypto Swarm Trading
Runs comprehensive backtests with multiple strategies and parameters
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import pickle
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
from tqdm import tqdm
import uuid

from backtesting.future_blind_simulator import FutureBlindSimulator
from multi_timeframe_learning_swarm import MultiTimeframeLearningSwarm
from enhanced_performance_tracker import PerformanceAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SimulationConfig:
    """Configuration for a simulation run"""
    strategy_id: str
    initial_capital: float
    pairs: List[str]
    timeframes: List[str]
    start_date: datetime
    end_date: datetime
    max_position_size: float
    stop_loss: float
    take_profit: float
    fee_rate: float = 0.001
    slippage: float = 0.0005
    
    
@dataclass
class SimulationResult:
    """Results from a simulation run"""
    config: SimulationConfig
    final_capital: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    avg_trade_duration: float
    profit_factor: float
    trades_log: List[Dict]
    equity_curve: pd.DataFrame
    

class EnhancedSimulationRunner:
    """Runs parallel simulations with different strategies and parameters"""
    
    def __init__(self, data_dir: str = "data/historical"):
        self.data_dir = data_dir
        self.results_dir = "simulation_results"
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Load available data
        self.available_data = self.load_available_data()
        
    def load_available_data(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """Load all available historical data"""
        data = {}
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.pkl'):
                parts = filename.replace('.pkl', '').split('_')
                if len(parts) >= 3:
                    pair = f"{parts[0]}/{parts[1]}"
                    timeframe = parts[2]
                    
                    if pair not in data:
                        data[pair] = {}
                    
                    filepath = os.path.join(self.data_dir, filename)
                    with open(filepath, 'rb') as f:
                        data[pair][timeframe] = pickle.load(f)
        
        return data
    
    def generate_strategy_variations(self, base_params: Dict) -> List[Dict]:
        """Generate variations of strategy parameters for optimization"""
        variations = []
        
        # Parameter ranges for grid search
        param_ranges = {
            'rsi_oversold': [20, 25, 30],
            'rsi_overbought': [70, 75, 80],
            'macd_threshold': [0.0001, 0.0002, 0.0003],
            'bb_threshold': [0.8, 0.9, 1.0],
            'volume_threshold': [1.2, 1.5, 2.0],
            'atr_multiplier': [1.5, 2.0, 2.5],
            'ema_fast': [12, 20, 50],
            'ema_slow': [26, 50, 100],
            'momentum_period': [10, 14, 20],
            'trend_strength': [0.001, 0.002, 0.003]
        }
        
        # Generate all combinations (limited to avoid explosion)
        from itertools import product
        
        # Select subset of parameters to vary
        varying_params = ['rsi_oversold', 'rsi_overbought', 'volume_threshold', 'atr_multiplier']
        
        param_combinations = list(product(*[param_ranges[p] for p in varying_params]))
        
        for combo in param_combinations[:50]:  # Limit to 50 variations
            strategy_params = base_params.copy()
            for i, param in enumerate(varying_params):
                strategy_params[param] = combo[i]
            variations.append(strategy_params)
        
        return variations
    
    async def run_single_simulation(self, config: SimulationConfig, 
                                  strategy_params: Dict) -> SimulationResult:
        """Run a single simulation with given configuration"""
        try:
            # Initialize components
            swarm = MultiTimeframeLearningSwarm(
                initial_capital=config.initial_capital,
                max_agents=5
            )
            
            tracker = PerformanceAnalyzer()
            
            # Load data for simulation period
            price_data = {}
            for pair in config.pairs:
                if pair in self.available_data:
                    pair_data = {}
                    for tf in config.timeframes:
                        if tf in self.available_data[pair]:
                            df = self.available_data[pair][tf]
                            # Filter to simulation period
                            mask = (df.index >= config.start_date) & (df.index <= config.end_date)
                            pair_data[tf] = df.loc[mask]
                    price_data[pair] = pair_data
            
            # Run simulation
            equity_curve = []
            trades_log = []
            current_capital = config.initial_capital
            
            # Iterate through time
            current_time = config.start_date
            time_step = timedelta(minutes=5)  # 5-minute steps
            
            while current_time < config.end_date:
                # Get current market state
                market_state = self.get_market_state(price_data, current_time)
                
                if market_state:
                    # Generate trading signals
                    signals = await self.generate_signals(
                        market_state, strategy_params, current_capital
                    )
                    
                    # Execute trades
                    for signal in signals:
                        if signal['action'] == 'BUY':
                            # Calculate position size
                            position_size = min(
                                signal['size'] * current_capital,
                                config.max_position_size * current_capital
                            )
                            
                            # Apply fees and slippage
                            entry_price = signal['price'] * (1 + config.slippage)
                            fee = position_size * config.fee_rate
                            
                            trade = {
                                'timestamp': current_time,
                                'pair': signal['pair'],
                                'action': 'BUY',
                                'price': entry_price,
                                'size': position_size / entry_price,
                                'fee': fee,
                                'capital_before': current_capital
                            }
                            
                            current_capital -= (position_size + fee)
                            trades_log.append(trade)
                            
                        elif signal['action'] == 'SELL' and self.has_position(trades_log, signal['pair']):
                            # Find corresponding buy trade
                            buy_trade = self.find_buy_trade(trades_log, signal['pair'])
                            if buy_trade:
                                exit_price = signal['price'] * (1 - config.slippage)
                                position_value = buy_trade['size'] * exit_price
                                fee = position_value * config.fee_rate
                                
                                profit = position_value - (buy_trade['size'] * buy_trade['price']) - fee - buy_trade['fee']
                                
                                trade = {
                                    'timestamp': current_time,
                                    'pair': signal['pair'],
                                    'action': 'SELL',
                                    'price': exit_price,
                                    'size': buy_trade['size'],
                                    'fee': fee,
                                    'profit': profit,
                                    'capital_before': current_capital
                                }
                                
                                current_capital += (position_value - fee)
                                trades_log.append(trade)
                
                # Record equity
                equity_curve.append({
                    'timestamp': current_time,
                    'capital': current_capital,
                    'positions': self.count_open_positions(trades_log)
                })
                
                current_time += time_step
            
            # Calculate final metrics
            equity_df = pd.DataFrame(equity_curve)
            equity_df.set_index('timestamp', inplace=True)
            
            # Calculate returns
            returns = equity_df['capital'].pct_change().dropna()
            
            # Performance metrics
            total_return = (current_capital - config.initial_capital) / config.initial_capital
            sharpe_ratio = self.calculate_sharpe_ratio(returns)
            max_drawdown = self.calculate_max_drawdown(equity_df['capital'])
            win_rate = self.calculate_win_rate(trades_log)
            profit_factor = self.calculate_profit_factor(trades_log)
            
            # Average trade duration
            avg_duration = self.calculate_avg_trade_duration(trades_log)
            
            return SimulationResult(
                config=config,
                final_capital=current_capital,
                total_return=total_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                total_trades=len([t for t in trades_log if t['action'] == 'BUY']),
                avg_trade_duration=avg_duration,
                profit_factor=profit_factor,
                trades_log=trades_log,
                equity_curve=equity_df
            )
            
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            # Return failed result
            return SimulationResult(
                config=config,
                final_capital=config.initial_capital,
                total_return=0,
                sharpe_ratio=0,
                max_drawdown=0,
                win_rate=0,
                total_trades=0,
                avg_trade_duration=0,
                profit_factor=0,
                trades_log=[],
                equity_curve=pd.DataFrame()
            )
    
    def get_market_state(self, price_data: Dict, current_time: datetime) -> Optional[Dict]:
        """Get current market state at given time"""
        state = {}
        
        for pair, timeframes in price_data.items():
            pair_state = {}
            
            for tf, df in timeframes.items():
                # Find the last available data point before current time
                available_data = df[df.index <= current_time]
                
                if not available_data.empty:
                    latest = available_data.iloc[-1]
                    
                    pair_state[tf] = {
                        'open': latest['open'],
                        'high': latest['high'],
                        'low': latest['low'],
                        'close': latest['close'],
                        'volume': latest['volume'],
                        'rsi': latest.get('rsi', 50),
                        'macd': latest.get('macd', 0),
                        'bb_percent': latest.get('bb_percent', 0.5),
                        'volume_ratio': latest.get('volume_ratio', 1.0),
                        'atr': latest.get('atr', 0),
                        'trend': self.calculate_trend(available_data.tail(20))
                    }
            
            if pair_state:
                state[pair] = pair_state
        
        return state if state else None
    
    def calculate_trend(self, df: pd.DataFrame) -> float:
        """Calculate trend strength"""
        if len(df) < 2:
            return 0
        
        # Simple linear regression slope
        x = np.arange(len(df))
        y = df['close'].values
        
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]
            return slope / df['close'].mean()  # Normalize by mean price
        
        return 0
    
    async def generate_signals(self, market_state: Dict, strategy_params: Dict, 
                             current_capital: float) -> List[Dict]:
        """Generate trading signals based on market state and strategy"""
        signals = []
        
        for pair, timeframes in market_state.items():
            # Multi-timeframe analysis
            if '1h' in timeframes and '15m' in timeframes:
                hourly = timeframes['1h']
                fifteen_min = timeframes['15m']
                
                # Buy conditions
                buy_score = 0
                
                # RSI oversold
                if fifteen_min['rsi'] < strategy_params.get('rsi_oversold', 30):
                    buy_score += 1
                
                # MACD bullish
                if fifteen_min['macd'] > strategy_params.get('macd_threshold', 0.0002):
                    buy_score += 1
                
                # Bollinger Band squeeze
                if fifteen_min['bb_percent'] < strategy_params.get('bb_threshold', 0.2):
                    buy_score += 1
                
                # Volume spike
                if fifteen_min['volume_ratio'] > strategy_params.get('volume_threshold', 1.5):
                    buy_score += 1
                
                # Hourly trend is up
                if hourly['trend'] > strategy_params.get('trend_strength', 0.001):
                    buy_score += 1
                
                # Generate buy signal
                if buy_score >= 3:
                    signals.append({
                        'pair': pair,
                        'action': 'BUY',
                        'price': fifteen_min['close'],
                        'size': 0.02,  # 2% of capital
                        'score': buy_score,
                        'reason': 'Multi-timeframe confluence'
                    })
                
                # Sell conditions
                sell_score = 0
                
                # RSI overbought
                if fifteen_min['rsi'] > strategy_params.get('rsi_overbought', 70):
                    sell_score += 1
                
                # MACD bearish
                if fifteen_min['macd'] < -strategy_params.get('macd_threshold', 0.0002):
                    sell_score += 1
                
                # Bollinger Band expansion
                if fifteen_min['bb_percent'] > (1 - strategy_params.get('bb_threshold', 0.2)):
                    sell_score += 1
                
                # Generate sell signal
                if sell_score >= 2:
                    signals.append({
                        'pair': pair,
                        'action': 'SELL',
                        'price': fifteen_min['close'],
                        'size': 0,  # Close full position
                        'score': sell_score,
                        'reason': 'Exit conditions met'
                    })
        
        return signals
    
    def has_position(self, trades_log: List[Dict], pair: str) -> bool:
        """Check if we have an open position for a pair"""
        buys = sum(1 for t in trades_log if t['pair'] == pair and t['action'] == 'BUY')
        sells = sum(1 for t in trades_log if t['pair'] == pair and t['action'] == 'SELL')
        return buys > sells
    
    def find_buy_trade(self, trades_log: List[Dict], pair: str) -> Optional[Dict]:
        """Find the last open buy trade for a pair"""
        # Find all trades for this pair
        pair_trades = [t for t in trades_log if t['pair'] == pair]
        
        # Track open positions
        for trade in reversed(pair_trades):
            if trade['action'] == 'BUY':
                # Check if this buy has been closed
                buy_index = trades_log.index(trade)
                subsequent_sells = [
                    t for t in trades_log[buy_index+1:] 
                    if t['pair'] == pair and t['action'] == 'SELL'
                ]
                
                if not subsequent_sells:
                    return trade
        
        return None
    
    def count_open_positions(self, trades_log: List[Dict]) -> int:
        """Count number of open positions"""
        positions = {}
        
        for trade in trades_log:
            pair = trade['pair']
            if pair not in positions:
                positions[pair] = 0
            
            if trade['action'] == 'BUY':
                positions[pair] += 1
            elif trade['action'] == 'SELL':
                positions[pair] = max(0, positions[pair] - 1)
        
        return sum(positions.values())
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 2:
            return 0
        
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        
        if excess_returns.std() == 0:
            return 0
        
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    
    def calculate_max_drawdown(self, equity: pd.Series) -> float:
        """Calculate maximum drawdown"""
        if len(equity) < 2:
            return 0
        
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax
        
        return abs(drawdown.min())
    
    def calculate_win_rate(self, trades_log: List[Dict]) -> float:
        """Calculate win rate from trades"""
        closed_trades = [t for t in trades_log if t['action'] == 'SELL' and 'profit' in t]
        
        if not closed_trades:
            return 0
        
        winning_trades = [t for t in closed_trades if t['profit'] > 0]
        
        return len(winning_trades) / len(closed_trades)
    
    def calculate_profit_factor(self, trades_log: List[Dict]) -> float:
        """Calculate profit factor"""
        closed_trades = [t for t in trades_log if t['action'] == 'SELL' and 'profit' in t]
        
        if not closed_trades:
            return 0
        
        gross_profit = sum(t['profit'] for t in closed_trades if t['profit'] > 0)
        gross_loss = abs(sum(t['profit'] for t in closed_trades if t['profit'] < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0
        
        return gross_profit / gross_loss
    
    def calculate_avg_trade_duration(self, trades_log: List[Dict]) -> float:
        """Calculate average trade duration in hours"""
        durations = []
        
        # Match buy and sell trades
        for sell_trade in [t for t in trades_log if t['action'] == 'SELL']:
            # Find corresponding buy
            buy_trade = None
            for trade in reversed(trades_log):
                if (trade['action'] == 'BUY' and 
                    trade['pair'] == sell_trade['pair'] and
                    trade['timestamp'] < sell_trade['timestamp']):
                    buy_trade = trade
                    break
            
            if buy_trade:
                duration = (sell_trade['timestamp'] - buy_trade['timestamp']).total_seconds() / 3600
                durations.append(duration)
        
        return np.mean(durations) if durations else 0
    
    async def run_parallel_simulations(self, num_simulations: int = 50):
        """Run multiple simulations in parallel"""
        logger.info(f"Starting {num_simulations} parallel simulations")
        
        # Base configuration
        base_config = SimulationConfig(
            strategy_id=str(uuid.uuid4()),
            initial_capital=1000,
            pairs=['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
            timeframes=['15m', '1h', '4h'],
            start_date=datetime.now() - timedelta(days=180),
            end_date=datetime.now() - timedelta(days=1),
            max_position_size=0.2,
            stop_loss=0.05,
            take_profit=0.1
        )
        
        # Base strategy parameters
        base_strategy_params = {
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_threshold': 0.0002,
            'bb_threshold': 0.9,
            'volume_threshold': 1.5,
            'atr_multiplier': 2.0,
            'ema_fast': 12,
            'ema_slow': 26,
            'momentum_period': 14,
            'trend_strength': 0.002
        }
        
        # Generate strategy variations
        strategy_variations = self.generate_strategy_variations(base_strategy_params)
        
        # Run simulations
        results = []
        
        # Use asyncio for concurrent execution
        tasks = []
        for i in range(min(num_simulations, len(strategy_variations))):
            config = SimulationConfig(
                strategy_id=str(uuid.uuid4()),
                initial_capital=base_config.initial_capital,
                pairs=base_config.pairs,
                timeframes=base_config.timeframes,
                start_date=base_config.start_date,
                end_date=base_config.end_date,
                max_position_size=base_config.max_position_size,
                stop_loss=base_config.stop_loss,
                take_profit=base_config.take_profit
            )
            
            task = self.run_single_simulation(config, strategy_variations[i])
            tasks.append(task)
        
        # Execute all simulations
        results = await asyncio.gather(*tasks)
        
        # Sort results by total return
        results.sort(key=lambda x: x.total_return, reverse=True)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.results_dir, f"simulation_results_{timestamp}.json")
        
        results_data = []
        for result in results:
            results_data.append({
                'strategy_id': result.config.strategy_id,
                'final_capital': result.final_capital,
                'total_return': result.total_return,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'win_rate': result.win_rate,
                'total_trades': result.total_trades,
                'avg_trade_duration': result.avg_trade_duration,
                'profit_factor': result.profit_factor
            })
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        # Save best strategy
        if results:
            best_result = results[0]
            best_strategy_file = os.path.join(self.results_dir, f"best_strategy_{timestamp}.pkl")
            
            with open(best_strategy_file, 'wb') as f:
                pickle.dump(best_result, f)
        
        # Generate summary report
        self.generate_summary_report(results, timestamp)
        
        return results
    
    def generate_summary_report(self, results: List[SimulationResult], timestamp: str):
        """Generate a summary report of simulation results"""
        report = {
            'timestamp': timestamp,
            'total_simulations': len(results),
            'summary_statistics': {
                'avg_return': np.mean([r.total_return for r in results]),
                'median_return': np.median([r.total_return for r in results]),
                'best_return': max([r.total_return for r in results]),
                'worst_return': min([r.total_return for r in results]),
                'avg_sharpe': np.mean([r.sharpe_ratio for r in results]),
                'avg_max_drawdown': np.mean([r.max_drawdown for r in results]),
                'avg_win_rate': np.mean([r.win_rate for r in results]),
                'avg_trades': np.mean([r.total_trades for r in results])
            },
            'top_10_strategies': []
        }
        
        # Add top 10 strategies
        for i, result in enumerate(results[:10]):
            report['top_10_strategies'].append({
                'rank': i + 1,
                'strategy_id': result.config.strategy_id,
                'total_return': result.total_return,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'win_rate': result.win_rate,
                'profit_factor': result.profit_factor
            })
        
        # Save report
        report_file = os.path.join(self.results_dir, f"summary_report_{timestamp}.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("SIMULATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Simulations: {report['total_simulations']}")
        logger.info(f"Average Return: {report['summary_statistics']['avg_return']:.2%}")
        logger.info(f"Best Return: {report['summary_statistics']['best_return']:.2%}")
        logger.info(f"Average Sharpe Ratio: {report['summary_statistics']['avg_sharpe']:.2f}")
        logger.info(f"Average Win Rate: {report['summary_statistics']['avg_win_rate']:.2%}")
        logger.info("\nTop 3 Strategies:")
        for strategy in report['top_10_strategies'][:3]:
            logger.info(f"  #{strategy['rank']}: Return={strategy['total_return']:.2%}, "
                       f"Sharpe={strategy['sharpe_ratio']:.2f}, "
                       f"MaxDD={strategy['max_drawdown']:.2%}")
        logger.info("="*60)


async def main():
    """Main function to run enhanced simulations"""
    runner = EnhancedSimulationRunner()
    
    # Run parallel simulations
    results = await runner.run_parallel_simulations(num_simulations=50)
    
    logger.info(f"Completed {len(results)} simulations")
    logger.info(f"Results saved to {runner.results_dir}")


if __name__ == "__main__":
    asyncio.run(main())