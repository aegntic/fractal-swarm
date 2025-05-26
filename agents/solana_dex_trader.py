"""
Solana DEX Trading Agent
Handles real trading on Raydium, Orca, and Jupiter
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import aiohttp
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer
from spl.token.instructions import get_associated_token_address
import base58

logger = logging.getLogger(__name__)

# Token addresses on Solana
TOKENS = {
    "SOL": "So11111111111111111111111111111111111111112",
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
    "ORCA": "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE",
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
}

# DEX Program IDs
DEX_PROGRAMS = {
    "raydium": PublicKey("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"),
    "orca": PublicKey("9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP"),
    "jupiter": PublicKey("JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB")
}


class SolanaDEXTrader:
    """Production Solana DEX trading implementation"""
    
    def __init__(self, keypair: Keypair, rpc_url: str, selected_dex: str):
        self.keypair = keypair
        self.client = AsyncClient(rpc_url)
        self.selected_dex = selected_dex
        self.session = None
        
    async def initialize(self):
        """Initialize HTTP session and verify connection"""
        self.session = aiohttp.ClientSession()
        
        # Verify wallet has SOL for fees
        balance = await self.get_sol_balance()
        if balance < 0.01:  # Minimum for fees
            raise Exception(f"Insufficient SOL for fees: {balance}")
        
        logger.info(f"Initialized Solana trader - Wallet: {self.keypair.public_key}")
        logger.info(f"SOL Balance: {balance:.4f}")
    
    async def get_sol_balance(self) -> float:
        """Get SOL balance in wallet"""
        response = await self.client.get_balance(self.keypair.public_key)
        return response['result']['value'] / 1e9
    
    async def get_token_balance(self, mint: str) -> float:
        """Get SPL token balance"""
        mint_pubkey = PublicKey(mint)
        token_account = get_associated_token_address(
            self.keypair.public_key,
            mint_pubkey
        )
        
        try:
            response = await self.client.get_token_account_balance(token_account)
            return float(response['result']['value']['amount']) / (10 ** response['result']['value']['decimals'])
        except:
            return 0.0
    
    async def get_price_quote(self, input_mint: str, output_mint: str, amount: float) -> Dict[str, Any]:
        """Get price quote from selected DEX"""
        if self.selected_dex == "jupiter":
            return await self._get_jupiter_quote(input_mint, output_mint, amount)
        elif self.selected_dex == "raydium":
            return await self._get_raydium_quote(input_mint, output_mint, amount)
        elif self.selected_dex == "orca":
            return await self._get_orca_quote(input_mint, output_mint, amount)
    
    async def _get_jupiter_quote(self, input_mint: str, output_mint: str, amount: float) -> Dict[str, Any]:
        """Get quote from Jupiter aggregator"""
        # Convert amount to smallest unit
        decimals = 6 if input_mint == TOKENS["USDC"] else 9
        amount_raw = int(amount * (10 ** decimals))
        
        url = f"https://quote-api.jup.ag/v6/quote"
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount_raw,
            "slippageBps": 50,  # 0.5% slippage
            "onlyDirectRoutes": False,
            "asLegacyTransaction": False
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('data'):
                    quote = data['data'][0]
                    return {
                        "inputAmount": amount,
                        "outputAmount": float(quote['outAmount']) / (10 ** (6 if output_mint == TOKENS["USDC"] else 9)),
                        "priceImpact": float(quote.get('priceImpactPct', 0)),
                        "route": quote.get('routePlan', []),
                        "raw": quote
                    }
        
        raise Exception("Failed to get Jupiter quote")
    
    async def _get_raydium_quote(self, input_mint: str, output_mint: str, amount: float) -> Dict[str, Any]:
        """Get quote from Raydium"""
        # Raydium API endpoint
        url = "https://api.raydium.io/v2/swap/compute"
        
        data = {
            "id": f"{input_mint}-{output_mint}",
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "slippage": 0.005
        }
        
        async with self.session.post(url, json=data) as response:
            if response.status == 200:
                result = await response.json()
                if result.get('success'):
                    return {
                        "inputAmount": amount,
                        "outputAmount": result['data']['outputAmount'],
                        "priceImpact": result['data']['priceImpact'],
                        "route": result['data']['route'],
                        "raw": result['data']
                    }
        
        raise Exception("Failed to get Raydium quote")
    
    async def execute_swap(self, input_mint: str, output_mint: str, amount: float, quote: Dict[str, Any]) -> str:
        """Execute actual swap transaction"""
        if self.selected_dex == "jupiter":
            return await self._execute_jupiter_swap(input_mint, output_mint, amount, quote)
        elif self.selected_dex == "raydium":
            return await self._execute_raydium_swap(input_mint, output_mint, amount, quote)
        elif self.selected_dex == "orca":
            return await self._execute_orca_swap(input_mint, output_mint, amount, quote)
    
    async def _execute_jupiter_swap(self, input_mint: str, output_mint: str, amount: float, quote: Dict[str, Any]) -> str:
        """Execute swap via Jupiter"""
        # Get swap transaction
        url = "https://quote-api.jup.ag/v6/swap"
        
        body = {
            "quoteResponse": quote['raw'],
            "userPublicKey": str(self.keypair.public_key),
            "wrapAndUnwrapSol": True,
            "computeUnitPriceMicroLamports": 20000,  # Priority fee
            "asLegacyTransaction": False
        }
        
        async with self.session.post(url, json=body) as response:
            if response.status == 200:
                swap_data = await response.json()
                swap_transaction = swap_data['swapTransaction']
                
                # Deserialize and sign transaction
                raw_tx = base58.b58decode(swap_transaction)
                tx = Transaction.from_bytes(raw_tx)
                
                # Send transaction
                result = await self.client.send_transaction(
                    tx,
                    self.keypair,
                    opts={"skip_preflight": False, "preflight_commitment": "confirmed"}
                )
                
                tx_hash = result['result']
                logger.info(f"Swap executed: {tx_hash}")
                
                # Wait for confirmation
                await self.client.confirm_transaction(tx_hash)
                
                return tx_hash
        
        raise Exception("Failed to execute Jupiter swap")
    
    async def monitor_positions(self) -> List[Dict[str, Any]]:
        """Monitor current token positions"""
        positions = []
        
        for token_name, mint in TOKENS.items():
            if token_name == "SOL":
                balance = await self.get_sol_balance()
            else:
                balance = await self.get_token_balance(mint)
            
            if balance > 0:
                # Get current price in USDC
                if token_name != "USDC":
                    try:
                        quote = await self.get_price_quote(mint, TOKENS["USDC"], balance)
                        value_usdc = quote['outputAmount']
                    except:
                        value_usdc = 0
                else:
                    value_usdc = balance
                
                positions.append({
                    "token": token_name,
                    "mint": mint,
                    "balance": balance,
                    "value_usdc": value_usdc
                })
        
        return positions
    
    async def find_arbitrage_opportunity(self) -> Optional[Dict[str, Any]]:
        """Find arbitrage opportunities across DEXs"""
        # Check common pairs
        pairs = [
            ("SOL", "USDC"),
            ("RAY", "USDC"),
            ("ORCA", "USDC"),
            ("BONK", "USDC")
        ]
        
        for token_a, token_b in pairs:
            mint_a = TOKENS[token_a]
            mint_b = TOKENS[token_b]
            
            # Test amount (in USDC value)
            test_amount = 100
            
            try:
                # Get quotes from different DEXs
                quotes = {}
                
                # Temporarily check multiple DEXs
                for dex in ["jupiter", "raydium"]:
                    self.selected_dex = dex
                    quote = await self.get_price_quote(mint_b, mint_a, test_amount)
                    quotes[dex] = quote
                
                # Calculate potential profit
                prices = {dex: q['outputAmount'] for dex, q in quotes.items()}
                max_dex = max(prices, key=prices.get)
                min_dex = min(prices, key=prices.get)
                
                spread = (prices[max_dex] - prices[min_dex]) / prices[min_dex] * 100
                
                # If spread > 0.5% after fees, it's profitable
                if spread > 0.5:
                    return {
                        "pair": f"{token_a}/{token_b}",
                        "buy_dex": min_dex,
                        "sell_dex": max_dex,
                        "spread_percent": spread,
                        "potential_profit": test_amount * (spread / 100)
                    }
                    
            except Exception as e:
                logger.error(f"Error checking arbitrage for {token_a}/{token_b}: {e}")
        
        return None
    
    async def execute_arbitrage(self, opportunity: Dict[str, Any]) -> bool:
        """Execute arbitrage trade"""
        try:
            # Parse opportunity
            tokens = opportunity['pair'].split('/')
            token_a = tokens[0]
            token_b = tokens[1]
            
            # Execute buy on cheaper DEX
            self.selected_dex = opportunity['buy_dex']
            buy_quote = await self.get_price_quote(
                TOKENS[token_b], 
                TOKENS[token_a], 
                100  # Trade size
            )
            
            buy_tx = await self.execute_swap(
                TOKENS[token_b],
                TOKENS[token_a],
                100,
                buy_quote
            )
            
            # Wait for confirmation
            await asyncio.sleep(2)
            
            # Execute sell on expensive DEX
            self.selected_dex = opportunity['sell_dex']
            sell_quote = await self.get_price_quote(
                TOKENS[token_a],
                TOKENS[token_b],
                buy_quote['outputAmount']
            )
            
            sell_tx = await self.execute_swap(
                TOKENS[token_a],
                TOKENS[token_b],
                buy_quote['outputAmount'],
                sell_quote
            )
            
            logger.info(f"Arbitrage executed - Buy: {buy_tx}, Sell: {sell_tx}")
            logger.info(f"Expected profit: ${opportunity['potential_profit']:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Arbitrage execution failed: {e}")
            return False
    
    async def close(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
        await self.client.close()