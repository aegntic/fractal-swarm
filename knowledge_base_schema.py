"""
Knowledge Base Schema for Strategy Evolution Tracking
Provides comprehensive documentation structure for all strategy parameters,
mutations, and performance metrics across multiple timeframes and assets
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import uuid
import os

class Timeframe(Enum):
    """Supported timeframes for analysis"""
    ONE_MIN = "1m"
    FIVE_MIN = "5m"
    FIFTEEN_MIN = "15m"
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"
    SIX_HOUR = "6h"
    TWELVE_HOUR = "12h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1M"
    
    @property
    def minutes(self):
        """Convert timeframe to minutes"""
        mapping = {
            "1m": 1, "5m": 5, "15m": 15, "1h": 60,
            "4h": 240, "6h": 360, "12h": 720,
            "1d": 1440, "1w": 10080, "1M": 43200
        }
        return mapping[self.value]

@dataclass
class AssetInfo:
    """Information about a trading asset"""
    symbol: str
    name: str
    network: str
    category: str  # 'major', 'solana_token', 'defi', etc.
    market_cap_rank: Optional[int] = None
    contract_address: Optional[str] = None
    decimals: Optional[int] = None
    
@dataclass
class StrategyGenome:
    """Complete genetic makeup of a strategy"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    
    # Multi-timeframe parameters
    timeframe_weights: Dict[str, float] = field(default_factory=dict)
    
    # Technical indicators per timeframe
    indicators: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Trading parameters
    risk_params: Dict[str, float] = field(default_factory=dict)
    entry_conditions: Dict[str, Any] = field(default_factory=dict)
    exit_conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Confluence requirements
    min_timeframe_alignment: int = 3
    confluence_threshold: float = 0.7
    
    # Asset preferences
    preferred_assets: List[str] = field(default_factory=list)
    asset_correlations: Dict[str, float] = field(default_factory=dict)
    
    # Mutation history
    mutations: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self):
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'name': self.name,
            'generation': self.generation,
            'parent_ids': self.parent_ids,
            'timeframe_weights': self.timeframe_weights,
            'indicators': self.indicators,
            'risk_params': self.risk_params,
            'entry_conditions': self.entry_conditions,
            'exit_conditions': self.exit_conditions,
            'min_timeframe_alignment': self.min_timeframe_alignment,
            'confluence_threshold': self.confluence_threshold,
            'preferred_assets': self.preferred_assets,
            'asset_correlations': self.asset_correlations,
            'mutations': self.mutations
        }

@dataclass
class TimeframeAnalysis:
    """Analysis results for a specific timeframe"""
    timeframe: Timeframe
    timestamp: datetime
    
    # Price action
    trend_direction: str  # 'bullish', 'bearish', 'neutral'
    trend_strength: float  # 0-1
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    
    # Technical indicators
    rsi: Optional[float] = None
    macd_signal: Optional[str] = None
    moving_averages: Dict[int, float] = field(default_factory=dict)
    volume_profile: Dict[str, float] = field(default_factory=dict)
    
    # Pattern recognition
    patterns_detected: List[str] = field(default_factory=list)
    pattern_confidence: Dict[str, float] = field(default_factory=dict)

@dataclass
class ConfluenceSignal:
    """Multi-timeframe confluence analysis result"""
    timestamp: datetime
    asset: str
    signal_type: str  # 'buy', 'sell', 'hold'
    overall_confidence: float
    
    # Timeframe alignments
    aligned_timeframes: List[Timeframe] = field(default_factory=list)
    timeframe_signals: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Confluence factors
    price_action_score: float = 0.0
    indicator_alignment_score: float = 0.0
    volume_confirmation_score: float = 0.0
    pattern_confluence_score: float = 0.0
    
    # Risk metrics
    risk_reward_ratio: float = 0.0
    suggested_stop_loss: Optional[float] = None
    suggested_take_profit: Optional[float] = None

@dataclass
class TradeExecution:
    """Detailed trade execution record"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    strategy_id: str = ""
    asset: str = ""
    
    # Execution details
    entry_time: datetime = field(default_factory=datetime.now)
    entry_price: float = 0.0
    position_size: float = 0.0
    direction: str = ""  # 'long' or 'short'
    
    # Confluence at entry
    confluence_signal: Optional[ConfluenceSignal] = None
    timeframe_analysis: Dict[str, TimeframeAnalysis] = field(default_factory=dict)
    
    # Exit details
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    
    # Performance
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None
    max_drawdown: Optional[float] = None
    time_in_position: Optional[int] = None  # minutes

@dataclass
class StrategyPerformance:
    """Comprehensive performance metrics for a strategy"""
    strategy_id: str
    evaluation_period: Dict[str, datetime]  # 'start', 'end'
    
    # Overall metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # Returns
    total_return: float = 0.0
    average_return_per_trade: float = 0.0
    best_trade_return: float = 0.0
    worst_trade_return: float = 0.0
    
    # Risk metrics
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    var_95: float = 0.0  # Value at Risk
    
    # Timeframe performance
    performance_by_timeframe: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Asset performance
    performance_by_asset: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Market condition performance
    performance_by_market_condition: Dict[str, Dict[str, float]] = field(default_factory=dict)

@dataclass
class GenerationSummary:
    """Summary of a complete generation of strategies"""
    generation_number: int
    timestamp: datetime
    
    # Population stats
    population_size: int = 0
    strategies: List[StrategyGenome] = field(default_factory=list)
    
    # Performance distribution
    avg_sharpe_ratio: float = 0.0
    best_sharpe_ratio: float = 0.0
    avg_return: float = 0.0
    best_return: float = 0.0
    
    # Evolution metrics
    mutation_rate: float = 0.0
    crossover_rate: float = 0.0
    selection_pressure: float = 0.0
    
    # Market conditions during generation
    market_regime: str = ""  # 'bull', 'bear', 'sideways'
    volatility_level: str = ""  # 'low', 'medium', 'high'
    major_events: List[str] = field(default_factory=list)

class KnowledgeBase:
    """Central knowledge base for all strategy evolution data"""
    
    def __init__(self, base_path: str = "/home/tabs/crypto-swarm-trader/knowledge_base"):
        self.base_path = base_path
        self.ensure_directories()
        
    def ensure_directories(self):
        """Create necessary directory structure"""
        import os
        directories = [
            'strategies',
            'generations',
            'trades',
            'performance',
            'market_data',
            'confluence_signals',
            'assets'
        ]
        
        for dir_name in directories:
            os.makedirs(os.path.join(self.base_path, dir_name), exist_ok=True)
    
    def save_strategy(self, strategy: StrategyGenome):
        """Save strategy genome to knowledge base"""
        path = os.path.join(self.base_path, 'strategies', f'{strategy.id}.json')
        with open(path, 'w') as f:
            json.dump(strategy.to_dict(), f, indent=2, default=str)
    
    def save_generation(self, summary: GenerationSummary):
        """Save generation summary"""
        path = os.path.join(self.base_path, 'generations', f'gen_{summary.generation_number}.json')
        with open(path, 'w') as f:
            json.dump({
                'generation_number': summary.generation_number,
                'timestamp': summary.timestamp.isoformat(),
                'population_size': summary.population_size,
                'avg_sharpe_ratio': summary.avg_sharpe_ratio,
                'best_sharpe_ratio': summary.best_sharpe_ratio,
                'avg_return': summary.avg_return,
                'best_return': summary.best_return,
                'mutation_rate': summary.mutation_rate,
                'crossover_rate': summary.crossover_rate,
                'selection_pressure': summary.selection_pressure,
                'market_regime': summary.market_regime,
                'volatility_level': summary.volatility_level,
                'major_events': summary.major_events,
                'strategy_ids': [s.id for s in summary.strategies]
            }, f, indent=2)
    
    def save_trade(self, trade: TradeExecution):
        """Save trade execution details"""
        path = os.path.join(self.base_path, 'trades', f'{trade.id}.json')
        with open(path, 'w') as f:
            trade_dict = {
                'id': trade.id,
                'strategy_id': trade.strategy_id,
                'asset': trade.asset,
                'entry_time': trade.entry_time.isoformat(),
                'entry_price': trade.entry_price,
                'position_size': trade.position_size,
                'direction': trade.direction,
                'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
                'exit_price': trade.exit_price,
                'exit_reason': trade.exit_reason,
                'pnl': trade.pnl,
                'pnl_percentage': trade.pnl_percentage,
                'max_drawdown': trade.max_drawdown,
                'time_in_position': trade.time_in_position
            }
            json.dump(trade_dict, f, indent=2)
    
    def query_strategies(self, filters: Dict[str, Any]) -> List[StrategyGenome]:
        """Query strategies based on filters"""
        # Implementation would load and filter strategies
        pass
    
    def get_performance_rankings(self, metric: str = 'sharpe_ratio') -> List[Dict[str, Any]]:
        """Get strategies ranked by performance metric"""
        # Implementation would load and rank strategies
        pass