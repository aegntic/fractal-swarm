"""
Enhanced Performance Tracker with Comprehensive Statistics
Tracks all trading metrics including opportunity cost vs buy-and-hold strategies
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import numpy as np
from enum import Enum

@dataclass
class TradeRecord:
    """Detailed record of a single trade"""
    id: str
    strategy_id: str
    asset: str
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime]
    exit_price: Optional[float]
    position_size: float  # In base currency (USD)
    direction: str  # 'long' or 'short'
    
    # Calculated fields
    pnl_dollars: Optional[float] = None
    pnl_percentage: Optional[float] = None
    duration_hours: Optional[float] = None
    max_drawdown_dollars: Optional[float] = None
    max_profit_dollars: Optional[float] = None
    
    # Risk metrics
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    
    def calculate_pnl(self):
        """Calculate P&L for the trade"""
        if self.exit_price and self.exit_time:
            if self.direction == 'long':
                self.pnl_percentage = (self.exit_price - self.entry_price) / self.entry_price
            else:  # short
                self.pnl_percentage = (self.entry_price - self.exit_price) / self.entry_price
            
            self.pnl_dollars = self.position_size * self.pnl_percentage
            self.duration_hours = (self.exit_time - self.entry_time).total_seconds() / 3600

@dataclass
class StrategyPerformanceMetrics:
    """Comprehensive performance metrics for a strategy"""
    strategy_id: str
    strategy_name: str
    evaluation_start: datetime
    evaluation_end: datetime
    initial_capital: float
    
    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # Dollar amounts
    total_profit_dollars: float = 0.0
    total_loss_dollars: float = 0.0
    largest_win_dollars: float = 0.0
    largest_loss_dollars: float = 0.0
    average_win_dollars: float = 0.0
    average_loss_dollars: float = 0.0
    
    # Percentages
    win_rate: float = 0.0
    total_return_percentage: float = 0.0
    average_return_per_trade: float = 0.0
    best_trade_percentage: float = 0.0
    worst_trade_percentage: float = 0.0
    
    # Risk metrics
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown_percentage: float = 0.0
    max_drawdown_dollars: float = 0.0
    value_at_risk_95: float = 0.0  # 95% VaR
    expected_shortfall: float = 0.0  # CVaR
    
    # Time-based metrics
    average_trade_duration_hours: float = 0.0
    longest_winning_streak: int = 0
    longest_losing_streak: int = 0
    profit_factor: float = 0.0  # Total profits / Total losses
    
    # Growth metrics
    final_capital: float = 0.0
    total_growth_percentage: float = 0.0
    annualized_return: float = 0.0
    monthly_returns: List[float] = field(default_factory=list)
    
    # Forecast metrics
    expected_annual_return: float = 0.0
    forecast_confidence_interval: Tuple[float, float] = (0.0, 0.0)
    break_even_probability: float = 0.0
    
    # Asset-specific performance
    performance_by_asset: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Opportunity cost vs buy-and-hold
    btc_buy_hold_return: float = 0.0
    eth_buy_hold_return: float = 0.0
    sol_buy_hold_return: float = 0.0
    opportunity_cost_vs_btc: float = 0.0
    opportunity_cost_vs_eth: float = 0.0
    opportunity_cost_vs_sol: float = 0.0

class OpportunityCostCalculator:
    """Calculate opportunity cost vs buy-and-hold strategies"""
    
    @staticmethod
    def calculate_buy_hold_return(asset: str, start_price: float, end_price: float) -> float:
        """Calculate simple buy-and-hold return"""
        return (end_price - start_price) / start_price
    
    @staticmethod
    def calculate_opportunity_cost(strategy_return: float, buy_hold_return: float) -> float:
        """
        Calculate opportunity cost
        Positive = strategy outperformed buy-and-hold
        Negative = buy-and-hold outperformed strategy
        """
        return strategy_return - buy_hold_return
    
    @staticmethod
    def calculate_risk_adjusted_opportunity_cost(
        strategy_sharpe: float, 
        strategy_return: float,
        buy_hold_return: float,
        buy_hold_volatility: float
    ) -> float:
        """Calculate risk-adjusted opportunity cost"""
        # Estimate buy-and-hold Sharpe (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        buy_hold_sharpe = (buy_hold_return - risk_free_rate) / buy_hold_volatility
        
        # Risk-adjusted excess return
        return (strategy_sharpe - buy_hold_sharpe) * buy_hold_volatility

class PerformanceAnalyzer:
    """Comprehensive performance analysis"""
    
    def __init__(self):
        self.trades: List[TradeRecord] = []
        self.metrics: Optional[StrategyPerformanceMetrics] = None
        
    def analyze_trades(self, trades: List[TradeRecord], initial_capital: float) -> StrategyPerformanceMetrics:
        """Analyze all trades and generate comprehensive metrics"""
        if not trades:
            return None
        
        # Sort trades by entry time
        sorted_trades = sorted(trades, key=lambda x: x.entry_time)
        
        # Initialize metrics
        metrics = StrategyPerformanceMetrics(
            strategy_id=trades[0].strategy_id,
            strategy_name=f"Strategy_{trades[0].strategy_id[:8]}",
            evaluation_start=sorted_trades[0].entry_time,
            evaluation_end=sorted_trades[-1].exit_time or datetime.now(),
            initial_capital=initial_capital
        )
        
        # Calculate basic statistics
        capital = initial_capital
        equity_curve = [capital]
        returns = []
        winning_streak = 0
        losing_streak = 0
        max_winning_streak = 0
        max_losing_streak = 0
        
        for trade in sorted_trades:
            trade.calculate_pnl()
            
            if trade.pnl_dollars is not None:
                metrics.total_trades += 1
                capital += trade.pnl_dollars
                equity_curve.append(capital)
                returns.append(trade.pnl_percentage)
                
                if trade.pnl_dollars > 0:
                    metrics.winning_trades += 1
                    metrics.total_profit_dollars += trade.pnl_dollars
                    winning_streak += 1
                    losing_streak = 0
                    max_winning_streak = max(max_winning_streak, winning_streak)
                    
                    if trade.pnl_dollars > metrics.largest_win_dollars:
                        metrics.largest_win_dollars = trade.pnl_dollars
                    if trade.pnl_percentage > metrics.best_trade_percentage:
                        metrics.best_trade_percentage = trade.pnl_percentage
                else:
                    metrics.losing_trades += 1
                    metrics.total_loss_dollars += abs(trade.pnl_dollars)
                    losing_streak += 1
                    winning_streak = 0
                    max_losing_streak = max(max_losing_streak, losing_streak)
                    
                    if abs(trade.pnl_dollars) > metrics.largest_loss_dollars:
                        metrics.largest_loss_dollars = abs(trade.pnl_dollars)
                    if trade.pnl_percentage < metrics.worst_trade_percentage:
                        metrics.worst_trade_percentage = trade.pnl_percentage
                
                # Update asset-specific performance
                if trade.asset not in metrics.performance_by_asset:
                    metrics.performance_by_asset[trade.asset] = {
                        'trades': 0, 'wins': 0, 'total_pnl': 0.0, 'win_rate': 0.0
                    }
                
                metrics.performance_by_asset[trade.asset]['trades'] += 1
                if trade.pnl_dollars > 0:
                    metrics.performance_by_asset[trade.asset]['wins'] += 1
                metrics.performance_by_asset[trade.asset]['total_pnl'] += trade.pnl_dollars
        
        # Calculate final metrics
        metrics.final_capital = capital
        metrics.total_growth_percentage = (capital - initial_capital) / initial_capital
        metrics.longest_winning_streak = max_winning_streak
        metrics.longest_losing_streak = max_losing_streak
        
        # Win rate and averages
        if metrics.total_trades > 0:
            metrics.win_rate = metrics.winning_trades / metrics.total_trades
            metrics.average_return_per_trade = sum(returns) / len(returns)
        
        if metrics.winning_trades > 0:
            metrics.average_win_dollars = metrics.total_profit_dollars / metrics.winning_trades
        
        if metrics.losing_trades > 0:
            metrics.average_loss_dollars = metrics.total_loss_dollars / metrics.losing_trades
        
        if metrics.total_loss_dollars > 0:
            metrics.profit_factor = metrics.total_profit_dollars / metrics.total_loss_dollars
        
        # Calculate risk metrics
        if returns:
            returns_array = np.array(returns)
            
            # Sharpe Ratio (annualized)
            if np.std(returns_array) > 0:
                metrics.sharpe_ratio = (np.mean(returns_array) * np.sqrt(252)) / (np.std(returns_array) * np.sqrt(252))
            
            # Sortino Ratio (downside deviation)
            downside_returns = returns_array[returns_array < 0]
            if len(downside_returns) > 0 and np.std(downside_returns) > 0:
                metrics.sortino_ratio = (np.mean(returns_array) * np.sqrt(252)) / (np.std(downside_returns) * np.sqrt(252))
            
            # Maximum Drawdown
            equity_array = np.array(equity_curve)
            peak = np.maximum.accumulate(equity_array)
            drawdown = (equity_array - peak) / peak
            metrics.max_drawdown_percentage = np.min(drawdown)
            metrics.max_drawdown_dollars = np.min(equity_array - peak)
            
            # Calmar Ratio
            if metrics.max_drawdown_percentage < 0:
                years = (metrics.evaluation_end - metrics.evaluation_start).days / 365.25
                annual_return = (metrics.final_capital / initial_capital) ** (1/years) - 1
                metrics.calmar_ratio = annual_return / abs(metrics.max_drawdown_percentage)
            
            # Value at Risk (95%)
            metrics.value_at_risk_95 = np.percentile(returns_array, 5)
            
            # Expected Shortfall (CVaR)
            var_threshold = metrics.value_at_risk_95
            tail_losses = returns_array[returns_array <= var_threshold]
            if len(tail_losses) > 0:
                metrics.expected_shortfall = np.mean(tail_losses)
        
        # Calculate annualized return
        days = (metrics.evaluation_end - metrics.evaluation_start).days
        if days > 0:
            years = days / 365.25
            metrics.annualized_return = (metrics.final_capital / initial_capital) ** (1/years) - 1
        
        # Asset win rates
        for asset, data in metrics.performance_by_asset.items():
            if data['trades'] > 0:
                data['win_rate'] = data['wins'] / data['trades']
        
        # Forecast metrics (simple projection based on historical performance)
        if metrics.total_trades > 30:  # Need sufficient data
            # Expected annual return based on historical average
            metrics.expected_annual_return = metrics.average_return_per_trade * 252  # Assuming daily trades
            
            # Confidence interval using historical volatility
            if returns:
                std_annual = np.std(returns) * np.sqrt(252)
                metrics.forecast_confidence_interval = (
                    metrics.expected_annual_return - 2 * std_annual,
                    metrics.expected_annual_return + 2 * std_annual
                )
            
            # Break-even probability (probability of positive returns)
            positive_returns = sum(1 for r in returns if r > 0)
            metrics.break_even_probability = positive_returns / len(returns)
        
        return metrics

class EnhancedBacktester:
    """Backtester with full statistics and opportunity cost tracking"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.analyzer = PerformanceAnalyzer()
        self.buy_hold_prices = {}
        
    def set_buy_hold_prices(self, asset_prices: Dict[str, Dict[str, float]]):
        """Set buy-and-hold reference prices
        asset_prices: {'BTC/USDT': {'start': 40000, 'end': 45000}, ...}
        """
        self.buy_hold_prices = asset_prices
    
    def run_backtest_with_full_metrics(self, trades: List[TradeRecord]) -> Dict:
        """Run backtest and calculate all metrics including opportunity costs"""
        # Analyze trades
        metrics = self.analyzer.analyze_trades(trades, self.initial_capital)
        
        if not metrics:
            return None
        
        # Calculate buy-and-hold returns
        if 'BTC/USDT' in self.buy_hold_prices:
            btc_prices = self.buy_hold_prices['BTC/USDT']
            metrics.btc_buy_hold_return = OpportunityCostCalculator.calculate_buy_hold_return(
                'BTC/USDT', btc_prices['start'], btc_prices['end']
            )
            metrics.opportunity_cost_vs_btc = OpportunityCostCalculator.calculate_opportunity_cost(
                metrics.total_growth_percentage, metrics.btc_buy_hold_return
            )
        
        if 'ETH/USDT' in self.buy_hold_prices:
            eth_prices = self.buy_hold_prices['ETH/USDT']
            metrics.eth_buy_hold_return = OpportunityCostCalculator.calculate_buy_hold_return(
                'ETH/USDT', eth_prices['start'], eth_prices['end']
            )
            metrics.opportunity_cost_vs_eth = OpportunityCostCalculator.calculate_opportunity_cost(
                metrics.total_growth_percentage, metrics.eth_buy_hold_return
            )
        
        if 'SOL/USDT' in self.buy_hold_prices:
            sol_prices = self.buy_hold_prices['SOL/USDT']
            metrics.sol_buy_hold_return = OpportunityCostCalculator.calculate_buy_hold_return(
                'SOL/USDT', sol_prices['start'], sol_prices['end']
            )
            metrics.opportunity_cost_vs_sol = OpportunityCostCalculator.calculate_opportunity_cost(
                metrics.total_growth_percentage, metrics.sol_buy_hold_return
            )
        
        return self._format_comprehensive_report(metrics)
    
    def _format_comprehensive_report(self, metrics: StrategyPerformanceMetrics) -> Dict:
        """Format metrics into comprehensive report"""
        return {
            'strategy_info': {
                'id': metrics.strategy_id,
                'name': metrics.strategy_name,
                'evaluation_period': {
                    'start': metrics.evaluation_start.isoformat(),
                    'end': metrics.evaluation_end.isoformat(),
                    'days': (metrics.evaluation_end - metrics.evaluation_start).days
                }
            },
            'capital': {
                'initial': metrics.initial_capital,
                'final': metrics.final_capital,
                'total_growth_percentage': f"{metrics.total_growth_percentage:.2%}",
                'annualized_return': f"{metrics.annualized_return:.2%}"
            },
            'trade_statistics': {
                'total_trades': metrics.total_trades,
                'winning_trades': metrics.winning_trades,
                'losing_trades': metrics.losing_trades,
                'win_rate': f"{metrics.win_rate:.2%}",
                'average_return_per_trade': f"{metrics.average_return_per_trade:.2%}",
                'longest_winning_streak': metrics.longest_winning_streak,
                'longest_losing_streak': metrics.longest_losing_streak,
                'profit_factor': f"{metrics.profit_factor:.2f}"
            },
            'dollar_pnl': {
                'total_profit_dollars': f"${metrics.total_profit_dollars:,.2f}",
                'total_loss_dollars': f"${metrics.total_loss_dollars:,.2f}",
                'net_pnl': f"${metrics.total_profit_dollars - metrics.total_loss_dollars:,.2f}",
                'largest_win': f"${metrics.largest_win_dollars:,.2f}",
                'largest_loss': f"${metrics.largest_loss_dollars:,.2f}",
                'average_win': f"${metrics.average_win_dollars:,.2f}",
                'average_loss': f"${metrics.average_loss_dollars:,.2f}"
            },
            'risk_metrics': {
                'sharpe_ratio': f"{metrics.sharpe_ratio:.3f}",
                'sortino_ratio': f"{metrics.sortino_ratio:.3f}",
                'calmar_ratio': f"{metrics.calmar_ratio:.3f}",
                'max_drawdown_percentage': f"{metrics.max_drawdown_percentage:.2%}",
                'max_drawdown_dollars': f"${metrics.max_drawdown_dollars:,.2f}",
                'value_at_risk_95': f"{metrics.value_at_risk_95:.2%}",
                'expected_shortfall': f"{metrics.expected_shortfall:.2%}"
            },
            'forecasts': {
                'expected_annual_return': f"{metrics.expected_annual_return:.2%}",
                'confidence_interval_lower': f"{metrics.forecast_confidence_interval[0]:.2%}",
                'confidence_interval_upper': f"{metrics.forecast_confidence_interval[1]:.2%}",
                'break_even_probability': f"{metrics.break_even_probability:.2%}"
            },
            'opportunity_cost_analysis': {
                'btc_buy_hold_return': f"{metrics.btc_buy_hold_return:.2%}",
                'eth_buy_hold_return': f"{metrics.eth_buy_hold_return:.2%}",
                'sol_buy_hold_return': f"{metrics.sol_buy_hold_return:.2%}",
                'vs_btc': {
                    'opportunity_cost': f"{metrics.opportunity_cost_vs_btc:.2%}",
                    'outperformed': metrics.opportunity_cost_vs_btc > 0
                },
                'vs_eth': {
                    'opportunity_cost': f"{metrics.opportunity_cost_vs_eth:.2%}",
                    'outperformed': metrics.opportunity_cost_vs_eth > 0
                },
                'vs_sol': {
                    'opportunity_cost': f"{metrics.opportunity_cost_vs_sol:.2%}",
                    'outperformed': metrics.opportunity_cost_vs_sol > 0
                }
            },
            'asset_breakdown': metrics.performance_by_asset
        }