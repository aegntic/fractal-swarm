#!/usr/bin/env python3
"""
Run Enhanced Historical Data Collection and Simulation Analysis
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_historical_collector import EnhancedDataCollector
from enhanced_simulation_runner import EnhancedSimulationRunner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to run complete analysis"""
    try:
        logger.info("="*60)
        logger.info("CRYPTO SWARM TRADER - ENHANCED ANALYSIS")
        logger.info("="*60)
        
        # Step 1: Collect Historical Data
        logger.info("\n[1/2] Starting Historical Data Collection...")
        logger.info("Collecting data for BTC, ETH, and SOL")
        
        collector = EnhancedDataCollector()
        
        # Initialize exchanges
        await collector.initialize_exchanges()
        
        # Collect historical data (365 days)
        await collector.fetch_all_historical_data(days_back=365)
        
        # Get correlations and statistics
        try:
            correlation_matrix = await collector.get_correlation_matrix()
            logger.info(f"\nAsset Correlations:\n{correlation_matrix}")
            
            stats = await collector.get_market_statistics()
            logger.info("\nMarket Statistics Summary:")
            for pair, pair_stats in stats.items():
                logger.info(f"\n{pair}:")
                for tf, metrics in pair_stats.items():
                    logger.info(f"  {tf}: Volatility={metrics['volatility']:.4f}, "
                               f"Sharpe={metrics['sharpe_ratio']:.2f}")
        except Exception as e:
            logger.warning(f"Could not calculate statistics: {e}")
        
        await collector.close_all()
        
        logger.info("\n✓ Historical data collection completed!")
        
        # Step 2: Run Simulations
        logger.info("\n[2/2] Starting Enhanced Simulations...")
        logger.info("Running 50 parallel backtests with different strategies")
        
        runner = EnhancedSimulationRunner()
        
        # Run simulations
        results = await runner.run_parallel_simulations(num_simulations=50)
        
        logger.info(f"\n✓ Completed {len(results)} simulations!")
        
        # Display top results
        if results:
            logger.info("\n" + "="*60)
            logger.info("TOP 5 PERFORMING STRATEGIES")
            logger.info("="*60)
            
            for i, result in enumerate(results[:5]):
                logger.info(f"\nStrategy #{i+1}:")
                logger.info(f"  Initial Capital: ${result.config.initial_capital:,.2f}")
                logger.info(f"  Final Capital: ${result.final_capital:,.2f}")
                logger.info(f"  Total Return: {result.total_return:.2%}")
                logger.info(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
                logger.info(f"  Max Drawdown: {result.max_drawdown:.2%}")
                logger.info(f"  Win Rate: {result.win_rate:.2%}")
                logger.info(f"  Total Trades: {result.total_trades}")
                logger.info(f"  Profit Factor: {result.profit_factor:.2f}")
        
        logger.info("\n" + "="*60)
        logger.info("ANALYSIS COMPLETE")
        logger.info("="*60)
        logger.info(f"Data saved to: data/historical/")
        logger.info(f"Results saved to: {runner.results_dir}/")
        logger.info("\nNext steps:")
        logger.info("1. Review the simulation results in simulation_results/")
        logger.info("2. Deploy the best performing strategies")
        logger.info("3. Monitor live performance and adjust parameters")
        
    except Exception as e:
        logger.error(f"Error in main analysis: {e}")
        raise


if __name__ == "__main__":
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        logger.warning("Warning: Not running in a virtual environment")
        logger.info("Consider activating the virtual environment: source venv/bin/activate")
    
    # Run the analysis
    asyncio.run(main())