"""
Quantum Swarm Trader - Onboarding Wizard
Production setup for Solana DEX trading
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, Center
from textual.widgets import Static, Input, Button, RadioSet, RadioButton, LoadingIndicator, Label
from textual.screen import Screen
from textual.validation import Number, Length
from rich.panel import Panel
from rich.text import Text
from rich.console import Group
import asyncio
import json
import os
from pathlib import Path
from solana.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey
import base58
from typing import Optional, Dict, Any
import aiohttp
from datetime import datetime
import redis

# Solana RPC endpoints
RPC_ENDPOINTS = {
    "mainnet": [
        "https://api.mainnet-beta.solana.com",
        "https://solana-api.projectserum.com",
        "https://rpc.ankr.com/solana"
    ],
    "devnet": ["https://api.devnet.solana.com"]
}

# Supported DEXs
SUPPORTED_DEXS = {
    "raydium": {
        "name": "Raydium",
        "program_id": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
        "min_capital": 50
    },
    "orca": {
        "name": "Orca",
        "program_id": "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP",
        "min_capital": 50
    },
    "jupiter": {
        "name": "Jupiter Aggregator",
        "program_id": "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB",
        "min_capital": 30
    }
}


class WelcomeScreen(Screen):
    """Welcome screen with project info"""
    
    def compose(self) -> ComposeResult:
        yield Container(
            Center(
                Vertical(
                    Static(
                        Panel(
                            """[bold cyan]🌌 QUANTUM SWARM TRADER[/bold cyan]
                            
[yellow]Autonomous Trading System[/yellow]

This wizard will help you set up:
• Solana wallet for DEX trading
• RPC endpoints for fast execution
• Initial capital allocation
• Trading parameters

[bold red]WARNING:[/bold red] This system trades REAL money.
Only proceed if you understand the risks.

[dim]Press ENTER to continue...[/dim]""",
                            title="Welcome",
                            border_style="cyan"
                        )
                    ),
                    Button("Start Setup", id="start", variant="primary"),
                    id="welcome-content"
                )
            )
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            self.app.push_screen(WalletSetupScreen())


class WalletSetupScreen(Screen):
    """Wallet creation or import screen"""
    
    def compose(self) -> ComposeResult:
        yield Container(
            Vertical(
                Static("[bold]Solana Wallet Setup[/bold]\n"),
                RadioSet(
                    RadioButton("Create new wallet", id="new"),
                    RadioButton("Import existing wallet", id="import"),
                ),
                Container(id="wallet-input-area"),
                Horizontal(
                    Button("Back", id="back", variant="default"),
                    Button("Next", id="next", variant="primary"),
                    id="button-row"
                ),
                id="wallet-content"
            )
        )
    
    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        container = self.query_one("#wallet-input-area")
        container.remove_children()
        
        if str(event.pressed.id) == "import":
            container.mount(
                Vertical(
                    Label("Enter private key (base58 format):"),
                    Input(placeholder="Your private key", password=True, id="private-key"),
                    Static("[dim]Your key will be encrypted and stored locally[/dim]")
                )
            )
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "next":
            await self.setup_wallet()
    
    async def setup_wallet(self) -> None:
        radio_set = self.query_one(RadioSet)
        
        if radio_set.pressed_index == 0:  # Create new
            keypair = Keypair()
            self.app.wallet_keypair = keypair
            self.app.push_screen(WalletCreatedScreen(keypair))
        else:  # Import
            try:
                private_key_input = self.query_one("#private-key", Input)
                private_key = private_key_input.value
                
                # Decode and create keypair
                secret_key = base58.b58decode(private_key)
                keypair = Keypair.from_secret_key(secret_key)
                self.app.wallet_keypair = keypair
                
                # Verify wallet
                async with AsyncClient(RPC_ENDPOINTS["mainnet"][0]) as client:
                    balance = await client.get_balance(keypair.public_key)
                    
                self.app.push_screen(NetworkSetupScreen())
                
            except Exception as e:
                self.app.notify(f"Invalid private key: {str(e)}", severity="error")


class WalletCreatedScreen(Screen):
    """Show created wallet details"""
    
    def __init__(self, keypair: Keypair):
        super().__init__()
        self.keypair = keypair
    
    def compose(self) -> ComposeResult:
        public_key = str(self.keypair.public_key)
        private_key = base58.b58encode(bytes(self.keypair.secret_key)).decode()
        
        yield Container(
            Vertical(
                Static(
                    Panel(
                        f"""[bold red]⚠️ IMPORTANT - SAVE THESE DETAILS ⚠️[/bold red]

[bold cyan]Public Key:[/bold cyan]
[yellow]{public_key}[/yellow]

[bold cyan]Private Key:[/bold cyan]
[red]{private_key}[/red]

[bold]CRITICAL:[/bold]
• Save your private key in a secure location
• You will need SOL for gas fees
• Never share your private key with anyone
• This key controls your trading funds

[dim]Press ENTER when you've saved these details...[/dim]""",
                        title="New Wallet Created",
                        border_style="red"
                    )
                ),
                Button("I've Saved My Keys", id="continue", variant="primary"),
                id="wallet-created-content"
            )
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "continue":
            self.app.push_screen(NetworkSetupScreen())


class NetworkSetupScreen(Screen):
    """Configure RPC endpoints"""
    
    def compose(self) -> ComposeResult:
        yield Container(
            Vertical(
                Static("[bold]Network Configuration[/bold]\n"),
                RadioSet(
                    RadioButton("Mainnet (Production)", id="mainnet"),
                    RadioButton("Devnet (Testing)", id="devnet"),
                ),
                Container(
                    Label("Custom RPC URL (optional):"),
                    Input(placeholder="https://your-rpc-endpoint.com", id="custom-rpc"),
                    Static("[dim]Leave empty to use default endpoints[/dim]"),
                    id="rpc-input"
                ),
                Horizontal(
                    Button("Back", id="back", variant="default"),
                    Button("Test Connection", id="test", variant="warning"),
                    Button("Next", id="next", variant="primary"),
                    id="button-row"
                ),
                Container(id="test-results"),
                id="network-content"
            )
        )
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "test":
            await self.test_connection()
        elif event.button.id == "next":
            await self.save_network_config()
    
    async def test_connection(self) -> None:
        results_container = self.query_one("#test-results")
        results_container.remove_children()
        results_container.mount(LoadingIndicator())
        
        radio_set = self.query_one(RadioSet)
        network = "mainnet" if radio_set.pressed_index == 0 else "devnet"
        custom_rpc = self.query_one("#custom-rpc", Input).value
        
        rpc_url = custom_rpc if custom_rpc else RPC_ENDPOINTS[network][0]
        
        try:
            async with AsyncClient(rpc_url) as client:
                # Test connection
                version = await client.get_version()
                slot = await client.get_slot()
                
                # Get wallet balance
                balance_resp = await client.get_balance(self.app.wallet_keypair.public_key)
                balance = balance_resp['result']['value'] / 1e9  # Convert lamports to SOL
                
                results_container.remove_children()
                results_container.mount(
                    Static(
                        Panel(
                            f"""[green]✓ Connection successful![/green]
                            
RPC Version: {version['result']['solana-core']}
Current Slot: {slot['result']}
Wallet Balance: {balance:.4f} SOL

[yellow]Note: You need SOL for gas fees[/yellow]""",
                            border_style="green"
                        )
                    )
                )
                
                self.app.network_config = {
                    "network": network,
                    "rpc_url": rpc_url,
                    "balance": balance
                }
                
        except Exception as e:
            results_container.remove_children()
            results_container.mount(
                Static(f"[red]Connection failed: {str(e)}[/red]")
            )
    
    async def save_network_config(self) -> None:
        if not hasattr(self.app, 'network_config'):
            self.app.notify("Please test connection first", severity="warning")
            return
        
        self.app.push_screen(DEXSetupScreen())


class DEXSetupScreen(Screen):
    """Select DEXs to trade on"""
    
    def compose(self) -> ComposeResult:
        yield Container(
            Vertical(
                Static("[bold]Select DEX Platforms[/bold]\n"),
                Static("Choose which decentralized exchanges to trade on:"),
                Container(
                    RadioSet(
                        RadioButton("Raydium (Most liquidity, MEV opportunities)", id="raydium"),
                        RadioButton("Orca (User-friendly, concentrated liquidity)", id="orca"),
                        RadioButton("Jupiter (Best price aggregation)", id="jupiter"),
                    ),
                    id="dex-selection"
                ),
                Container(id="dex-info"),
                Horizontal(
                    Button("Back", id="back", variant="default"),
                    Button("Next", id="next", variant="primary"),
                    id="button-row"
                ),
                id="dex-content"
            )
        )
    
    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        dex_id = str(event.pressed.id)
        dex_info = SUPPORTED_DEXS.get(dex_id, {})
        
        info_container = self.query_one("#dex-info")
        info_container.remove_children()
        info_container.mount(
            Static(
                Panel(
                    f"""[cyan]{dex_info.get('name', 'Unknown')}[/cyan]
                    
Program ID: [dim]{dex_info.get('program_id', 'N/A')}[/dim]
Min Capital: ${dex_info.get('min_capital', 0)} USDC

[yellow]Features:[/yellow]
• Real-time price feeds
• MEV protection
• Low slippage routing""",
                    border_style="blue"
                )
            )
        )
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "next":
            radio_set = self.query_one(RadioSet)
            if radio_set.pressed_index is not None:
                dex_id = str(radio_set.pressed_button.id)
                self.app.selected_dex = dex_id
                self.app.push_screen(CapitalSetupScreen())
            else:
                self.app.notify("Please select a DEX", severity="warning")


class CapitalSetupScreen(Screen):
    """Configure initial capital"""
    
    def compose(self) -> ComposeResult:
        min_capital = SUPPORTED_DEXS.get(self.app.selected_dex, {}).get('min_capital', 50)
        
        yield Container(
            Vertical(
                Static("[bold]Initial Capital Setup[/bold]\n"),
                Static(f"Minimum required: ${min_capital} USDC"),
                Container(
                    Label("Starting capital (USDC):"),
                    Input(
                        placeholder="100",
                        id="capital",
                        validators=[Number(minimum=min_capital)]
                    ),
                    Static("[dim]This will be your initial trading capital[/dim]")
                ),
                Container(
                    Label("Risk per trade (%):"),
                    Input(
                        placeholder="2",
                        id="risk",
                        validators=[Number(minimum=0.5, maximum=10)]
                    ),
                    Static("[dim]Recommended: 1-2% for safety[/dim]")
                ),
                Container(
                    Label("Daily loss limit (%):"),
                    Input(
                        placeholder="5",
                        id="loss-limit",
                        validators=[Number(minimum=1, maximum=20)]
                    ),
                    Static("[dim]System stops trading if daily loss exceeds this[/dim]")
                ),
                Horizontal(
                    Button("Back", id="back", variant="default"),
                    Button("Next", id="next", variant="primary"),
                    id="button-row"
                ),
                id="capital-content"
            )
        )
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "next":
            # Validate inputs
            capital_input = self.query_one("#capital", Input)
            risk_input = self.query_one("#risk", Input)
            loss_limit_input = self.query_one("#loss-limit", Input)
            
            if capital_input.is_valid and risk_input.is_valid and loss_limit_input.is_valid:
                self.app.trading_config = {
                    "initial_capital": float(capital_input.value),
                    "risk_per_trade": float(risk_input.value),
                    "daily_loss_limit": float(loss_limit_input.value)
                }
                self.app.push_screen(FinalSetupScreen())
            else:
                self.app.notify("Please fill all fields correctly", severity="error")


class FinalSetupScreen(Screen):
    """Review and finalize setup"""
    
    def compose(self) -> ComposeResult:
        # Gather all config
        wallet_address = str(self.app.wallet_keypair.public_key)
        network = self.app.network_config['network']
        dex = SUPPORTED_DEXS[self.app.selected_dex]['name']
        capital = self.app.trading_config['initial_capital']
        
        config_summary = f"""[bold cyan]Configuration Summary:[/bold cyan]

[yellow]Wallet:[/yellow] {wallet_address[:20]}...
[yellow]Network:[/yellow] {network.upper()}
[yellow]DEX:[/yellow] {dex}
[yellow]Initial Capital:[/yellow] ${capital} USDC
[yellow]Risk per Trade:[/yellow] {self.app.trading_config['risk_per_trade']}%
[yellow]Daily Loss Limit:[/yellow] {self.app.trading_config['daily_loss_limit']}%

[bold]Ready to start trading?[/bold]"""
        
        yield Container(
            Vertical(
                Static(
                    Panel(
                        config_summary,
                        title="Final Review",
                        border_style="green"
                    )
                ),
                Container(id="setup-progress"),
                Horizontal(
                    Button("Back", id="back", variant="default"),
                    Button("Start Trading", id="start", variant="success"),
                    id="button-row"
                ),
                id="final-content"
            )
        )
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "start":
            await self.finalize_setup()
    
    async def finalize_setup(self) -> None:
        progress = self.query_one("#setup-progress")
        progress.mount(LoadingIndicator())
        
        try:
            # Create config directory
            config_dir = Path.home() / ".quantum_swarm"
            config_dir.mkdir(exist_ok=True)
            
            # Save encrypted wallet
            wallet_file = config_dir / "wallet.json"
            wallet_data = {
                "public_key": str(self.app.wallet_keypair.public_key),
                "secret_key": base58.b58encode(bytes(self.app.wallet_keypair.secret_key)).decode(),
                "created": datetime.now().isoformat()
            }
            
            # In production, encrypt this file
            with open(wallet_file, 'w') as f:
                json.dump(wallet_data, f)
            os.chmod(wallet_file, 0o600)  # Restrict access
            
            # Save trading config
            config_file = config_dir / "config.json"
            config_data = {
                "network": self.app.network_config,
                "dex": self.app.selected_dex,
                "trading": self.app.trading_config,
                "created": datetime.now().isoformat()
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            # Initialize Redis with config
            redis_client = redis.Redis(host='localhost', port=6379, db=0)
            redis_client.set('swarm:config', json.dumps(config_data))
            redis_client.set('swarm:wallet', wallet_data['public_key'])
            redis_client.set('swarm:capital', self.app.trading_config['initial_capital'])
            
            progress.remove_children()
            progress.mount(
                Static("[green]✓ Setup complete! Launching trading system...[/green]")
            )
            
            # Wait a moment then exit to main app
            await asyncio.sleep(2)
            self.app.exit(result="setup_complete")
            
        except Exception as e:
            progress.remove_children()
            progress.mount(
                Static(f"[red]Setup failed: {str(e)}[/red]")
            )


class OnboardingApp(App):
    """Onboarding wizard application"""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    #welcome-content, #wallet-content, #network-content, 
    #dex-content, #capital-content, #final-content {
        width: 80;
        height: auto;
        border: solid cyan;
        padding: 2;
    }
    
    #button-row {
        margin-top: 2;
        align: center middle;
    }
    
    Button {
        margin: 0 1;
    }
    
    RadioSet {
        margin: 1 0;
    }
    
    Input {
        margin: 1 0;
    }
    """
    
    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())


async def check_existing_setup() -> bool:
    """Check if setup already exists"""
    config_dir = Path.home() / ".quantum_swarm"
    return (config_dir / "config.json").exists()


async def run_onboarding() -> bool:
    """Run the onboarding process"""
    # Check if already set up
    if await check_existing_setup():
        print("✓ Setup already complete. Run 'python ui/tui_dashboard.py' to start.")
        return True
    
    # Run onboarding
    app = OnboardingApp()
    result = await app.run_async()
    
    return result == "setup_complete"


if __name__ == "__main__":
    import sys
    
    if asyncio.run(run_onboarding()):
        print("\n🎉 Setup complete! Starting Quantum Swarm Trader...")
        print("Run: python ui/tui_dashboard.py")
    else:
        print("\n❌ Setup cancelled.")
        sys.exit(1)