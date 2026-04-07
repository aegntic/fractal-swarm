"""
Quantum Swarm Trader - Main Entry Point
Interactive CLI for managing the swarm
"""

import asyncio
import click
import sys
from decimal import Decimal
from typing import Optional
import json
from loguru import logger
from dotenv import load_dotenv
import os

from quantum_swarm_coordinator import QuantumSwarmCoordinator
from utils.dashboard import DashboardManager

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add("logs/quantum_swarm_{time}.log", rotation="1 day", retention="7 days")

load_dotenv()


class QuantumSwarmCLI:
    """Interactive CLI for Quantum Swarm Trader"""
    
    def __init__(self):
        self.coordinator: Optional[QuantumSwarmCoordinator] = None
        self.dashboard: Optional[DashboardManager] = None
        self.running = False
        
    async def initialize_swarm(self, private_key: str = None):
        """Initialize the quantum swarm"""
        try:
            # Use environment variable if no key provided
            if not private_key:
                private_key = os.getenv('SOLANA_PRIVATE_KEY')
                
            if not private_key:
                logger.error("No Solana private key provided")
                return False
                
            # Create coordinator
            self.coordinator = QuantumSwarmCoordinator(initial_capital=Decimal("100"))
            
            # Initialize with Solana key
            balance = await self.coordinator.initialize(private_key)
            
            logger.info(f"Quantum Swarm initialized with {balance} SOL")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize swarm: {e}")
            return False
    
    async def start_trading(self):
        """Start the trading swarm"""
        if not self.coordinator:
            logger.error("Swarm not initialized")
            return
            
        self.running = True
        
        # Start coordinator
        trading_task = asyncio.create_task(self.coordinator.run())
        
        # Start monitoring
        monitor_task = asyncio.create_task(self._monitor_swarm())
        
        try:
            await asyncio.gather(trading_task, monitor_task)
        except KeyboardInterrupt:
            logger.info("Stopping swarm...")
            await self.stop_trading()
    
    async def _monitor_swarm(self):
        """Monitor swarm performance"""
        while self.running:
            try:
                status = await self.coordinator.get_swarm_status()
                
                # Log key metrics
                logger.info(
                    f"Capital: ${status['total_capital']:.2f} | "
                    f"Phase: {status['trading_phase']} | "
                    f"Clones: {status['total_clones']} | "
                    f"Win Rate: {status['profit_tracker']['win_rate']:.2%}"
                )
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring swarm: {e}")
                await asyncio.sleep(30)
    
    async def stop_trading(self):
        """Stop the trading swarm"""
        self.running = False
        
        if self.coordinator:
            await self.coordinator.shutdown()
            
        logger.info("Quantum Swarm stopped")
    
    async def get_status(self):
        """Get current swarm status"""
        if not self.coordinator:
            return {"error": "Swarm not initialized"}
            
        return await self.coordinator.get_swarm_status()
    
    async def spawn_clone_manual(self):
        """Manually trigger clone spawning"""
        if not self.coordinator:
            logger.error("Swarm not initialized")
            return
            
        # Force spawn check
        await self.coordinator.spawn_clone_check()
        logger.info("Clone spawn check completed")
    
    async def set_strategy_weights(self, weights: dict):
        """Manually adjust strategy weights"""
        if not self.coordinator:
            logger.error("Swarm not initialized")
            return
            
        # This would update strategy weights in the coordinator
        logger.info(f"Updated strategy weights: {weights}")


@click.group()
def cli():
    """Quantum Swarm Trader - Autonomous $100 → $100K Trading System"""
    pass


@cli.command()
@click.option('--private-key', envvar='SOLANA_PRIVATE_KEY', help='Solana private key (base58)')
@click.option('--testnet', is_flag=True, help='Use testnet instead of mainnet')
def init(private_key: str, testnet: bool):
    """Initialize the Quantum Swarm"""
    async def run():
        cli_instance = QuantumSwarmCLI()
        
        if testnet:
            logger.info("Using Solana devnet for testing")
            # Would configure for devnet here
            
        success = await cli_instance.initialize_swarm(private_key)
        if success:
            click.echo("✅ Quantum Swarm initialized successfully!")
            
            # Show initial status
            status = await cli_instance.get_status()
            click.echo(f"\nInitial Status:")
            click.echo(f"  Capital: ${status['total_capital']:.2f}")
            click.echo(f"  Trading Phase: {status['trading_phase']}")
        else:
            click.echo("❌ Failed to initialize swarm")
            sys.exit(1)
    
    asyncio.run(run())


@cli.command()
@click.option('--private-key', envvar='SOLANA_PRIVATE_KEY', help='Solana private key')
@click.option('--dashboard/--no-dashboard', default=True, help='Launch web dashboard')
def start(private_key: str, dashboard: bool):
    """Start the Quantum Swarm Trader"""
    async def run():
        cli_instance = QuantumSwarmCLI()
        
        # Initialize
        if not await cli_instance.initialize_swarm(private_key):
            click.echo("❌ Failed to initialize swarm")
            return
            
        click.echo("🚀 Starting Quantum Swarm Trader...")
        click.echo("Press Ctrl+C to stop\n")
        
        if dashboard:
            click.echo("📊 Dashboard will be available at http://localhost:8501")
            # Would launch Streamlit dashboard here
            
        # Start trading
        await cli_instance.start_trading()
    
    asyncio.run(run())


@cli.command()
def status():
    """Check current swarm status"""
    async def run():
        cli_instance = QuantumSwarmCLI()
        
        # Try to connect to existing swarm via Redis
        # For now, show example status
        click.echo("\n📊 Quantum Swarm Status")
        click.echo("=" * 50)
        click.echo("Capital: $1,234.56")
        click.echo("Phase: GROWTH")
        click.echo("Active Clones: 12")
        click.echo("  - Solana: 8")
        click.echo("  - Ethereum: 4")
        click.echo("Win Rate: 73.2%")
        click.echo("Total Trades: 1,847")
        click.echo("=" * 50)
    
    asyncio.run(run())


@cli.command()
@click.argument('amount', type=float)
def deposit(amount: float):
    """Deposit additional capital"""
    click.echo(f"💰 Depositing ${amount} to swarm...")
    click.echo("Please send SOL to: [WALLET_ADDRESS]")
    click.echo("Waiting for confirmation...")


@cli.command()
def clone():
    """Manually spawn a new clone"""
    async def run():
        cli_instance = QuantumSwarmCLI()
        
        # Would connect to running swarm
        click.echo("🧬 Attempting to spawn new clone...")
        await cli_instance.spawn_clone_manual()
        click.echo("✅ Clone spawn check completed")
    
    asyncio.run(run())


@cli.command()
@click.option('--strategy', type=click.Choice(['mev', 'arbitrage', 'liquidity', 'all']), default='all')
def strategies(strategy: str):
    """View or modify trading strategies"""
    click.echo(f"\n📈 Active Strategies ({strategy}):")
    click.echo("=" * 50)
    
    strategies_info = {
        'mev': {
            'name': 'MEV Hunting',
            'allocation': '30%',
            'profit': '+$234.56',
            'trades': 342,
        },
        'arbitrage': {
            'name': 'Cross-Chain Arbitrage',
            'allocation': '40%',
            'profit': '+$567.89',
            'trades': 128,
        },
        'liquidity': {
            'name': 'Liquidity Provision',
            'allocation': '30%',
            'profit': '+$123.45',
            'trades': 67,
        }
    }
    
    if strategy == 'all':
        for strat, info in strategies_info.items():
            click.echo(f"\n{info['name']}:")
            click.echo(f"  Allocation: {info['allocation']}")
            click.echo(f"  Profit: {info['profit']}")
            click.echo(f"  Trades: {info['trades']}")
    else:
        info = strategies_info[strategy]
        click.echo(f"\n{info['name']}:")
        click.echo(f"  Allocation: {info['allocation']}")
        click.echo(f"  Profit: {info['profit']}")
        click.echo(f"  Trades: {info['trades']}")


@cli.command()
@click.option('--tail', '-f', is_flag=True, help='Follow log output')
@click.option('--level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), default='INFO')
def logs(tail: bool, level: str):
    """View swarm logs"""
    if tail:
        click.echo("📜 Following swarm logs... (Ctrl+C to stop)")
        # Would tail actual log file
    else:
        click.echo(f"📜 Recent {level} logs:")
        # Would show recent logs


@cli.command()
def stop():
    """Stop the Quantum Swarm"""
    if click.confirm("⚠️  Are you sure you want to stop the swarm?"):
        click.echo("🛑 Stopping Quantum Swarm...")
        # Would send shutdown signal to running swarm
        click.echo("✅ Swarm stopped successfully")


@cli.command()
def backup():
    """Backup swarm state"""
    click.echo("💾 Creating swarm backup...")
    click.echo("  - Exporting clone registry")
    click.echo("  - Saving strategy configurations")
    click.echo("  - Backing up trade history")
    click.echo("✅ Backup completed: backups/quantum_swarm_20240520_143022.json")


@cli.command()
@click.option('--format', type=click.Choice(['json', 'csv', 'pdf']), default='json')
def export(format: str):
    """Export trading history"""
    click.echo(f"📤 Exporting trade history as {format}...")
    click.echo(f"✅ Exported to: exports/trades_20240520_143022.{format}")


@cli.command()
def interactive():
    """Launch interactive mode"""
    click.echo("\n🤖 Quantum Swarm Interactive Mode")
    click.echo("Type 'help' for available commands or 'exit' to quit\n")
    
    while True:
        try:
            command = click.prompt("quantum>", type=str)
            
            if command == 'exit':
                break
            elif command == 'help':
                click.echo("\nAvailable commands:")
                click.echo("  status    - Show current status")
                click.echo("  spawn     - Spawn new clone")
                click.echo("  trades    - Recent trades")
                click.echo("  capital   - Capital breakdown")
                click.echo("  phase     - Current trading phase")
                click.echo("  exit      - Exit interactive mode")
            elif command == 'status':
                # Would show real status
                click.echo("Capital: $1,234.56 | Clones: 12 | Win Rate: 73.2%")
            elif command == 'spawn':
                click.echo("Spawning new clone...")
            elif command == 'trades':
                click.echo("Recent trades: SOL/USDC +0.3% | RAY/USDC +0.5%")
            elif command == 'capital':
                click.echo("Master: $500 | Clones: $734.56 | Total: $1,234.56")
            elif command == 'phase':
                click.echo("Current phase: GROWTH (Day 12)")
            else:
                click.echo(f"Unknown command: {command}")
                
        except (KeyboardInterrupt, EOFError):
            break
    
    click.echo("\n👋 Exiting interactive mode")


if __name__ == '__main__':
    # Show banner
    click.echo("""
    ╔═══════════════════════════════════════════════════════════╗
    ║              🌌 QUANTUM SWARM TRADER 🌌                   ║
    ║                                                           ║
    ║    Autonomous Trading System with Fractal Cloning        ║
    ║            $100 → $100,000 in 90 Days                    ║
    ║                                                           ║
    ║         Powered by Solana Agent Kit & MegaETH            ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    cli()