"""
Quantum Swarm Coordinator - Master orchestrator for multi-chain trading
Integrates Solana Agent Kit and MegaETH for cross-chain operations
"""

import asyncio
import redis.asyncio as aioredis
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime
import json
import hashlib
from loguru import logger

from solana_agent_wrapper import SolanaSwarmCoordinator, SolanaSwarmAgent
from config_solana import solana_config, megaeth_config, crosschain_config, REDIS_CONFIG
from config import SwarmConfig, TradingPhase

# Import existing agents
from agents.mev_hunter import MEVHunterAgent
from agents.social_sentiment import SocialSentimentAgent
from strategies.cross_chain_arbitrage import CrossChainArbitrageStrategy
from strategies.flash_loan_cascade import FlashLoanCascadeStrategy
from ml_feedback_loop import MLFeedbackLoop


class QuantumSwarmCoordinator:
    """
    Master coordinator for the Quantum Swarm Trader
    Manages multi-chain operations and fractal clone spawning
    """
    
    def __init__(self, initial_capital: Decimal = Decimal("100")):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trading_phase = TradingPhase.MICRO
        
        # Redis for swarm communication
        self.redis_client = None
        
        # Chain coordinators
        self.solana_coordinator = None
        self.ethereum_agents = {}
        
        # Swarm state
        self.total_clones = 0
        self.clone_registry = {}
        self.opportunity_locks = {}
        
        # Performance tracking
        self.trade_history = []
        self.profit_tracker = {
            "total_trades": 0,
            "winning_trades": 0,
            "total_profit": Decimal("0"),
            "phase_start_time": datetime.now(),
        }
        
        # Quantum decision engine state
        self.quantum_state = self._initialize_quantum_state()
        
        # ML feedback loop
        self.ml_feedback = MLFeedbackLoop({
            'redis_url': f"redis://{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/{REDIS_CONFIG['db']}"
        })
        
    def _initialize_quantum_state(self) -> Dict[str, Any]:
        """Initialize quantum-inspired decision engine"""
        return {
            "superposition_states": {},  # Multiple market scenarios
            "entangled_pairs": {},      # Correlated trading pairs
            "probability_fields": {},    # Probability distributions
            "collapse_history": [],      # Decision history
        }
    
    async def initialize(self, solana_private_key: str):
        """Initialize all components"""
        logger.info("Initializing Quantum Swarm Coordinator")
        
        # Initialize Redis
        self.redis_client = await aioredis.create_redis_pool(
            f"redis://{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/{REDIS_CONFIG['db']}",
            encoding="utf-8"
        )
        
        # Initialize Solana coordinator
        self.solana_coordinator = SolanaSwarmCoordinator(solana_private_key)
        initial_balance = await self.solana_coordinator.initialize()
        
        # Initialize communication channels
        await self._setup_redis_channels()
        
        # Initialize ML feedback loop
        await self.ml_feedback.initialize()
        
        # Start background tasks
        asyncio.create_task(self._monitor_clone_health())
        asyncio.create_task(self._process_swarm_messages())
        asyncio.create_task(self.ml_feedback.start())
        
        logger.info(f"Quantum Swarm initialized with {initial_balance} SOL")
        return initial_balance
    
    async def _setup_redis_channels(self):
        """Setup Redis pub/sub channels for swarm communication"""
        channels = [
            "swarm:opportunities",
            "swarm:claims", 
            "swarm:results",
            "swarm:heartbeat",
            "swarm:spawning",
        ]
        
        for channel in channels:
            await self.redis_client.subscribe(channel)
    
    async def _monitor_clone_health(self):
        """Monitor health of all clones"""
        while True:
            try:
                # Check Solana clones
                for clone_id, clone in self.solana_coordinator.clones.items():
                    heartbeat_key = f"heartbeat:{clone_id}"
                    await self.redis_client.setex(heartbeat_key, 30, "alive")
                
                # Check for dead clones
                all_clones = await self.redis_client.keys("heartbeat:*")
                for key in all_clones:
                    ttl = await self.redis_client.ttl(key)
                    if ttl <= 0:
                        clone_id = key.split(":")[1]
                        logger.warning(f"Clone {clone_id} appears dead, attempting resurrection")
                        await self._resurrect_clone(clone_id)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring clone health: {e}")
                await asyncio.sleep(10)
    
    async def _process_swarm_messages(self):
        """Process messages from the swarm"""
        while True:
            try:
                message = await self.redis_client.get_message(timeout=1)
                if message and message['type'] == 'message':
                    await self._handle_swarm_message(
                        message['channel'],
                        json.loads(message['data'])
                    )
                    
            except Exception as e:
                logger.error(f"Error processing swarm messages: {e}")
                await asyncio.sleep(1)
    
    async def _handle_swarm_message(self, channel: str, data: Dict):
        """Handle incoming swarm messages"""
        if channel == "swarm:opportunities":
            await self._handle_opportunity(data)
        elif channel == "swarm:claims":
            await self._handle_claim(data)
        elif channel == "swarm:results":
            await self._handle_result(data)
        elif channel == "swarm:spawning":
            await self._handle_spawn_request(data)
    
    async def _handle_opportunity(self, opportunity: Dict):
        """Handle new opportunity from swarm"""
        opp_id = opportunity['id']
        
        # Use quantum decision engine to evaluate
        score = await self._quantum_evaluate_opportunity(opportunity)
        
        if score > 0.7:  # High confidence threshold
            # Try to claim opportunity
            claimed = await self._claim_opportunity(opp_id)
            if claimed:
                asyncio.create_task(self._execute_opportunity(opportunity))
    
    async def _quantum_evaluate_opportunity(self, opportunity: Dict) -> float:
        """
        Use quantum-inspired algorithm to evaluate opportunity
        
        This simulates quantum superposition by evaluating multiple
        market scenarios simultaneously
        """
        # Get ML predictions if available
        ml_prediction = None
        coin_id = opportunity.get('token', opportunity.get('coin_id', ''))
        
        if coin_id:
            prediction_key = f"swarm:ml:prediction:{coin_id}"
            ml_data = await self.redis_client.get(prediction_key)
            if ml_data:
                ml_prediction = json.loads(ml_data)
        
        # Create superposition of market states
        scenarios = []
        
        # Base scenario
        base_profit = opportunity.get('expected_profit', 0)
        base_risk = opportunity.get('risk_score', 0.5)
        
        # Adjust based on ML predictions
        if ml_prediction:
            confidence = ml_prediction.get('confidence_score', 0.5)
            potential = ml_prediction.get('medium_term_potential', 0.5)
            base_profit *= (1 + potential)
            base_risk *= (1 - confidence * 0.5)
        
        # Generate quantum states (parallel universes)
        for i in range(10):
            # Each state has slightly different market conditions
            volatility_factor = 1 + (i - 5) * 0.1  # -50% to +50%
            slippage_factor = 1 + (i - 5) * 0.05   # -25% to +25%
            
            scenario_profit = base_profit * volatility_factor
            scenario_risk = min(base_risk * slippage_factor, 1.0)
            
            # Calculate probability amplitude
            amplitude = (scenario_profit * (1 - scenario_risk)) / 100
            scenarios.append(amplitude)
        
        # Collapse wave function (take weighted average)
        final_score = sum(scenarios) / len(scenarios)
        
        # Store in quantum state
        self.quantum_state['superposition_states'][opportunity['id']] = scenarios
        self.quantum_state['collapse_history'].append({
            'opportunity_id': opportunity['id'],
            'final_score': final_score,
            'ml_enhanced': ml_prediction is not None,
            'timestamp': datetime.now().isoformat(),
        })
        
        return final_score
    
    async def _claim_opportunity(self, opportunity_id: str) -> bool:
        """Atomically claim an opportunity"""
        lock_key = f"opp_lock:{opportunity_id}"
        
        # Try to set lock with 5 second expiry
        result = await self.redis_client.set(
            lock_key,
            self.solana_coordinator.master_agent.agent_id,
            expire=5,
            exist="SET_IF_NOT_EXIST"
        )
        
        return result is not None
    
    async def _execute_opportunity(self, opportunity: Dict):
        """Execute a claimed opportunity"""
        execution_result = None
        try:
            opp_type = opportunity.get('type', 'unknown')
            
            if opp_type == 'arbitrage':
                execution_result = await self._execute_arbitrage(opportunity)
            elif opp_type == 'mev':
                execution_result = await self._execute_mev(opportunity)
            elif opp_type == 'liquidity':
                execution_result = await self._execute_liquidity_provision(opportunity)
            else:
                logger.warning(f"Unknown opportunity type: {opp_type}")
            
            # Record experience for ML training
            if execution_result:
                await self._record_trading_experience(opportunity, execution_result)
                
        except Exception as e:
            logger.error(f"Error executing opportunity: {e}")
        finally:
            # Release lock
            lock_key = f"opp_lock:{opportunity['id']}"
            await self.redis_client.delete(lock_key)
    
    async def _execute_arbitrage(self, opportunity: Dict):
        """Execute arbitrage opportunity"""
        chain = opportunity.get('chain', 'solana')
        
        if chain == 'solana':
            # Use Solana coordinator
            success = await self.solana_coordinator.execute_best_opportunity([opportunity])
        else:
            # Use cross-chain arbitrage strategy
            strategy = CrossChainArbitrageStrategy()
            success = await strategy.execute(opportunity)
        
        if success:
            self.profit_tracker['winning_trades'] += 1
            
        self.profit_tracker['total_trades'] += 1
        
        return {'success': success, 'chain': chain, 'type': 'arbitrage'}
    
    async def _execute_mev(self, opportunity: Dict):
        """Execute MEV opportunity"""
        chain = opportunity.get('chain', 'ethereum')
        
        if chain == 'solana':
            # Use Jito for Solana MEV
            agent = self._get_specialized_solana_agent('jito_mev_hunter')
            if agent:
                await agent.execute_mev_strategy(opportunity.get('strategy', 'sandwich'))
        else:
            # Use Flashbots for Ethereum MEV
            mev_agent = MEVHunterAgent('ethereum')
            result = await mev_agent.execute_opportunity(opportunity)
            return {'success': result, 'chain': chain, 'type': 'mev'}
    
    def _get_specialized_solana_agent(self, specialization: str) -> Optional[SolanaSwarmAgent]:
        """Get a Solana agent with specific specialization"""
        for clone_id, clone in self.solana_coordinator.clones.items():
            if clone.specialization == specialization:
                return clone
                
        # Return master if no specialized clone found
        return self.solana_coordinator.master_agent
    
    async def _execute_liquidity_provision(self, opportunity: Dict):
        """Execute liquidity provision opportunity"""
        pool = opportunity.get('pool_address')
        token_a = opportunity.get('token_a')
        token_b = opportunity.get('token_b')
        
        agent = self._get_specialized_solana_agent('raydium_liquidity')
        if agent:
            result = await agent.provide_liquidity(
                pool,
                Decimal(str(opportunity.get('amount_a', 0))),
                Decimal(str(opportunity.get('amount_b', 0)))
            )
            return {'success': result, 'chain': 'solana', 'type': 'liquidity'}
        return {'success': False, 'chain': 'solana', 'type': 'liquidity'}
    
    async def check_phase_transition(self):
        """Check if we should transition to next trading phase"""
        if self.current_capital >= 1000 and self.trading_phase == TradingPhase.MICRO:
            self.trading_phase = TradingPhase.GROWTH
            logger.info(f"Transitioning to GROWTH phase with ${self.current_capital}")
            await self._announce_phase_transition()
            
        elif self.current_capital >= 10000 and self.trading_phase == TradingPhase.GROWTH:
            self.trading_phase = TradingPhase.SCALE
            logger.info(f"Transitioning to SCALE phase with ${self.current_capital}")
            await self._announce_phase_transition()
    
    async def _announce_phase_transition(self):
        """Announce phase transition to all clones"""
        message = {
            "type": "phase_transition",
            "new_phase": self.trading_phase.value,
            "timestamp": datetime.now().isoformat(),
        }
        
        await self.redis_client.publish("swarm:announcements", json.dumps(message))
    
    async def spawn_clone_check(self):
        """Check if conditions are met to spawn new clones"""
        # Check Solana clones
        spawned = await self.solana_coordinator.spawn_clone_if_ready(self.current_capital)
        
        if spawned:
            self.total_clones += 1
            
            # Announce to swarm
            message = {
                "type": "clone_spawned",
                "total_clones": self.total_clones,
                "chain": "solana",
                "timestamp": datetime.now().isoformat(),
            }
            
            await self.redis_client.publish("swarm:spawning", json.dumps(message))
    
    async def _resurrect_clone(self, clone_id: str):
        """Attempt to resurrect a dead clone"""
        # Get clone state from Redis
        state_key = f"clone_state:{clone_id}"
        state_data = await self.redis_client.get(state_key)
        
        if state_data:
            state = json.loads(state_data)
            
            # Recreate clone with saved state
            # This is a simplified resurrection - in production would be more complex
            logger.info(f"Resurrecting clone {clone_id}")
    
    async def run_quantum_cycle(self):
        """Run one cycle of quantum swarm operations"""
        try:
            # Update current capital
            await self._update_capital_state()
            
            # Check phase transition
            await self.check_phase_transition()
            
            # Check clone spawning
            await self.spawn_clone_check()
            
            # Coordinate cross-chain arbitrage
            await self._coordinate_cross_chain_arbitrage()
            
            # Run Solana-specific cycle
            await self.solana_coordinator.run_swarm_cycle()
            
            # Collect and analyze swarm intelligence
            await self._analyze_swarm_intelligence()
            
        except Exception as e:
            logger.error(f"Error in quantum cycle: {e}")
    
    async def _update_capital_state(self):
        """Update total capital across all chains"""
        total = Decimal("0")
        
        # Solana capital
        sol_balance = await self.solana_coordinator.master_agent.get_balance()
        total += sol_balance
        
        for clone in self.solana_coordinator.clones.values():
            total += await clone.get_balance()
        
        # Add Ethereum/MegaETH capital (would need Web3 integration)
        # eth_balance = await self.get_ethereum_balance()
        # total += eth_balance
        
        self.current_capital = total
        
        # Update Redis
        await self.redis_client.set("swarm:total_capital", str(total))
    
    async def _coordinate_cross_chain_arbitrage(self):
        """Coordinate arbitrage across multiple chains"""
        # Check SOL/ETH arbitrage via bridges
        opportunities = []
        
        # Example: Check SOL price on Solana vs wrapped SOL on Ethereum
        sol_price_solana = await self._get_token_price("solana", "SOL")
        sol_price_eth = await self._get_token_price("ethereum", "wSOL")
        
        if sol_price_solana and sol_price_eth:
            price_diff = abs(sol_price_eth - sol_price_solana) / sol_price_solana
            
            if price_diff > 0.005:  # 0.5% difference
                opportunity = {
                    "id": hashlib.sha256(f"arb_{datetime.now().isoformat()}".encode()).hexdigest()[:16],
                    "type": "arbitrage",
                    "subtype": "cross_chain",
                    "chain_a": "solana",
                    "chain_b": "ethereum",
                    "token": "SOL",
                    "price_a": sol_price_solana,
                    "price_b": sol_price_eth,
                    "expected_profit": price_diff,
                    "timestamp": datetime.now().isoformat(),
                }
                
                # Publish to swarm
                await self.redis_client.publish(
                    "swarm:opportunities",
                    json.dumps(opportunity)
                )
    
    async def _get_token_price(self, chain: str, token: str) -> Optional[float]:
        """Get token price from various sources"""
        # This would integrate with real price feeds
        # For now, return mock prices
        mock_prices = {
            ("solana", "SOL"): 100.0,
            ("ethereum", "wSOL"): 100.5,
        }
        
        return mock_prices.get((chain, token))
    
    async def _analyze_swarm_intelligence(self):
        """Analyze collective intelligence from all clones"""
        # Collect recent trades from all clones
        recent_trades = await self.redis_client.lrange("swarm:recent_trades", 0, 100)
        
        if recent_trades:
            # Analyze patterns
            winning_strategies = {}
            
            for trade_data in recent_trades:
                trade = json.loads(trade_data)
                strategy = trade.get('strategy')
                profit = trade.get('profit', 0)
                
                if strategy:
                    if strategy not in winning_strategies:
                        winning_strategies[strategy] = {
                            'count': 0,
                            'total_profit': 0,
                        }
                    
                    winning_strategies[strategy]['count'] += 1
                    winning_strategies[strategy]['total_profit'] += profit
            
            # Update strategy weights based on performance
            await self._update_strategy_weights(winning_strategies)
            
            # Share intelligence with ML system
            await self._share_swarm_intelligence(winning_strategies)
    
    async def _update_strategy_weights(self, performance_data: Dict):
        """Update strategy weights based on performance"""
        """Update strategy weights based on performance"""
        # Calculate normalized scores
        total_profit = sum(data['total_profit'] for data in performance_data.values())
        
        if total_profit > 0:
            for strategy, data in performance_data.items():
                weight = data['total_profit'] / total_profit
                # Store updated weight
                await self.redis_client.set(f"strategy:weight:{strategy}", str(weight), expire=3600)
    
    async def get_swarm_status(self) -> Dict:
        """Get current swarm status"""
        return {
            "total_capital": float(self.current_capital),
            "trading_phase": self.trading_phase.value,
            "total_clones": self.total_clones,
            "solana_clones": len(self.solana_coordinator.clones),
            "profit_tracker": {
                "total_trades": self.profit_tracker['total_trades'],
                "win_rate": (
                    self.profit_tracker['winning_trades'] / self.profit_tracker['total_trades']
                    if self.profit_tracker['total_trades'] > 0 else 0
                ),
                "total_profit": float(self.profit_tracker['total_profit']),
            },
            "quantum_state": {
                "active_superpositions": len(self.quantum_state['superposition_states']),
                "decisions_made": len(self.quantum_state['collapse_history']),
            },
            "ml_feedback": {
                "status": "active" if self.ml_feedback.is_running else "inactive",
                "model_confidence": "high"  # Would get from actual ML metrics
            }
        }
    
    async def run(self):
        """Main quantum swarm loop"""
        logger.info("Starting Quantum Swarm Trader")
        
        while True:
            await self.run_quantum_cycle()
            await asyncio.sleep(3)  # 3 second cycles for responsiveness
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down Quantum Swarm")
        
        # Save state to Redis
        state = {
            "total_capital": str(self.current_capital),
            "trading_phase": self.trading_phase.value,
            "total_clones": self.total_clones,
            "profit_tracker": self.profit_tracker,
            "quantum_state": self.quantum_state,
        }
        
        await self.redis_client.set("swarm:final_state", json.dumps(state))
        
        # Shutdown coordinators
        if self.solana_coordinator:
            await self.solana_coordinator.shutdown()
        
        # Close Redis
        if self.redis_client:
            self.redis_client.close()
            await self.redis_client.wait_closed()
        
        logger.info("Quantum Swarm shutdown complete")
    
    async def _record_trading_experience(self, opportunity: Dict, result: Dict):
        """Record trading experience for ML training"""
        try:
            # Get market data at time of trade
            coin_id = opportunity.get('token', opportunity.get('coin_id', ''))
            market_signal = await self.redis_client.get(f"market:data:{coin_id}")
            
            experience = {
                'market_signal': json.loads(market_signal) if market_signal else {},
                'outcome': {
                    'coin_id': coin_id,
                    'entry_time': opportunity.get('timestamp', datetime.now().isoformat()),
                    'exit_time': datetime.now().isoformat(),
                    'entry_price': opportunity.get('price_a', 0),
                    'exit_price': opportunity.get('price_b', 0),
                    'position_size': opportunity.get('amount', 0),
                    'profit_loss': opportunity.get('expected_profit', 0) if result.get('success') else -0.01,
                    'profit_percentage': opportunity.get('expected_profit', 0) * 100 if result.get('success') else -1,
                    'strategy_used': opportunity.get('type', 'unknown'),
                    'clone_id': self.solana_coordinator.master_agent.agent_id
                }
            }
            
            # Store experience for ML training
            await self.redis_client.lpush(
                f"swarm:clone:{self.solana_coordinator.master_agent.agent_id}:experience",
                json.dumps(experience)
            )
            
            # Trim to keep only recent experiences
            await self.redis_client.ltrim(
                f"swarm:clone:{self.solana_coordinator.master_agent.agent_id}:experience",
                0, 1000
            )
            
        except Exception as e:
            logger.error(f"Failed to record trading experience: {e}")
    
    async def _share_swarm_intelligence(self, winning_strategies: Dict):
        """Share swarm intelligence with ML system"""
        try:
            intelligence_data = {
                'timestamp': datetime.now().isoformat(),
                'winning_strategies': winning_strategies,
                'current_phase': self.trading_phase.value,
                'total_capital': float(self.current_capital),
                'clone_count': self.total_clones,
                'quantum_decisions': len(self.quantum_state['collapse_history'])
            }
            
            await self.redis_client.set(
                "swarm:intelligence:latest",
                json.dumps(intelligence_data),
                expire=3600
            )
            
        except Exception as e:
            logger.error(f"Failed to share swarm intelligence: {e}")