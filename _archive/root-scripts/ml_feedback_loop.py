"""
Machine Learning Feedback Loop System for Quantum Swarm Trader
Enables exponential learning of coin potential and parallel value extraction
"""

import asyncio
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import redis.asyncio as redis
from collections import deque
import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from concurrent.futures import ProcessPoolExecutor
import aiohttp
from web3 import Web3
import ccxt.async_support as ccxt
from social_intelligence_analyzer_puppeteer import PuppeteerSocialAnalyzer, SocialMetrics

logger = logging.getLogger(__name__)

@dataclass
class MarketSignal:
    """Real-time market signal data"""
    coin_id: str
    timestamp: datetime
    price: float
    volume_24h: float
    market_cap: float
    price_change_1h: float
    price_change_24h: float
    price_change_7d: float
    social_sentiment: float
    whale_activity: float
    dex_liquidity: float
    github_activity: float
    on_chain_metrics: Dict[str, float]
    technical_indicators: Dict[str, float]
    social_metrics: Optional[SocialMetrics] = None

@dataclass
class TradingOutcome:
    """Result of a trading decision"""
    coin_id: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    position_size: float
    profit_loss: float
    profit_percentage: float
    strategy_used: str
    market_conditions: Dict[str, float]
    clone_id: str

@dataclass
class CoinPotential:
    """Predicted potential for a coin"""
    coin_id: str
    short_term_potential: float  # 1-24 hours
    medium_term_potential: float  # 1-7 days
    long_term_potential: float  # 7-30 days
    volatility_score: float
    risk_adjusted_return: float
    optimal_position_size: float
    confidence_score: float
    predicted_price_targets: List[float]
    stop_loss_levels: List[float]

class CoinPotentialPredictor(nn.Module):
    """Neural network for predicting coin potential"""
    
    def __init__(self, input_features: int = 70, hidden_layers: List[int] = [256, 128, 64]):
        super().__init__()
        self.layers = nn.ModuleList()
        
        # Build dynamic architecture
        prev_size = input_features
        for hidden_size in hidden_layers:
            self.layers.append(nn.Linear(prev_size, hidden_size))
            self.layers.append(nn.BatchNorm1d(hidden_size))
            self.layers.append(nn.ReLU())
            self.layers.append(nn.Dropout(0.3))
            prev_size = hidden_size
        
        # Output layers for different predictions
        self.short_term_head = nn.Linear(prev_size, 1)
        self.medium_term_head = nn.Linear(prev_size, 1)
        self.long_term_head = nn.Linear(prev_size, 1)
        self.volatility_head = nn.Linear(prev_size, 1)
        self.confidence_head = nn.Linear(prev_size, 1)
        
    def forward(self, x):
        # Pass through hidden layers
        for layer in self.layers:
            x = layer(x)
        
        # Generate predictions
        short_term = torch.sigmoid(self.short_term_head(x))
        medium_term = torch.sigmoid(self.medium_term_head(x))
        long_term = torch.sigmoid(self.long_term_head(x))
        volatility = torch.sigmoid(self.volatility_head(x))
        confidence = torch.sigmoid(self.confidence_head(x))
        
        return short_term, medium_term, long_term, volatility, confidence

class SwarmLearningOrchestrator:
    """Orchestrates distributed learning across swarm clones"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.model = CoinPotentialPredictor()
        self.optimizer = optim.AdamW(self.model.parameters(), lr=0.001)
        self.scaler = StandardScaler()
        self.experience_buffer = deque(maxlen=100000)
        self.performance_history = deque(maxlen=10000)
        
    async def initialize(self):
        """Initialize Redis connection and load existing model"""
        self.redis_client = await redis.from_url(self.redis_url)
        await self._load_shared_model()
        
    async def _load_shared_model(self):
        """Load model weights from Redis shared storage"""
        try:
            model_data = await self.redis_client.get("swarm:ml:model_weights")
            if model_data:
                weights = torch.load(json.loads(model_data))
                self.model.load_state_dict(weights)
                logger.info("Loaded shared model from Redis")
        except Exception as e:
            logger.warning(f"Could not load shared model: {e}")
    
    async def _save_shared_model(self):
        """Save model weights to Redis for swarm sharing"""
        try:
            model_data = json.dumps({
                'state_dict': self.model.state_dict(),
                'timestamp': datetime.utcnow().isoformat()
            })
            await self.redis_client.set("swarm:ml:model_weights", model_data)
            await self.redis_client.expire("swarm:ml:model_weights", 3600)  # 1 hour TTL
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    async def collect_swarm_experiences(self):
        """Aggregate learning experiences from all clones"""
        experiences = []
        clone_keys = await self.redis_client.keys("swarm:clone:*:experience")
        
        for key in clone_keys:
            try:
                exp_data = await self.redis_client.get(key)
                if exp_data:
                    experiences.extend(json.loads(exp_data))
            except Exception as e:
                logger.error(f"Failed to collect experience from {key}: {e}")
        
        # Add to local buffer
        self.experience_buffer.extend(experiences)
        return len(experiences)
    
    async def train_on_experiences(self, batch_size: int = 128):
        """Train model on collected experiences"""
        if len(self.experience_buffer) < batch_size:
            return
        
        # Sample batch
        batch_indices = np.random.choice(len(self.experience_buffer), batch_size)
        batch = [self.experience_buffer[i] for i in batch_indices]
        
        # Prepare training data
        X, y_short, y_medium, y_long = self._prepare_training_data(batch)
        
        # Convert to tensors
        X_tensor = torch.FloatTensor(X)
        y_short_tensor = torch.FloatTensor(y_short)
        y_medium_tensor = torch.FloatTensor(y_medium)
        y_long_tensor = torch.FloatTensor(y_long)
        
        # Forward pass
        pred_short, pred_medium, pred_long, _, _ = self.model(X_tensor)
        
        # Calculate losses
        loss_short = nn.MSELoss()(pred_short.squeeze(), y_short_tensor)
        loss_medium = nn.MSELoss()(pred_medium.squeeze(), y_medium_tensor)
        loss_long = nn.MSELoss()(pred_long.squeeze(), y_long_tensor)
        
        total_loss = loss_short + loss_medium + loss_long
        
        # Backward pass
        self.optimizer.zero_grad()
        total_loss.backward()
        self.optimizer.step()
        
        # Save updated model
        await self._save_shared_model()
        
        return total_loss.item()
    
    def _prepare_training_data(self, experiences: List[Dict]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Convert experiences to training data"""
        features = []
        targets_short = []
        targets_medium = []
        targets_long = []
        
        for exp in experiences:
            # Extract features
            feature_vec = self._extract_features(exp['market_signal'])
            features.append(feature_vec)
            
            # Calculate actual returns
            outcome = exp['outcome']
            profit_pct = outcome['profit_percentage']
            
            # Normalize to 0-1 range
            targets_short.append(min(max(profit_pct / 10, 0), 1))  # Cap at 10%
            targets_medium.append(min(max(profit_pct / 50, 0), 1))  # Cap at 50%
            targets_long.append(min(max(profit_pct / 100, 0), 1))  # Cap at 100%
        
        return np.array(features), np.array(targets_short), np.array(targets_medium), np.array(targets_long)
    
    def _extract_features(self, signal: Dict) -> np.ndarray:
        """Extract feature vector from market signal"""
        features = [
            signal.get('price', 0),
            signal.get('volume_24h', 0),
            signal.get('market_cap', 0),
            signal.get('price_change_1h', 0),
            signal.get('price_change_24h', 0),
            signal.get('price_change_7d', 0),
            signal.get('social_sentiment', 0),
            signal.get('whale_activity', 0),
            signal.get('dex_liquidity', 0),
            signal.get('github_activity', 0),
        ]
        
        # Add technical indicators
        tech_indicators = signal.get('technical_indicators', {})
        features.extend([
            tech_indicators.get('rsi', 50),
            tech_indicators.get('macd', 0),
            tech_indicators.get('bb_position', 0.5),
            tech_indicators.get('volume_ratio', 1),
        ])
        
        # Add on-chain metrics
        on_chain = signal.get('on_chain_metrics', {})
        features.extend([
            on_chain.get('active_addresses', 0),
            on_chain.get('transaction_volume', 0),
            on_chain.get('exchange_inflow', 0),
            on_chain.get('exchange_outflow', 0),
        ])
        
        # Add social intelligence metrics
        social_metrics = signal.get('social_metrics')
        if social_metrics and hasattr(social_metrics, '__dict__'):
            sm = social_metrics
            features.extend([
                sm.twitter_followers / 1000000,  # Normalize to millions
                sm.twitter_engagement_rate,
                sm.twitter_post_frequency / 100,  # Normalize
                float(sm.twitter_verified),
                sm.twitter_account_age_days / 365,  # Years
                sm.telegram_members / 100000,  # Normalize
                sm.telegram_online_ratio,
                sm.telegram_message_frequency / 100,
                float(sm.website_valid),
                float(sm.website_ssl),
                sm.website_age_days / 365,
                sm.github_stars / 1000,
                sm.github_commits_30d / 100,
                sm.reddit_subscribers / 10000,
                sm.overall_credibility_score,
                sm.bot_activity_score,
                sm.community_health_score,
                sm.risk_score,
            ])
        else:
            # Add zeros if no social metrics
            features.extend([0] * 18)
        
        # Pad to expected size
        while len(features) < 70:
            features.append(0)
        
        return np.array(features[:70])

class MLFeedbackLoop:
    """Main ML feedback loop system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.orchestrator = SwarmLearningOrchestrator(config.get('redis_url', 'redis://localhost:6379'))
        self.data_collector = MarketDataCollector(config)
        self.value_extractor = ParallelValueExtractor(config)
        self.performance_tracker = PerformanceTracker()
        self.is_running = False
        
    async def initialize(self):
        """Initialize all components"""
        await self.orchestrator.initialize()
        await self.data_collector.initialize()
        await self.value_extractor.initialize()
        logger.info("ML Feedback Loop initialized")
    
    async def start(self):
        """Start the feedback loop"""
        self.is_running = True
        
        # Start concurrent tasks
        tasks = [
            self._data_collection_loop(),
            self._training_loop(),
            self._prediction_loop(),
            self._performance_tracking_loop(),
        ]
        
        await asyncio.gather(*tasks)
    
    async def _data_collection_loop(self):
        """Continuously collect market data"""
        while self.is_running:
            try:
                # Collect data from multiple sources
                market_data = await self.data_collector.collect_all_market_data()
                
                # Store in Redis for swarm access
                await self._store_market_data(market_data)
                
                await asyncio.sleep(60)  # Update every minute
            except Exception as e:
                logger.error(f"Data collection error: {e}")
                await asyncio.sleep(300)  # Wait 5 min on error
    
    async def _training_loop(self):
        """Continuously train on new experiences"""
        while self.is_running:
            try:
                # Collect experiences from swarm
                exp_count = await self.orchestrator.collect_swarm_experiences()
                
                if exp_count > 0:
                    # Train model
                    loss = await self.orchestrator.train_on_experiences()
                    logger.info(f"Training complete. Loss: {loss}, Experiences: {exp_count}")
                
                await asyncio.sleep(300)  # Train every 5 minutes
            except Exception as e:
                logger.error(f"Training error: {e}")
                await asyncio.sleep(600)
    
    async def _prediction_loop(self):
        """Generate predictions for all tracked coins"""
        while self.is_running:
            try:
                # Get current market data
                market_data = await self._get_latest_market_data()
                
                # Generate predictions
                predictions = await self._generate_predictions(market_data)
                
                # Identify opportunities
                opportunities = await self.value_extractor.identify_opportunities(predictions)
                
                # Distribute to swarm
                await self._distribute_opportunities(opportunities)
                
                await asyncio.sleep(30)  # Predict every 30 seconds
            except Exception as e:
                logger.error(f"Prediction error: {e}")
                await asyncio.sleep(60)
    
    async def _performance_tracking_loop(self):
        """Track and analyze performance"""
        while self.is_running:
            try:
                # Collect performance metrics
                metrics = await self.performance_tracker.collect_swarm_metrics()
                
                # Analyze and adjust
                adjustments = await self.performance_tracker.analyze_performance(metrics)
                
                # Apply adjustments
                await self._apply_performance_adjustments(adjustments)
                
                await asyncio.sleep(600)  # Analyze every 10 minutes
            except Exception as e:
                logger.error(f"Performance tracking error: {e}")
                await asyncio.sleep(1200)
    
    async def _generate_predictions(self, market_data: List[MarketSignal]) -> List[CoinPotential]:
        """Generate predictions for all coins"""
        predictions = []
        
        for signal in market_data:
            try:
                # Extract features
                features = self.orchestrator._extract_features(signal.__dict__)
                features_tensor = torch.FloatTensor(features).unsqueeze(0)
                
                # Get predictions
                with torch.no_grad():
                    short, medium, long, volatility, confidence = self.orchestrator.model(features_tensor)
                
                # Calculate derived metrics
                risk_adjusted_return = self._calculate_risk_adjusted_return(
                    medium.item(), volatility.item()
                )
                
                optimal_size = self._calculate_optimal_position_size(
                    confidence.item(), volatility.item()
                )
                
                # Generate price targets
                current_price = signal.price
                targets = [
                    current_price * (1 + short.item() * 0.1),
                    current_price * (1 + medium.item() * 0.5),
                    current_price * (1 + long.item() * 1.0),
                ]
                
                # Calculate stop losses
                stop_losses = [
                    current_price * (1 - volatility.item() * 0.05),
                    current_price * (1 - volatility.item() * 0.1),
                ]
                
                prediction = CoinPotential(
                    coin_id=signal.coin_id,
                    short_term_potential=short.item(),
                    medium_term_potential=medium.item(),
                    long_term_potential=long.item(),
                    volatility_score=volatility.item(),
                    risk_adjusted_return=risk_adjusted_return,
                    optimal_position_size=optimal_size,
                    confidence_score=confidence.item(),
                    predicted_price_targets=targets,
                    stop_loss_levels=stop_losses
                )
                
                predictions.append(prediction)
                
            except Exception as e:
                logger.error(f"Prediction error for {signal.coin_id}: {e}")
        
        return predictions
    
    def _calculate_risk_adjusted_return(self, expected_return: float, volatility: float) -> float:
        """Calculate Sharpe-like ratio"""
        risk_free_rate = 0.02  # 2% annual
        if volatility > 0:
            return (expected_return - risk_free_rate) / volatility
        return 0
    
    def _calculate_optimal_position_size(self, confidence: float, volatility: float) -> float:
        """Kelly Criterion-inspired position sizing"""
        # Simplified Kelly: f = (p*b - q) / b
        # where p = probability of win, b = odds, q = probability of loss
        
        win_probability = confidence
        loss_probability = 1 - confidence
        odds = 2.0  # Assume 2:1 reward:risk
        
        kelly_fraction = (win_probability * odds - loss_probability) / odds
        
        # Apply safety factor and volatility adjustment
        safety_factor = 0.25  # Use 25% of Kelly
        volatility_adjustment = 1 - volatility
        
        position_size = max(0, min(0.2, kelly_fraction * safety_factor * volatility_adjustment))
        
        return position_size
    
    async def _store_market_data(self, data: List[MarketSignal]):
        """Store market data in Redis"""
        for signal in data:
            key = f"market:data:{signal.coin_id}"
            await self.orchestrator.redis_client.set(
                key, 
                json.dumps(signal.__dict__, default=str),
                ex=3600
            )
    
    async def _get_latest_market_data(self) -> List[MarketSignal]:
        """Retrieve latest market data"""
        data = []
        keys = await self.orchestrator.redis_client.keys("market:data:*")
        
        for key in keys:
            try:
                signal_data = await self.orchestrator.redis_client.get(key)
                if signal_data:
                    signal_dict = json.loads(signal_data)
                    # Convert back to MarketSignal
                    signal = MarketSignal(**signal_dict)
                    data.append(signal)
            except Exception as e:
                logger.error(f"Failed to retrieve {key}: {e}")
        
        return data
    
    async def _distribute_opportunities(self, opportunities: List[Dict]):
        """Distribute trading opportunities to swarm"""
        # Sort by potential
        opportunities.sort(key=lambda x: x['potential'], reverse=True)
        
        # Publish to Redis pub/sub
        for opp in opportunities[:20]:  # Top 20 opportunities
            await self.orchestrator.redis_client.publish(
                "swarm:opportunities",
                json.dumps(opp)
            )
    
    async def _apply_performance_adjustments(self, adjustments: Dict):
        """Apply performance-based adjustments"""
        # Update model hyperparameters
        if 'learning_rate' in adjustments:
            for param_group in self.orchestrator.optimizer.param_groups:
                param_group['lr'] = adjustments['learning_rate']
        
        # Update risk parameters
        if 'risk_threshold' in adjustments:
            await self.orchestrator.redis_client.set(
                "swarm:config:risk_threshold",
                adjustments['risk_threshold']
            )

class MarketDataCollector:
    """Collects comprehensive market data from multiple sources"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.exchanges = {}
        self.web3_providers = {}
        self.session = None
        self.social_analyzer = PuppeteerSocialAnalyzer(config.get('redis_url', 'redis://localhost:6379'))
        
    async def initialize(self):
        """Initialize data collection infrastructure"""
        self.session = aiohttp.ClientSession()
        
        # Initialize social analyzer
        await self.social_analyzer.initialize()
        
        # Initialize exchanges
        for exchange_id in ['binance', 'coinbase', 'kraken']:
            try:
                exchange_class = getattr(ccxt, exchange_id)
                self.exchanges[exchange_id] = exchange_class({
                    'enableRateLimit': True,
                    'apiKey': self.config.get(f'{exchange_id}_api_key'),
                    'secret': self.config.get(f'{exchange_id}_secret'),
                })
            except Exception as e:
                logger.warning(f"Failed to initialize {exchange_id}: {e}")
        
        # Initialize Web3 providers
        self.web3_providers['ethereum'] = Web3(Web3.HTTPProvider(
            self.config.get('ethereum_rpc', 'https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY')
        ))
        self.web3_providers['polygon'] = Web3(Web3.HTTPProvider(
            self.config.get('polygon_rpc', 'https://polygon-rpc.com')
        ))
    
    async def collect_all_market_data(self) -> List[MarketSignal]:
        """Collect data from all sources"""
        signals = []
        
        # Get top coins by market cap
        top_coins = await self._get_top_coins(limit=100)
        
        # Collect data for each coin
        tasks = [self._collect_coin_data(coin) for coin in top_coins]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, MarketSignal):
                signals.append(result)
        
        return signals
    
    async def _get_top_coins(self, limit: int = 100) -> List[Dict]:
        """Get top coins by market cap"""
        try:
            # Use CoinGecko API
            url = f"https://api.coingecko.com/api/v3/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': False
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get top coins: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching top coins: {e}")
            return []
    
    async def _collect_coin_data(self, coin: Dict) -> Optional[MarketSignal]:
        """Collect comprehensive data for a single coin"""
        try:
            # Basic market data
            market_data = await self._get_market_data(coin)
            
            # Technical indicators
            tech_indicators = await self._calculate_technical_indicators(coin['symbol'])
            
            # On-chain metrics
            on_chain = await self._get_on_chain_metrics(coin['id'])
            
            # Social sentiment
            sentiment = await self._get_social_sentiment(coin['symbol'])
            
            # DEX liquidity
            dex_liquidity = await self._get_dex_liquidity(coin['id'])
            
            # Whale activity
            whale_activity = await self._detect_whale_activity(coin['id'])
            
            # GitHub activity (for development activity)
            github_activity = await self._get_github_activity(coin['id'])
            
            # Social intelligence analysis
            social_metrics = await self.social_analyzer.analyze_project(
                coin_symbol=coin['symbol'].upper(),
                project_name=coin['name'],
                twitter_handle=coin.get('twitter_username'),
                website_url=coin.get('homepage', [''])[0] if coin.get('homepage') else None
            )
            
            return MarketSignal(
                coin_id=coin['id'],
                timestamp=datetime.utcnow(),
                price=market_data['price'],
                volume_24h=market_data['volume_24h'],
                market_cap=market_data['market_cap'],
                price_change_1h=market_data['price_change_1h'],
                price_change_24h=market_data['price_change_24h'],
                price_change_7d=market_data['price_change_7d'],
                social_sentiment=sentiment,
                whale_activity=whale_activity,
                dex_liquidity=dex_liquidity,
                github_activity=github_activity,
                on_chain_metrics=on_chain,
                technical_indicators=tech_indicators,
                social_metrics=social_metrics
            )
            
        except Exception as e:
            logger.error(f"Failed to collect data for {coin['id']}: {e}")
            return None
    
    async def _get_market_data(self, coin: Dict) -> Dict:
        """Get basic market data"""
        return {
            'price': coin.get('current_price', 0),
            'volume_24h': coin.get('total_volume', 0),
            'market_cap': coin.get('market_cap', 0),
            'price_change_1h': coin.get('price_change_percentage_1h_in_currency', 0),
            'price_change_24h': coin.get('price_change_percentage_24h', 0),
            'price_change_7d': coin.get('price_change_percentage_7d_in_currency', 0),
        }
    
    async def _calculate_technical_indicators(self, symbol: str) -> Dict[str, float]:
        """Calculate technical indicators"""
        try:
            # Get OHLCV data from exchange
            for exchange_id, exchange in self.exchanges.items():
                try:
                    ohlcv = await exchange.fetch_ohlcv(f"{symbol}/USDT", '1h', limit=100)
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    # Calculate indicators
                    indicators = {}
                    
                    # RSI
                    delta = df['close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    indicators['rsi'] = 100 - (100 / (1 + rs)).iloc[-1]
                    
                    # MACD
                    exp1 = df['close'].ewm(span=12, adjust=False).mean()
                    exp2 = df['close'].ewm(span=26, adjust=False).mean()
                    indicators['macd'] = (exp1 - exp2).iloc[-1]
                    
                    # Bollinger Bands position
                    sma = df['close'].rolling(window=20).mean()
                    std = df['close'].rolling(window=20).std()
                    upper_band = sma + (std * 2)
                    lower_band = sma - (std * 2)
                    current_price = df['close'].iloc[-1]
                    bb_range = upper_band.iloc[-1] - lower_band.iloc[-1]
                    if bb_range > 0:
                        indicators['bb_position'] = (current_price - lower_band.iloc[-1]) / bb_range
                    else:
                        indicators['bb_position'] = 0.5
                    
                    # Volume ratio
                    indicators['volume_ratio'] = df['volume'].iloc[-1] / df['volume'].rolling(window=20).mean().iloc[-1]
                    
                    return indicators
                    
                except Exception as e:
                    continue
            
            # Return default values if all exchanges fail
            return {
                'rsi': 50,
                'macd': 0,
                'bb_position': 0.5,
                'volume_ratio': 1
            }
            
        except Exception as e:
            logger.error(f"Technical indicator calculation failed: {e}")
            return {}
    
    async def _get_on_chain_metrics(self, coin_id: str) -> Dict[str, float]:
        """Get on-chain metrics"""
        # This would connect to blockchain analytics APIs
        # For now, return simulated data
        return {
            'active_addresses': np.random.randint(1000, 100000),
            'transaction_volume': np.random.uniform(1e6, 1e9),
            'exchange_inflow': np.random.uniform(1e5, 1e7),
            'exchange_outflow': np.random.uniform(1e5, 1e7),
        }
    
    async def _get_social_sentiment(self, symbol: str) -> float:
        """Analyze social media sentiment"""
        # This is now handled by social_analyzer in _collect_coin_data
        # Return default for backward compatibility
        return 0.5
    
    async def _get_dex_liquidity(self, coin_id: str) -> float:
        """Check DEX liquidity depth"""
        # Would query Uniswap, Sushiswap, etc.
        # Return liquidity score 0-1
        return np.random.uniform(0.2, 0.9)
    
    async def _detect_whale_activity(self, coin_id: str) -> float:
        """Detect large holder movements"""
        # Would monitor large wallet movements
        # Return activity score 0-1
        return np.random.uniform(0.1, 0.7)
    
    async def _get_github_activity(self, coin_id: str) -> float:
        """Get development activity score"""
        # This is now handled by social_analyzer in _collect_coin_data
        # Return default for backward compatibility
        return 0.5

class ParallelValueExtractor:
    """Optimizes parallel value extraction across multiple opportunities"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.active_positions = {}
        self.capital_allocator = CapitalAllocator(config)
        self.risk_manager = RiskManager(config)
        
    async def initialize(self):
        """Initialize value extraction system"""
        await self.capital_allocator.initialize()
        await self.risk_manager.initialize()
    
    async def identify_opportunities(self, predictions: List[CoinPotential]) -> List[Dict]:
        """Identify and rank trading opportunities"""
        opportunities = []
        
        for pred in predictions:
            # Filter by minimum thresholds
            if pred.confidence_score < 0.6:
                continue
            
            if pred.risk_adjusted_return < 1.5:
                continue
            
            # Additional filtering based on social metrics
            if hasattr(pred, 'social_metrics') and pred.social_metrics:
                sm = pred.social_metrics
                # Skip if high risk or low credibility
                if sm.risk_score > 0.7 or sm.overall_credibility_score < 0.3:
                    continue
                # Skip if high bot activity
                if sm.bot_activity_score > 0.8:
                    continue
            
            # Calculate opportunity score
            score = self._calculate_opportunity_score(pred)
            
            # Determine strategy
            strategy = self._select_strategy(pred)
            
            opportunity = {
                'coin_id': pred.coin_id,
                'score': score,
                'potential': pred.medium_term_potential,
                'strategy': strategy,
                'position_size': pred.optimal_position_size,
                'entry_targets': pred.predicted_price_targets[:1],
                'stop_loss': pred.stop_loss_levels[0],
                'take_profit': pred.predicted_price_targets[1],
                'confidence': pred.confidence_score,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            opportunities.append(opportunity)
        
        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        # Apply portfolio constraints
        filtered_opportunities = await self._apply_portfolio_constraints(opportunities)
        
        return filtered_opportunities
    
    def _calculate_opportunity_score(self, pred: CoinPotential) -> float:
        """Calculate composite opportunity score"""
        # Weight different factors
        weights = {
            'potential': 0.3,
            'confidence': 0.25,
            'risk_adjusted_return': 0.25,
            'volatility': 0.2
        }
        
        score = (
            pred.medium_term_potential * weights['potential'] +
            pred.confidence_score * weights['confidence'] +
            min(pred.risk_adjusted_return / 5, 1) * weights['risk_adjusted_return'] +
            (1 - pred.volatility_score) * weights['volatility']
        )
        
        return score
    
    def _select_strategy(self, pred: CoinPotential) -> str:
        """Select optimal trading strategy"""
        if pred.volatility_score > 0.7 and pred.short_term_potential > 0.8:
            return "scalping"
        elif pred.medium_term_potential > 0.7 and pred.volatility_score < 0.5:
            return "swing_trading"
        elif pred.long_term_potential > 0.8 and pred.confidence_score > 0.8:
            return "position_trading"
        elif pred.volatility_score > 0.8:
            return "arbitrage"
        else:
            return "balanced"
    
    async def _apply_portfolio_constraints(self, opportunities: List[Dict]) -> List[Dict]:
        """Apply risk and portfolio constraints"""
        filtered = []
        total_allocation = 0
        correlation_matrix = await self._calculate_correlation_matrix(opportunities)
        
        for opp in opportunities:
            # Check capital availability
            if total_allocation + opp['position_size'] > 0.9:  # Max 90% allocation
                continue
            
            # Check correlation with existing positions
            if not await self._check_correlation_constraint(opp, filtered, correlation_matrix):
                continue
            
            # Check sector concentration
            if not await self._check_sector_concentration(opp, filtered):
                continue
            
            filtered.append(opp)
            total_allocation += opp['position_size']
            
            # Limit to manageable number
            if len(filtered) >= 10:
                break
        
        return filtered
    
    async def _calculate_correlation_matrix(self, opportunities: List[Dict]) -> np.ndarray:
        """Calculate correlation between opportunities"""
        # Would calculate actual price correlations
        # For now, return random correlations
        n = len(opportunities)
        matrix = np.random.uniform(-0.5, 0.5, (n, n))
        np.fill_diagonal(matrix, 1.0)
        return matrix
    
    async def _check_correlation_constraint(self, opp: Dict, existing: List[Dict], corr_matrix: np.ndarray) -> bool:
        """Check if opportunity is too correlated with existing positions"""
        # Maximum allowed correlation
        max_correlation = 0.7
        
        # Would check actual correlations
        # For now, always return True
        return True
    
    async def _check_sector_concentration(self, opp: Dict, existing: List[Dict]) -> bool:
        """Check sector concentration limits"""
        # Would categorize by sector and check limits
        # For now, always return True
        return True

class CapitalAllocator:
    """Manages capital allocation across swarm"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = None
        
    async def initialize(self):
        """Initialize capital allocator"""
        self.redis_client = await redis.from_url(self.config.get('redis_url', 'redis://localhost:6379'))
    
    async def allocate_capital(self, opportunity: Dict, clone_id: str) -> Optional[float]:
        """Allocate capital for opportunity"""
        # Get available capital
        available = await self._get_available_capital(clone_id)
        
        # Calculate allocation
        requested = opportunity['position_size'] * available
        
        # Check limits
        if requested > available * 0.2:  # Max 20% per position
            requested = available * 0.2
        
        # Reserve capital
        if await self._reserve_capital(clone_id, requested):
            return requested
        
        return None
    
    async def _get_available_capital(self, clone_id: str) -> float:
        """Get available capital for clone"""
        capital_data = await self.redis_client.get(f"swarm:clone:{clone_id}:capital")
        if capital_data:
            return float(capital_data)
        return 0
    
    async def _reserve_capital(self, clone_id: str, amount: float) -> bool:
        """Reserve capital for trade"""
        # Would implement atomic capital reservation
        return True

class RiskManager:
    """Manages risk across the swarm"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = None
        
    async def initialize(self):
        """Initialize risk manager"""
        self.redis_client = await redis.from_url(self.config.get('redis_url', 'redis://localhost:6379'))
    
    async def check_risk_limits(self, opportunity: Dict, clone_id: str) -> bool:
        """Check if opportunity passes risk limits"""
        # Check daily loss limit
        daily_loss = await self._get_daily_loss(clone_id)
        if daily_loss > 0.1:  # 10% daily loss limit
            return False
        
        # Check position limits
        position_count = await self._get_position_count(clone_id)
        if position_count >= 5:  # Max 5 concurrent positions per clone
            return False
        
        # Check volatility limits
        if opportunity.get('volatility', 0) > 0.9:
            return False
        
        return True
    
    async def _get_daily_loss(self, clone_id: str) -> float:
        """Get daily loss percentage"""
        # Would calculate actual daily P&L
        return 0.05
    
    async def _get_position_count(self, clone_id: str) -> int:
        """Get current position count"""
        # Would count actual positions
        return 2

class PerformanceTracker:
    """Tracks and analyzes swarm performance"""
    
    def __init__(self):
        self.metrics_history = deque(maxlen=10000)
        
    async def collect_swarm_metrics(self) -> Dict:
        """Collect performance metrics from all clones"""
        # Would aggregate actual metrics
        return {
            'total_profit': np.random.uniform(-1000, 5000),
            'win_rate': np.random.uniform(0.4, 0.7),
            'sharpe_ratio': np.random.uniform(0.5, 2.5),
            'max_drawdown': np.random.uniform(0.05, 0.25),
            'active_clones': np.random.randint(5, 20),
        }
    
    async def analyze_performance(self, metrics: Dict) -> Dict:
        """Analyze performance and suggest adjustments"""
        adjustments = {}
        
        # Adjust learning rate based on performance
        if metrics['win_rate'] < 0.5:
            adjustments['learning_rate'] = 0.0001  # Reduce learning rate
        elif metrics['win_rate'] > 0.65:
            adjustments['learning_rate'] = 0.01  # Increase learning rate
        
        # Adjust risk threshold
        if metrics['max_drawdown'] > 0.2:
            adjustments['risk_threshold'] = 0.8  # Reduce risk
        elif metrics['max_drawdown'] < 0.1:
            adjustments['risk_threshold'] = 1.2  # Increase risk
        
        return adjustments

# Export main class
__all__ = ['MLFeedbackLoop', 'SwarmLearningOrchestrator', 'MarketDataCollector', 'ParallelValueExtractor']