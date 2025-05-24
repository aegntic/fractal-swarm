"""
Crypto Swarm Trader Configuration
This defines the multi-phase strategy for growing $100 to $100,000
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Any
from enum import Enum

class TradingPhase(Enum):
    MICRO = "micro"  # $100 - $1,000
    GROWTH = "growth"  # $1,000 - $10,000
    SCALE = "scale"  # $10,000 - $100,000

@dataclass
class SwarmConfig:
    # Initial settings
    initial_capital: float = 100.0
    target_capital: float = 100000.0
    
    # Phase thresholds
    phase_thresholds = {
        TradingPhase.MICRO: (100, 1000),
        TradingPhase.GROWTH: (1000, 10000),
        TradingPhase.SCALE: (10000, 100000)
    }
    
    # Agent configuration
    agent_counts = {
        "scout": 5,
        "analyst": 3,
        "trader": 4,
        "risk_manager": 2,
        "arbitrage": 3,
        "mev": 2,
        "sentiment": 2
    }    
    # Strategy weights by phase
    strategy_weights = {
        TradingPhase.MICRO: {
            "mev_opportunities": 0.3,
            "micro_arbitrage": 0.25,
            "momentum_scalping": 0.2,
            "liquidity_provision": 0.15,
            "social_signals": 0.1
        },
        TradingPhase.GROWTH: {
            "cross_exchange_arbitrage": 0.25,
            "trend_following": 0.2,
            "defi_yield": 0.2,
            "options_strategies": 0.15,
            "whale_following": 0.1,
            "news_trading": 0.1
        },
        TradingPhase.SCALE: {
            "portfolio_optimization": 0.25,
            "market_making": 0.2,
            "yield_farming": 0.2,
            "derivatives_hedging": 0.15,
            "cross_chain_arbitrage": 0.1,
            "venture_positions": 0.1
        }
    }    
    # Risk parameters by phase
    risk_params = {
        TradingPhase.MICRO: {
            "max_position_size": 0.2,  # 20% of capital
            "stop_loss": 0.05,  # 5% stop loss
            "max_daily_drawdown": 0.15,  # 15% daily max loss
            "leverage_limit": 3.0
        },
        TradingPhase.GROWTH: {
            "max_position_size": 0.15,
            "stop_loss": 0.03,
            "max_daily_drawdown": 0.10,
            "leverage_limit": 2.0
        },
        TradingPhase.SCALE: {
            "max_position_size": 0.10,
            "stop_loss": 0.02,
            "max_daily_drawdown": 0.05,
            "leverage_limit": 1.5
        }
    }
    
    # Exchange configuration
    exchanges = {
        "spot": ["binance", "coinbase", "kraken", "kucoin", "gate"],
        "derivatives": ["binance_futures", "dydx", "gmx"],
        "dex": ["uniswap", "sushiswap", "curve", "balancer", "pancakeswap"]
    }    
    # Data sources
    data_sources = {
        "on_chain": [
            "etherscan", "bscscan", "polygonscan", "arbiscan",
            "dune_analytics", "nansen", "glassnode"
        ],
        "social": [
            "twitter", "reddit", "discord", "telegram",
            "stocktwits", "tradingview"
        ],
        "news": [
            "coindesk", "cointelegraph", "decrypt", "theblock",
            "bloomberg_crypto", "reuters_crypto"
        ],
        "technical": [
            "tradingview", "coingecko", "coinmarketcap",
            "messari", "santiment"
        ]
    }
    
    # MEV and advanced strategies
    mev_config = {
        "flashloan_providers": ["aave", "dydx", "euler"],
        "sandwich_threshold": 0.003,  # 0.3% profit minimum
        "frontrun_gas_multiplier": 1.2,
        "backrun_delay_blocks": 1
    }    
    # Machine learning models
    ml_models = {
        "price_prediction": "lstm_ensemble",
        "sentiment_analysis": "transformer_bert",
        "pattern_recognition": "cnn_resnet",
        "anomaly_detection": "isolation_forest",
        "portfolio_optimization": "reinforcement_learning"
    }
    
    # Communication and coordination
    swarm_communication = {
        "consensus_threshold": 0.6,  # 60% agent agreement
        "update_frequency": 5,  # seconds
        "heartbeat_timeout": 30,  # seconds
        "message_broker": "redis",
        "coordination_protocol": "raft"
    }

# Singleton config instance
config = SwarmConfig()