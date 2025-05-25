"""
Quantum Swarm Trader - Terminal UI Dashboard
Built with Textual for beautiful terminal interfaces
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
import random
from decimal import Decimal
import json

# Import our coordinator (mock for UI demo)
class MockSwarmData:
    """Mock data generator for UI development"""
    
    def __init__(self):
        self.capital = 1234.56
        self.clones = 12
        self.win_rate = 0.732
        self.phase = "GROWTH"
        self.trades_today = 847
        self.profit_today = 234.56
        
    def get_status(self):
        # Simulate some changes
        self.capital += random.uniform(-10, 20)
        self.profit_today += random.uniform(-5, 10)
        self.trades_today += random.randint(0, 3)
        
        return {
            "capital": self.capital,
            "clones": self.clones,
            "win_rate": self.win_rate,
            "phase": self.phase,
            "trades_today": self.trades_today,
            "profit_today": self.profit_today,
            "profit_percent": (self.profit_today / (self.capital - self.profit_today)) * 100
        }
    
    def get_clone_list(self):
        clones = []
        for i in range(self.clones):
            clones.append({
                "id": f"clone_{i+1}",
                "specialization": random.choice(["MEV Hunter", "Arbitrage", "Liquidity", "Social"]),
                "balance": random.uniform(50, 200),
                "trades": random.randint(10, 100),
                "profit": random.uniform(-10, 50),
                "status": random.choice(["Active", "Active", "Active", "Idle"])
            })
        return clones
    
    def get_recent_trades(self):
        trades = []
        tokens = ["SOL/USDC", "RAY/USDC", "ORCA/USDC", "BONK/USDC", "JUP/USDC"]
        for i in range(10):
            trades.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "pair": random.choice(tokens),
                "type": random.choice(["ARB", "MEV", "SWAP"]),
                "profit": random.uniform(-1, 5),
                "clone": f"clone_{random.randint(1, self.clones)}"
            })
        return trades


class MetricsWidget(Static):
    """Display key metrics"""
    
    def __init__(self, mock_data):
        super().__init__()
        self.mock_data = mock_data
        
    def compose(self) -> ComposeResult:
        yield Static(id="metrics-display")
        
    def on_mount(self) -> None:
        self.update_metrics()
        self.set_interval(1.0, self.update_metrics)
        
    def update_metrics(self) -> None:
        data = self.mock_data.get_status()
        
        metrics_text = f"""[bold cyan]💰 Capital:[/bold cyan] [bold green]${data['capital']:,.2f}[/bold green]
[bold cyan]🧬 Clones:[/bold cyan] [bold white]{data['clones']}[/bold white]
[bold cyan]📈 Win Rate:[/bold cyan] [bold yellow]{data['win_rate']:.1%}[/bold yellow]
[bold cyan]🎯 Phase:[/bold cyan] [bold magenta]{data['phase']}[/bold magenta]

[bold cyan]Today's Performance:[/bold cyan]
[bold cyan]📊 Trades:[/bold cyan] {data['trades_today']}
[bold cyan]💵 Profit:[/bold cyan] [bold {'green' if data['profit_today'] > 0 else 'red'}]${data['profit_today']:+,.2f} ({data['profit_percent']:+.2f}%)[/bold {'green' if data['profit_today'] > 0 else 'red'}]"""
        
        self.query_one("#metrics-display").update(
            Panel(metrics_text, title="[bold]Swarm Metrics[/bold]", border_style="cyan")
        )


class CloneTable(Static):
    """Display clone status table"""
    
    def __init__(self, mock_data):
        super().__init__()
        self.mock_data = mock_data
        
    def compose(self) -> ComposeResult:
        yield DataTable(id="clone-table")
        
    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("ID", "Type", "Balance", "Trades", "Profit", "Status")
        self.update_clones()
        self.set_interval(2.0, self.update_clones)
        
    def update_clones(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        
        clones = self.mock_data.get_clone_list()
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
    """Display recent trades"""
    
    def __init__(self, mock_data):
        super().__init__()
        self.mock_data = mock_data
        
    def compose(self) -> ComposeResult:
        yield ScrollableContainer(Static(id="trade-log-content"))
        
    def on_mount(self) -> None:
        self.update_trades()
        self.set_interval(1.5, self.update_trades)
        
    def update_trades(self) -> None:
        trades = self.mock_data.get_recent_trades()
        
        trade_lines = ["[bold cyan]Recent Trades:[/bold cyan]\n"]
        for trade in trades:
            profit_style = "green" if trade["profit"] > 0 else "red"
            trade_lines.append(
                f"[dim]{trade['time']}[/dim] [{trade['type']}] {trade['pair']} "
                f"[{profit_style}]{trade['profit']:+.2f}%[/{profit_style}] "
                f"[dim]({trade['clone']})[/dim]"
            )
        
        content = self.query_one("#trade-log-content")
        content.update("\n".join(trade_lines))


class PerformanceChart(Static):
    """Simple performance sparkline"""
    
    def __init__(self):
        super().__init__()
        self.data = [100]  # Starting capital
        
    def compose(self) -> ComposeResult:
        yield Sparkline(
            self.data,
            id="performance-sparkline",
            summary_function=lambda data: f"Capital: ${data[-1]:,.2f}"
        )
        
    def on_mount(self) -> None:
        self.set_interval(2.0, self.update_chart)
        
    def update_chart(self) -> None:
        # Simulate capital growth
        last_value = self.data[-1]
        change = random.uniform(-2, 3)  # -2% to +3% change
        new_value = last_value * (1 + change / 100)
        self.data.append(new_value)
        
        # Keep last 50 points
        if len(self.data) > 50:
            self.data.pop(0)
            
        sparkline = self.query_one("#performance-sparkline")
        sparkline.data = self.data
        sparkline.refresh()


class ActionButtons(Static):
    """Control buttons"""
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="button-container"):
            yield Button("🧬 Spawn Clone", id="spawn-clone", variant="primary")
            yield Button("⚙️ Settings", id="settings", variant="default")
            yield Button("📊 Full Stats", id="full-stats", variant="default")
            yield Button("🛑 Emergency Stop", id="emergency-stop", variant="error")


class QuantumSwarmTUI(App):
    """Main TUI Application"""
    
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
        ("d", "toggle_dark", "Toggle Dark Mode"),
    ]
    
    def __init__(self):
        super().__init__()
        self.mock_data = MockSwarmData()
        self.title = "🌌 Quantum Swarm Trader"
        self.sub_title = "Autonomous Trading System"
        
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            MetricsWidget(self.mock_data),
            id="metrics-container"
        )
        yield Container(
            CloneTable(self.mock_data),
            TradeLog(self.mock_data),
            PerformanceChart(),
            ActionButtons(),
            id="main-content"
        )
        yield Footer()
        
    def action_spawn_clone(self) -> None:
        self.mock_data.clones += 1
        self.notify("🧬 Spawning new clone...", severity="information")
        
    def action_toggle_dark(self) -> None:
        self.dark = not self.dark
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if button_id == "spawn-clone":
            self.action_spawn_clone()
        elif button_id == "emergency-stop":
            self.notify("🛑 EMERGENCY STOP ACTIVATED", severity="error")
            # Would trigger actual emergency stop
        elif button_id == "settings":
            self.notify("⚙️ Settings panel coming soon", severity="information")
        elif button_id == "full-stats":
            self.notify("📊 Opening full statistics...", severity="information")


class SimpleTUI:
    """Simpler alternative using Rich only"""
    
    def __init__(self):
        self.console = Console()
        self.mock_data = MockSwarmData()
        
    def create_layout(self):
        """Create the dashboard layout"""
        layout = Layout()
        
        # Split into header and body
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Split body into left and right
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        # Split left into metrics and chart
        layout["left"].split_column(
            Layout(name="metrics", size=10),
            Layout(name="chart")
        )
        
        # Split right into clones and trades
        layout["right"].split_column(
            Layout(name="clones"),
            Layout(name="trades", size=12)
        )
        
        return layout
    
    def update_header(self, layout):
        header = Table.grid(expand=True)
        header.add_column(justify="center")
        header.add_row(
            "[bold cyan]🌌 QUANTUM SWARM TRADER[/bold cyan]\n"
            "[dim]Autonomous Trading System[/dim]"
        )
        layout["header"].update(Panel(header, style="cyan"))
    
    def update_metrics(self, layout):
        data = self.mock_data.get_status()
        
        metrics = Table.grid(expand=True, padding=1)
        metrics.add_column(style="cyan", justify="right")
        metrics.add_column(min_width=20)
        
        metrics.add_row("💰 Capital:", f"[bold green]${data['capital']:,.2f}[/bold green]")
        metrics.add_row("🧬 Clones:", f"[bold white]{data['clones']}[/bold white]")
        metrics.add_row("📈 Win Rate:", f"[bold yellow]{data['win_rate']:.1%}[/bold yellow]")
        metrics.add_row("🎯 Phase:", f"[bold magenta]{data['phase']}[/bold magenta]")
        
        layout["metrics"].update(Panel(metrics, title="Swarm Metrics", border_style="cyan"))
    
    def update_clones(self, layout):
        clones = self.mock_data.get_clone_list()
        
        table = Table(title="Active Clones", border_style="blue")
        table.add_column("ID", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Balance", justify="right")
        table.add_column("Profit", justify="right")
        
        for clone in clones[:8]:  # Show top 8
            profit_style = "green" if clone["profit"] > 0 else "red"
            table.add_row(
                clone["id"],
                clone["specialization"],
                f"${clone['balance']:.2f}",
                f"[{profit_style}]${clone['profit']:+.2f}[/{profit_style}]"
            )
        
        layout["clones"].update(table)
    
    def update_trades(self, layout):
        trades = self.mock_data.get_recent_trades()
        
        trade_text = "[bold cyan]Recent Trades:[/bold cyan]\n\n"
        for trade in trades[:8]:
            profit_style = "green" if trade["profit"] > 0 else "red"
            trade_text += (
                f"[dim]{trade['time']}[/dim] {trade['pair']} "
                f"[{profit_style}]{trade['profit']:+.2f}%[/{profit_style}]\n"
            )
        
        layout["trades"].update(Panel(trade_text, title="Trade Log", border_style="green"))
    
    def update_chart(self, layout):
        # Simple ASCII chart
        chart = """
    $2000 │     ╭─╮
    $1800 │   ╭─╯ ╰─╮
    $1600 │ ╭─╯     ╰─╮
    $1400 │╭╯         ╰─╮
    $1200 ├─────────────╯
    $1000 │
          └─────────────────
          1h  4h  8h  12h  24h
        """
        layout["chart"].update(Panel(chart, title="Performance", border_style="green"))
    
    def update_footer(self, layout):
        footer = "[bold]Commands:[/bold] [cyan]Q[/cyan]uit | [cyan]S[/cyan]pawn Clone | [cyan]R[/cyan]efresh | [cyan]E[/cyan]mergency Stop"
        layout["footer"].update(Panel(footer, style="dim"))
    
    async def run(self):
        """Run the simple TUI"""
        layout = self.create_layout()
        
        with Live(layout, refresh_per_second=2, screen=True) as live:
            while True:
                self.update_header(layout)
                self.update_metrics(layout)
                self.update_clones(layout)
                self.update_trades(layout)
                self.update_chart(layout)
                self.update_footer(layout)
                
                await asyncio.sleep(1)


def main():
    """Entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        # Run simple Rich-based TUI
        tui = SimpleTUI()
        try:
            asyncio.run(tui.run())
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
    else:
        # Run full Textual TUI
        app = QuantumSwarmTUI()
        app.run()


if __name__ == "__main__":
    main()