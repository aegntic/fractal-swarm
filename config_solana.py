"""
Solana-specific configuration for Quantum Swarm Trader
Includes Solana Agent Kit integration and MegaETH cross-chain support
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class SolanaConfig:
    """Solana blockchain and DeFi configuration"""
    
    # RPC Endpoints
    mainnet_rpc: str = os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')
    devnet_rpc: str = os.getenv('SOLANA_DEVNET_URL', 'https://api.devnet.solana.com')
    
    # Private key for main wallet (Base58 encoded)
    private_key: str = os.getenv('SOLANA_PRIVATE_KEY', '')
    
    # Solana Programs
    programs = {
        # DEX Aggregators
        "jupiter": "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB",
        
        # DEXs
        "raydium": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
        "orca_whirlpool": "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
        "serum": "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin",
        
        # Lending
        "solend": "So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
        "marginfi": "MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA",
        "kamino": "KAMINOxHnWbmXG3JMUJcxEUeHFHh5DREAqPBVvvVxSc",
        
        # Staking
        "marinade": "MarBmsSgKXdrN1egZf5sqe1TMai9K1rChYNDJgjq7aD",
        "jito": "Jito4APyf642JPZPx3hGc6WWJ8zPKtRbRs4P815Awbb",
        
        # Oracles
        "pyth": "FsJ3A3u2vn5cTVofAjvy6y5kwABJAqYWpe4975bi2epH",
        "switchboard": "SW1TCH7qEPTdLsDHRgPuMQjbQxKdH2aBStViMFnt64f",
        
        # NFT
        "metaplex": "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s",
        "magic_eden": "MEisE1HzehtrDpAAT8PnLHjpSSkRYakotTuJRPjTpo8",
        
        # Other
        "pump_fun": "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
        "drift": "dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH",
        "zeta": "ZETAxsqBRek56DhiGXrn75yj2NHU3aYUnxvHXpkf3aD",
    }
    
    # Token addresses
    tokens = {
        "SOL": "So11111111111111111111111111111111111111112",
        "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
        "SRM": "SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt",
        "ORCA": "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE",
        "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
        "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        "WIF": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
    }
    
    # MEV and trading configuration
    mev_config = {
        "jito_block_engine": "https://block-engine.jito.wtf",
        "jito_tip_account": "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",
        "priority_fee_percentile": 90,  # Use 90th percentile for priority fees
        "max_priority_fee_lamports": 100000,  # Max 0.0001 SOL priority fee
        "sandwich_min_profit_bps": 30,  # 0.3% minimum profit
    }
    
    # Fractal clone configuration
    clone_config = {
        "max_clones_per_rpc": 10,  # Max clones per RPC endpoint
        "clone_wallet_derivation_path": "m/44'/501'/0'/0'",  # BIP44 path
        "clone_behavioral_variance": 0.15,  # 15% behavioral variance
        "clone_specializations": [
            "jupiter_arbitrage",
            "raydium_liquidity",
            "pump_fun_sniper",
            "jito_mev_hunter",
            "lending_optimizer",
        ]
    }

@dataclass
class MegaETHConfig:
    """MegaETH real-time blockchain configuration"""
    
    # Network configuration
    rpc_url: str = os.getenv('MEGAETH_RPC_URL', 'https://rpc.megaeth.com')
    chain_id: int = 69420  # Update when mainnet launches
    
    # Expected capabilities (based on "real-time blockchain" claim)
    expected_features = {
        "block_time_ms": 100,  # Sub-second blocks
        "tps_capacity": 100000,  # High throughput
        "finality_ms": 1000,  # Near-instant finality
        "mev_protection": True,  # Built-in MEV protection expected
    }
    
    # Cross-chain bridge configuration
    bridge_config = {
        "wormhole_bridge": "0x3ee18B2214AFF97000D974cf647E7C347E8fa585",
        "supported_chains": ["ethereum", "solana", "arbitrum", "optimism"],
        "min_bridge_amount_usd": 100,
        "max_slippage_bps": 50,  # 0.5% max slippage
    }

@dataclass
class CrossChainConfig:
    """Configuration for cross-chain operations"""
    
    # Supported chains for arbitrage
    chains = {
        "solana": {
            "rpc": os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com'),
            "chain_id": "solana-mainnet",
            "block_time": 0.4,  # 400ms
            "native_token": "SOL",
        },
        "ethereum": {
            "rpc": os.getenv('ETH_RPC_URL', 'https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY'),
            "chain_id": 1,
            "block_time": 12,
            "native_token": "ETH",
        },
        "megaeth": {
            "rpc": os.getenv('MEGAETH_RPC_URL', 'https://rpc.megaeth.com'),
            "chain_id": 69420,
            "block_time": 0.1,  # 100ms claimed
            "native_token": "MEGA",
        },
        "arbitrum": {
            "rpc": os.getenv('ARB_RPC_URL', 'https://arb1.arbitrum.io/rpc'),
            "chain_id": 42161,
            "block_time": 0.25,
            "native_token": "ETH",
        },
        "optimism": {
            "rpc": os.getenv('OP_RPC_URL', 'https://mainnet.optimism.io'),
            "chain_id": 10,
            "block_time": 2,
            "native_token": "ETH",
        },
    }
    
    # Cross-chain arbitrage parameters
    arbitrage_config = {
        "min_profit_bps": 50,  # 0.5% minimum profit
        "max_execution_time_ms": 5000,  # 5 second max
        "confidence_threshold": 0.95,  # 95% price confidence
        "gas_buffer_multiplier": 1.2,  # 20% gas buffer
    }

# Singleton instances
solana_config = SolanaConfig()
megaeth_config = MegaETHConfig()
crosschain_config = CrossChainConfig()

# API Keys for various services
API_KEYS = {
    "openai": os.getenv('OPENAI_API_KEY', ''),  # For Solana Agent Kit
    "coingecko": os.getenv('COINGECKO_API_KEY', ''),
    "birdeye": os.getenv('BIRDEYE_API_KEY', ''),
    "helius": os.getenv('HELIUS_API_KEY', ''),
    "quicknode": os.getenv('QUICKNODE_API_KEY', ''),
}

# Redis configuration for swarm coordination
REDIS_CONFIG = {
    "host": os.getenv('REDIS_HOST', 'localhost'),
    "port": int(os.getenv('REDIS_PORT', 6379)),
    "db": int(os.getenv('REDIS_DB', 0)),
    "decode_responses": True,
}

# Clone spawning thresholds
CLONE_THRESHOLDS = {
    "generation_0": 500,    # $500 to spawn first clone
    "generation_1": 2000,   # $2000 for gen 1 clones
    "generation_2": 5000,   # $5000 for gen 2 clones
    "generation_3": 10000,  # $10000 for gen 3 clones
    "max_generations": 5,   # Maximum clone depth
}