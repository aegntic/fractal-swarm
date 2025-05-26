"""
Demonstration of Enhanced Statistics Tracking
Shows comprehensive performance metrics with simulated results
"""

import json
import os
from datetime import datetime, timedelta
import random
import numpy as np
from enhanced_performance_tracker import (
    TradeRecord, StrategyPerformanceMetrics, 
    PerformanceAnalyzer, EnhancedBacktester
)

def generate_demo_trades(strategy_id: str, num_trades: int = 50) -> list:
    """Generate realistic demo trades with various outcomes"""
    trades = []
    start_date = datetime.now() - timedelta(days=30)
    
    assets = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'RAY/USDT', 'SRM/USDT']
    
    for i in range(num_trades):
        # Random asset
        asset = random.choice(assets)
        
        # Entry time (spread over 30 days)
        entry_time = start_date + timedelta(hours=random.randint(0, 720))
        
        # Entry price based on asset
        base_prices = {
            'BTC/USDT': 40000,
            'ETH/USDT': 2500,
            'SOL/USDT': 100,
            'RAY/USDT': 5,
            'SRM/USDT': 3
        }
        entry_price = base_prices[asset] * random.uniform(0.95, 1.05)
        
        # Position size ($500-2000)
        position_size = random.uniform(500, 2000)
        
        # Direction
        direction = random.choice(['long', 'short'])
        
        # Exit (1-72 hours later)
        exit_time = entry_time + timedelta(hours=random.randint(1, 72))
        
        # Generate realistic P&L
        # 60% win rate with winners being larger than losers
        is_winner = random.random() < 0.6
        
        if is_winner:
            # Winners: 0.5% to 3% gain
            pnl_pct = random.uniform(0.005, 0.03)
        else:
            # Losers: 0.2% to 1.5% loss
            pnl_pct = -random.uniform(0.002, 0.015)
        
        # Exit price
        if direction == 'long':
            exit_price = entry_price * (1 + pnl_pct)
        else:
            exit_price = entry_price * (1 - pnl_pct)
        
        # Create trade
        trade = TradeRecord(
            id=f"trade_{i}",
            strategy_id=strategy_id,
            asset=asset,
            entry_time=entry_time,
            entry_price=entry_price,
            exit_time=exit_time,
            exit_price=exit_price,
            position_size=position_size,
            direction=direction,
            stop_loss=entry_price * (0.98 if direction == 'long' else 1.02),
            take_profit=entry_price * (1.03 if direction == 'long' else 0.97),
            risk_reward_ratio=2.0
        )
        
        trades.append(trade)
    
    return trades

def demonstrate_comprehensive_statistics():
    """Run demonstration of all statistics tracking"""
    print("="*100)
    print("🚀 ENHANCED PERFORMANCE TRACKING DEMONSTRATION")
    print("📊 Showing All Statistics Including Opportunity Cost Analysis")
    print("="*100)
    
    # Generate trades for multiple strategies
    strategies = [
        ("Momentum_Confluence_Strategy", 75),  # 75 trades
        ("Mean_Reversion_MTF", 50),  # 50 trades
        ("Volatility_Breakout", 60),  # 60 trades
    ]
    
    # Set buy-and-hold prices (simulating market movement)
    buy_hold_prices = {
        'BTC/USDT': {'start': 40000, 'end': 44000},  # +10%
        'ETH/USDT': {'start': 2500, 'end': 2750},    # +10%
        'SOL/USDT': {'start': 100, 'end': 120}       # +20%
    }
    
    all_reports = []
    
    for strategy_name, num_trades in strategies:
        print(f"\n{'='*80}")
        print(f"📈 Analyzing {strategy_name}")
        print(f"{'='*80}")
        
        # Generate trades
        strategy_id = f"strat_{strategy_name[:5]}"
        trades = generate_demo_trades(strategy_id, num_trades)
        
        # Run analysis
        backtester = EnhancedBacktester(initial_capital=10000)
        backtester.set_buy_hold_prices(buy_hold_prices)
        
        report = backtester.run_backtest_with_full_metrics(trades)
        all_reports.append((strategy_name, report))
        
        # Display comprehensive results
        display_full_report(strategy_name, report)
    
    # Compare strategies
    print(f"\n{'='*100}")
    print("🏆 STRATEGY COMPARISON")
    print(f"{'='*100}")
    compare_strategies(all_reports)
    
    # Save sample report
    save_sample_report(all_reports[0][1])

def display_full_report(strategy_name: str, report: dict):
    """Display all statistics from the report"""
    print(f"\n📊 {strategy_name} - Complete Performance Report")
    print("-"*80)
    
    # Capital Growth
    print("\n💰 CAPITAL GROWTH:")
    print(f"   Initial Capital: {report['capital']['initial']}")
    print(f"   Final Capital: {report['capital']['final']}")
    print(f"   Total Growth: {report['capital']['total_growth_percentage']}")
    print(f"   Annualized Return: {report['capital']['annualized_return']}")
    
    # Trade Statistics
    print("\n📈 TRADE STATISTICS:")
    stats = report['trade_statistics']
    print(f"   Total Trades: {stats['total_trades']}")
    print(f"   Winning Trades: {stats['winning_trades']}")
    print(f"   Losing Trades: {stats['losing_trades']}")
    print(f"   Win Rate: {stats['win_rate']}")
    print(f"   Average Return per Trade: {stats['average_return_per_trade']}")
    print(f"   Longest Winning Streak: {stats['longest_winning_streak']}")
    print(f"   Longest Losing Streak: {stats['longest_losing_streak']}")
    print(f"   Profit Factor: {stats['profit_factor']}")
    
    # Dollar P&L
    print("\n💵 DOLLAR P&L:")
    pnl = report['dollar_pnl']
    print(f"   Total Profits: {pnl['total_profit_dollars']}")
    print(f"   Total Losses: {pnl['total_loss_dollars']}")
    print(f"   Net P&L: {pnl['net_pnl']}")
    print(f"   Largest Win: {pnl['largest_win']}")
    print(f"   Largest Loss: {pnl['largest_loss']}")
    print(f"   Average Win: {pnl['average_win']}")
    print(f"   Average Loss: {pnl['average_loss']}")
    
    # Risk Metrics
    print("\n⚠️ RISK METRICS:")
    risk = report['risk_metrics']
    print(f"   Sharpe Ratio: {risk['sharpe_ratio']}")
    print(f"   Sortino Ratio: {risk['sortino_ratio']}")
    print(f"   Calmar Ratio: {risk['calmar_ratio']}")
    print(f"   Max Drawdown %: {risk['max_drawdown_percentage']}")
    print(f"   Max Drawdown $: {risk['max_drawdown_dollars']}")
    print(f"   Value at Risk (95%): {risk['value_at_risk_95']}")
    print(f"   Expected Shortfall: {risk['expected_shortfall']}")
    
    # Forecasts
    print("\n🔮 FORECASTS:")
    forecast = report['forecasts']
    print(f"   Expected Annual Return: {forecast['expected_annual_return']}")
    print(f"   95% Confidence Interval: [{forecast['confidence_interval_lower']}, {forecast['confidence_interval_upper']}]")
    print(f"   Break-even Probability: {forecast['break_even_probability']}")
    
    # Opportunity Cost Analysis
    print("\n🆚 OPPORTUNITY COST vs BUY & HOLD:")
    opp = report['opportunity_cost_analysis']
    print(f"   BTC Buy & Hold Return: {opp['btc_buy_hold_return']}")
    print(f"   ETH Buy & Hold Return: {opp['eth_buy_hold_return']}")
    print(f"   SOL Buy & Hold Return: {opp['sol_buy_hold_return']}")
    print(f"   ")
    print(f"   vs BTC: {opp['vs_btc']['opportunity_cost']} {'✅ OUTPERFORMED' if opp['vs_btc']['outperformed'] else '❌ UNDERPERFORMED'}")
    print(f"   vs ETH: {opp['vs_eth']['opportunity_cost']} {'✅ OUTPERFORMED' if opp['vs_eth']['outperformed'] else '❌ UNDERPERFORMED'}")
    print(f"   vs SOL: {opp['vs_sol']['opportunity_cost']} {'✅ OUTPERFORMED' if opp['vs_sol']['outperformed'] else '❌ UNDERPERFORMED'}")
    
    # Asset Breakdown
    print("\n🪙 PERFORMANCE BY ASSET:")
    for asset, data in report['asset_breakdown'].items():
        print(f"   {asset}: {data['trades']} trades, {data['win_rate']:.1%} win rate, ${data['total_pnl']:.2f} P&L")

def compare_strategies(all_reports: list):
    """Compare multiple strategies side by side"""
    print("\n📊 Side-by-Side Comparison:")
    print("-"*120)
    print(f"{'Strategy':<30} {'Return':<12} {'Sharpe':<10} {'Win Rate':<10} {'Max DD':<12} {'vs BTC':<15} {'vs ETH':<15} {'vs SOL':<15}")
    print("-"*120)
    
    for name, report in all_reports:
        return_pct = report['capital']['total_growth_percentage']
        sharpe = report['risk_metrics']['sharpe_ratio']
        win_rate = report['trade_statistics']['win_rate']
        max_dd = report['risk_metrics']['max_drawdown_percentage']
        vs_btc = report['opportunity_cost_analysis']['vs_btc']['opportunity_cost']
        vs_eth = report['opportunity_cost_analysis']['vs_eth']['opportunity_cost']
        vs_sol = report['opportunity_cost_analysis']['vs_sol']['opportunity_cost']
        
        btc_symbol = '✅' if report['opportunity_cost_analysis']['vs_btc']['outperformed'] else '❌'
        eth_symbol = '✅' if report['opportunity_cost_analysis']['vs_eth']['outperformed'] else '❌'
        sol_symbol = '✅' if report['opportunity_cost_analysis']['vs_sol']['outperformed'] else '❌'
        
        print(f"{name:<30} {return_pct:<12} {sharpe:<10} {win_rate:<10} {max_dd:<12} {vs_btc:<12}{btc_symbol} {vs_eth:<12}{eth_symbol} {vs_sol:<12}{sol_symbol}")

def save_sample_report(report: dict):
    """Save a sample report to show the data structure"""
    os.makedirs("knowledge_base/sample_reports", exist_ok=True)
    
    with open("knowledge_base/sample_reports/comprehensive_performance_report.json", 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📁 Sample report saved to: knowledge_base/sample_reports/comprehensive_performance_report.json")

if __name__ == "__main__":
    demonstrate_comprehensive_statistics()