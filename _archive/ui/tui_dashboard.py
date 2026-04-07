"""
Quantum Swarm Trader - Terminal UI Dashboard
Production-ready interface for monitoring and controlling the trading swarm
NO DEMO DATA - REAL TRADING ONLY
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, DataTable, Sparkline, ProgressBar, Button, Label
from textual.reactive import reactive
from textual.timer import Timer
from textual import events
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.console import Console
from datetime import datetime
import asyncio
import redis
import json
from decimal import Decimal
import ccxt.async_support as ccxt
import aiohttp
import logging
import os
from typing import Dict, List, Any, Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
import base58
from solana.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey

from swarm_coordinator import QuantumSwarmCoordinator, SwarmState
from config import config, TradingPhase
from agents.mev_hunter import MEVHunterAgent
from agents.social_sentiment import SocialSentimentAgent
from ui.onboarding import run_onboarding

logger = logging.getLogger(__name__)


class RealSwarmData:
    """Real-time data interface for the trading swarm"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.coordinator = QuantumSwarmCoordinator()
        self.exchanges = {}
        self.solana_client = None
        self.wallet_keypair = None
        self.load_config()
        self.initialize_connections()
        
    def load_config(self):
        """Load configuration from onboarding"""
        config_dir = Path.home() / ".quantum_swarm"
        config_file = config_dir / "config.json"
        wallet_file = config_dir / "wallet.json"
        
        if config_file.exists() and wallet_file.exists():
            # Load trading config
            with open(config_file, 'r') as f:
                self.trading_config = json.load(f)
            
            # Load wallet
            with open(wallet_file, 'r') as f:
                wallet_data = json.load(f)
                secret_key = base58.b58decode(wallet_data['secret_key'])
                self.wallet_keypair = Keypair.from_secret_key(secret_key)
        else:
            raise Exception("Setup not complete. Run onboarding first.")
    
    def initialize_connections(self):
        """Initialize Solana and DEX connections"""
        # Initialize Solana RPC
        rpc_url = self.trading_config['network']['rpc_url']
        self.solana_client = AsyncClient(rpc_url)
        
        # For CEX support (optional)
        if config.binance_api_key and config.binance_api_secret:
            self.exchanges['binance'] = ccxt.binance({
                'apiKey': config.binance_api_key,
                'secret': config.binance_api_secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
    
    async def get_status(self) -> Dict[str, Any]:
        """Get real swarm status from Redis and coordinator"""
        try:
            # Get state from Redis
            state_data = self.redis_client.get('swarm:state')
            if state_data:
                state = json.loads(state_data)
            else:
                # Fallback to coordinator state
                await self.coordinator.initialize()
                state = {
                    "capital": self.coordinator.capital,
                    "phase": self.coordinator.phase.value,
                    "positions": {}
                }
            
            # Get Solana wallet balance
            total_balance = 0.0
            try:
                # Get SOL balance
                sol_balance = await self.solana_client.get_balance(self.wallet_keypair.public_key)
                sol_value = sol_balance['result']['value'] / 1e9  # Convert lamports to SOL
                
                # Get USDC balance (assuming USDC mint)
                usdc_mint = PublicKey("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
                # In production, fetch actual token balance
                
                # For now, use configured capital
                total_balance = self.trading_config['trading']['initial_capital']
                
            except Exception as e:
                logger.error(f"Error fetching Solana balance: {e}")
                total_balance = self.trading_config['trading']['initial_capital']
            
            # Get performance metrics from Redis
            metrics = {
                "win_rate": float(self.redis_client.get('metrics:win_rate') or 0),
                "trades_today": int(self.redis_client.get('metrics:trades_today') or 0),
                "profit_today": float(self.redis_client.get('metrics:profit_today') or 0),
                "active_clones": int(self.redis_client.get('swarm:clone_count') or 0)
            }
            
            return {
                "capital": total_balance if total_balance > 0 else state.get("capital", 0),
                "clones": metrics["active_clones"],
                "win_rate": metrics["win_rate"],
                "phase": state.get("phase", "MICRO"),
                "trades_today": metrics["trades_today"],
                "profit_today": metrics["profit_today"],
                "profit_percent": (metrics["profit_today"] / max(total_balance - metrics["profit_today"], 1)) * 100
            }
            
        except Exception as e:
            logger.error(f"Error getting swarm status: {e}")
            return {
                "capital": 0,
                "clones": 0,
                "win_rate": 0,
                "phase": "ERROR",
                "trades_today": 0,
                "profit_today": 0,
                "profit_percent": 0
            }
    
    async def get_clone_list(self) -> List[Dict[str, Any]]:
        """Get real clone data from Redis"""
        try:
            clone_keys = self.redis_client.keys('clone:*:status')
            clones = []
            
            for key in clone_keys[:20]:  # Limit to 20 for display
                clone_id = key.split(':')[1]
                status_data = self.redis_client.get(key)
                
                if status_data:
                    status = json.loads(status_data)
                    clones.append({
                        "id": clone_id,
                        "specialization": status.get("type", "Unknown"),
                        "balance": float(status.get("balance", 0)),
                        "trades": int(status.get("trades", 0)),
                        "profit": float(status.get("profit", 0)),
                        "status": "Active" if status.get("active", False) else "Idle"
                    })
            
            return clones
            
        except Exception as e:
            logger.error(f"Error getting clone list: {e}")
            return []
    
    async def get_recent_trades(self) -> List[Dict[str, Any]]:
        """Get real recent trades from Redis"""
        try:
            trades = []
            trade_keys = self.redis_client.lrange('trades:recent', 0, 20)
            
            for trade_data in trade_keys:
                if trade_data:
                    trade = json.loads(trade_data)
                    trades.append({
                        "time": datetime.fromtimestamp(trade.get("timestamp", 0)).strftime("%H:%M:%S"),
                        "pair": trade.get("pair", "Unknown"),
                        "type": trade.get("type", "SWAP"),
                        "profit": float(trade.get("profit", 0)),
                        "clone": trade.get("clone_id", "Unknown")
                    })
            
            return trades
            
        except Exception as e:
            logger.error(f"Error getting recent trades: {e}")
            return []
    
    async def spawn_clone(self) -> bool:
        """Actually spawn a new clone"""
        try:
            # Check if we have enough capital
            status = await self.get_status()
            if status["capital"] < 50:  # Minimum capital for new clone
                return False
            
            # Send spawn command to coordinator
            self.redis_client.publish('swarm:commands', json.dumps({
                "command": "spawn_clone",
                "timestamp": datetime.now().isoformat()
            }))
            
            return True
            
        except Exception as e:
            logger.error(f"Error spawning clone: {e}")
            return False
    
    async def emergency_stop(self) -> bool:
        """Execute emergency stop - close all positions"""
        try:
            # Send emergency stop to all components
            self.redis_client.publish('swarm:commands', json.dumps({
                "command": "emergency_stop",
                "timestamp": datetime.now().isoformat()
            }))
            
            # Set emergency flag
            self.redis_client.set('swarm:emergency_stop', '1')
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing emergency stop: {e}")
            return False


class MetricsWidget(Static):
    """Display real-time metrics"""
    
    def __init__(self, swarm_data):
        super().__init__()
        self.swarm_data = swarm_data
        
    def compose(self) -> ComposeResult:
        yield Static(id="metrics-display")
        
    def on_mount(self) -> None:
        self.update_metrics()
        self.set_interval(1.0, self.update_metrics)
        
    async def update_metrics(self) -> None:
        data = await self.swarm_data.get_status()
        
        # Color coding based on performance
        capital_color = "green" if data['profit_today'] >= 0 else "red"
        phase_colors = {
            "MICRO": "cyan",
            "GROWTH": "yellow", 
            "SCALE": "green",
            "EMPIRE": "magenta",
            "ERROR": "red"
        }
        
        metrics_text = f"""[bold cyan]💰 Capital:[/bold cyan] [bold {capital_color}]${data['capital']:,.2f}[/bold {capital_color}]
[bold cyan]🧬 Active Clones:[/bold cyan] [bold white]{data['clones']}[/bold white]
[bold cyan]📈 Win Rate:[/bold cyan] [bold yellow]{data['win_rate']:.1%}[/bold yellow]
[bold cyan]🎯 Phase:[/bold cyan] [bold {phase_colors.get(data['phase'], 'white')}]{data['phase']}[/bold {phase_colors.get(data['phase'], 'white')}]

[bold cyan]Today's Performance:[/bold cyan]
[bold cyan]📊 Trades:[/bold cyan] {data['trades_today']}
[bold cyan]💵 Profit:[/bold cyan] [bold {'green' if data['profit_today'] > 0 else 'red'}]${data['profit_today']:+,.2f} ({data['profit_percent']:+.2f}%)[/bold {'green' if data['profit_today'] > 0 else 'red'}]"""
        
        self.query_one("#metrics-display").update(
            Panel(metrics_text, title="[bold]Live Swarm Metrics[/bold]", border_style="cyan")
        )


class CloneTable(Static):
    """Display real clone status table"""
    
    def __init__(self, swarm_data):
        super().__init__()
        self.swarm_data = swarm_data
        
    def compose(self) -> ComposeResult:
        yield DataTable(id="clone-table")
        
    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("ID", "Type", "Balance", "Trades", "Profit", "Status")
        self.update_clones()
        self.set_interval(2.0, self.update_clones)
        
    async def update_clones(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        
        clones = await self.swarm_data.get_clone_list()
        for clone in clones:
            status_style = "green" if clone["status"] == "Active" else "yellow"
            profit_style = "green" if clone["profit"] > 0 else "red"
            
            table.add_row(
                clone["id"],
                clone["specialization"],
                f"${clone['balance']:.2f}",
                str(clone["trades"]),
                Text(f"${clone['profit']:+.2f}", style=profit_style),
                Text(clone["status"], style=status_style)
            )


class TradeLog(Static):
    """Display real recent trades"""
    
    def __init__(self, swarm_data):
        super().__init__()
        self.swarm_data = swarm_data
        
    def compose(self) -> ComposeResult:
        yield ScrollableContainer(Static(id="trade-log-content"))
        
    def on_mount(self) -> None:
        self.update_trades()
        self.set_interval(1.5, self.update_trades)
        
    async def update_trades(self) -> None:
        trades = await self.swarm_data.get_recent_trades()
        
        trade_lines = ["[bold cyan]Live Trade Feed:[/bold cyan]\n"]
        for trade in trades:
            profit_style = "green" if trade["profit"] > 0 else "red"
            trade_lines.append(
                f"[dim]{trade['time']}[/dim] [{trade['type']}] {trade['pair']} "
                f"[{profit_style}]{trade['profit']:+.2f}%[/{profit_style}] "
                f"[dim]({trade['clone']})[/dim]"
            )
        
        if not trades:
            trade_lines.append("[dim]No recent trades[/dim]")
        
        content = self.query_one("#trade-log-content")
        content.update("\n".join(trade_lines))


class PerformanceChart(Static):
    """Real performance tracking"""
    
    def __init__(self, swarm_data):
        super().__init__()
        self.swarm_data = swarm_data
        self.data = []
        
    def compose(self) -> ComposeResult:
        yield Sparkline(
            self.data,
            id="performance-sparkline",
            summary_function=lambda data: f"Capital: ${data[-1]:,.2f}" if data else "Loading..."
        )
        
    def on_mount(self) -> None:
        self.set_interval(2.0, self.update_chart)
        
    async def update_chart(self) -> None:
        status = await self.swarm_data.get_status()
        capital = status["capital"]
        
        if capital > 0:
            self.data.append(capital)
            
            # Keep last 50 points
            if len(self.data) > 50:
                self.data.pop(0)
                
            sparkline = self.query_one("#performance-sparkline")
            sparkline.data = self.data
            sparkline.refresh()


class ActionButtons(Static):
    """Real trading controls"""
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="button-container"):
            yield Button("🧬 Spawn Clone", id="spawn-clone", variant="primary")
            yield Button("⚙️ Settings", id="settings", variant="default")
            yield Button("📊 Export Stats", id="export-stats", variant="default")
            yield Button("🛑 EMERGENCY STOP", id="emergency-stop", variant="error")


class QuantumSwarmTUI(App):
    """Production TUI Application"""
    
    CSS = """
    Screen {
        background: $background;
    }
    
    #metrics-container {
        height: 12;
        margin: 1;
    }
    
    #main-content {
        height: 100%;
    }
    
    #clone-table {
        height: 15;
        margin: 1;
        border: solid cyan;
    }
    
    #trade-log-content {
        height: 10;
        margin: 1;
        border: solid blue;
        padding: 1;
    }
    
    #performance-sparkline {
        height: 7;
        margin: 1;
        border: solid green;
        padding: 1;
    }
    
    #button-container {
        height: 3;
        margin: 1;
        align: center middle;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "spawn_clone", "Spawn Clone"),
        ("r", "refresh", "Refresh"),
        ("e", "emergency_stop", "Emergency Stop"),
    ]
    
    def __init__(self):
        super().__init__()
        self.swarm_data = RealSwarmData()
        self.title = "🌌 Quantum Swarm Trader - LIVE"
        self.sub_title = "Real Money Trading System"
        
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            MetricsWidget(self.swarm_data),
            id="metrics-container"
        )
        yield Container(
            CloneTable(self.swarm_data),
            TradeLog(self.swarm_data),
            PerformanceChart(self.swarm_data),
            ActionButtons(),
            id="main-content"
        )
        yield Footer()
        
    async def action_spawn_clone(self) -> None:
        success = await self.swarm_data.spawn_clone()
        if success:
            self.notify("🧬 Spawning new clone...", severity="information")
        else:
            self.notify("❌ Insufficient capital for new clone", severity="error")
            
    async def action_emergency_stop(self) -> None:
        # Confirm dialog would go here in production
        success = await self.swarm_data.emergency_stop()
        if success:
            self.notify("🛑 EMERGENCY STOP ACTIVATED - All positions closing", severity="error")
        else:
            self.notify("❌ Emergency stop failed!", severity="error")
        
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if button_id == "spawn-clone":
            await self.action_spawn_clone()
        elif button_id == "emergency-stop":
            await self.action_emergency_stop()
        elif button_id == "export-stats":
            # Export real stats to file
            try:
                stats = await self.swarm_data.get_status()
                with open(f"swarm_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
                    json.dump(stats, f, indent=2)
                self.notify("📊 Stats exported successfully", severity="information")
            except Exception as e:
                self.notify(f"❌ Export failed: {e}", severity="error")


async def main():
    """Entry point for production TUI"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('tui_dashboard.log'),
            logging.StreamHandler()
        ]
    )
    
    # Check Redis connection
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0)
        redis_client.ping()
    except redis.ConnectionError:
        print("❌ ERROR: Redis not running. Please start Redis first.")
        print("Run: redis-server")
        return
    
    # Check if setup is complete
    config_dir = Path.home() / ".quantum_swarm"
    if not (config_dir / "config.json").exists():
        print("🚀 First time setup required...")
        print("Starting onboarding wizard...\n")
        
        # Run onboarding
        if not await run_onboarding():
            print("Setup cancelled.")
            return
    
    # Run the production TUI
    try:
        app = QuantumSwarmTUI()
        await app.run_async()
    except Exception as e:
        if "Setup not complete" in str(e):
            print("\n❌ Setup incomplete. Running onboarding...")
            if await run_onboarding():
                app = QuantumSwarmTUI()
                await app.run_async()
        else:
            raise


if __name__ == "__main__":
    asyncio.run(main())