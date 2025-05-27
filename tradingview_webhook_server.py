#!/usr/bin/env python3
"""
Standalone TradingView Webhook Server
Receives and processes TradingView alerts
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from aiohttp import web

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingview_integration import TradingViewWebhookServer, TradingViewAlert
from swarm_coordinator import SwarmCoordinator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tradingview_webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TradingViewHandler:
    """Handles TradingView alerts and converts them to trading actions"""
    
    def __init__(self):
        self.swarm = None
        self.stats = {
            'total_alerts': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'last_alert': None
        }
        
    async def initialize_swarm(self):
        """Initialize the swarm coordinator"""
        try:
            self.swarm = SwarmCoordinator(
                initial_capital=float(os.getenv('INITIAL_CAPITAL', '1000')),
                max_agents=5
            )
            await self.swarm.initialize()
            logger.info("Swarm coordinator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize swarm: {e}")
            self.swarm = None
    
    async def process_alert(self, alert: TradingViewAlert):
        """Process TradingView alert"""
        self.stats['total_alerts'] += 1
        self.stats['last_alert'] = alert.timestamp
        
        logger.info(f"Processing alert: {alert.symbol} {alert.action} at {alert.price}")
        
        # Validate alert
        if not self.validate_alert(alert):
            logger.warning(f"Invalid alert: {alert}")
            return
        
        # Convert to trading signal
        try:
            if self.swarm:
                signal = {
                    'timestamp': alert.timestamp,
                    'symbol': alert.symbol,
                    'action': alert.action.upper(),
                    'price': alert.price,
                    'source': f'TradingView:{alert.strategy_name}',
                    'confidence': 0.8,
                    'timeframe': alert.timeframe,
                    'indicators': alert.indicators
                }
                
                # Execute through swarm
                result = await self.swarm.process_external_signal(signal)
                
                if result.get('success'):
                    self.stats['successful_trades'] += 1
                    logger.info(f"Trade executed successfully: {result}")
                else:
                    self.stats['failed_trades'] += 1
                    logger.error(f"Trade failed: {result}")
            else:
                logger.warning("Swarm not initialized, storing alert only")
                
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
            self.stats['failed_trades'] += 1
    
    def validate_alert(self, alert: TradingViewAlert) -> bool:
        """Validate TradingView alert"""
        # Check required fields
        if not alert.symbol or not alert.action:
            return False
        
        # Validate action
        valid_actions = ['buy', 'sell', 'long', 'short', 'close', 'exit']
        if alert.action.lower() not in valid_actions:
            return False
        
        # Validate price
        if alert.price <= 0:
            return False
        
        return True
    
    def get_stats(self) -> dict:
        """Get current statistics"""
        return self.stats


async def main():
    """Main function"""
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    logger.info("Starting TradingView Webhook Server")
    
    # Create handler
    handler = TradingViewHandler()
    
    # Initialize swarm if enabled
    if os.getenv('ENABLE_LIVE_TRADING', 'false').lower() == 'true':
        await handler.initialize_swarm()
    else:
        logger.info("Live trading disabled - running in alert-only mode")
    
    # Create webhook server
    port = int(os.getenv('WEBHOOK_PORT', '8080'))
    server = TradingViewWebhookServer(port=port)
    
    # Register alert handler
    server.register_alert_handler(handler.process_alert)
    
    # Add stats endpoint
    async def stats_handler(request):
        stats = handler.get_stats()
        return web.json_response(stats)
    
    server.app.router.add_get('/stats', stats_handler)
    
    # Start server
    await server.start()
    
    logger.info(f"Webhook server running on http://0.0.0.0:{port}")
    logger.info("Endpoints:")
    logger.info(f"  - POST /webhook/tradingview - Receive alerts")
    logger.info(f"  - GET /health - Health check")
    logger.info(f"  - GET /stats - View statistics")
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == "__main__":
    asyncio.run(main())