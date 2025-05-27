"""
TradingView Integration Module for Crypto Swarm Trader
Handles webhooks, data import/export, and signal processing
"""

import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import aiohttp
from aiohttp import web
import logging
import os
import csv
from dataclasses import dataclass
import hmac
import hashlib
from redis import Redis
import pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TradingViewAlert:
    """Represents a TradingView alert/signal"""
    timestamp: datetime
    symbol: str
    action: str  # 'buy', 'sell', 'close'
    price: float
    strategy_name: str
    timeframe: str
    indicators: Dict[str, float]
    message: str
    

@dataclass
class TradingViewData:
    """Represents imported TradingView data"""
    symbol: str
    timeframe: str
    data: pd.DataFrame
    indicators: List[str]
    

class TradingViewWebhookServer:
    """Webhook server to receive TradingView alerts"""
    
    def __init__(self, port: int = 8080, secret_key: str = None):
        self.port = port
        self.secret_key = secret_key or os.getenv('TRADINGVIEW_WEBHOOK_SECRET', 'your-secret-key')
        self.redis = Redis(host='localhost', port=6379, db=0)
        self.alert_handlers = []
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        """Setup webhook routes"""
        self.app.router.add_post('/webhook/tradingview', self.handle_webhook)
        self.app.router.add_get('/health', self.health_check)
        
    def verify_webhook(self, body: bytes, signature: str) -> bool:
        """Verify webhook signature for security"""
        expected_signature = hmac.new(
            self.secret_key.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)
    
    async def handle_webhook(self, request: web.Request) -> web.Response:
        """Handle incoming TradingView webhook"""
        try:
            # Get signature from headers
            signature = request.headers.get('X-Webhook-Signature', '')
            
            # Read body
            body = await request.read()
            
            # Verify signature (optional but recommended)
            # if not self.verify_webhook(body, signature):
            #     return web.Response(text="Unauthorized", status=401)
            
            # Parse JSON
            data = json.loads(body)
            
            # Create alert object
            alert = TradingViewAlert(
                timestamp=datetime.now(),
                symbol=data.get('symbol', 'UNKNOWN'),
                action=data.get('action', 'unknown').lower(),
                price=float(data.get('price', 0)),
                strategy_name=data.get('strategy', 'TradingView'),
                timeframe=data.get('timeframe', '1h'),
                indicators=data.get('indicators', {}),
                message=data.get('message', '')
            )
            
            # Store in Redis
            alert_key = f"tv_alert:{alert.symbol}:{alert.timestamp.isoformat()}"
            self.redis.setex(alert_key, 86400, pickle.dumps(alert))
            
            # Process alert
            await self.process_alert(alert)
            
            logger.info(f"Received TradingView alert: {alert.symbol} - {alert.action} at {alert.price}")
            
            return web.Response(text="OK", status=200)
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return web.Response(text=f"Error: {str(e)}", status=400)
    
    async def process_alert(self, alert: TradingViewAlert):
        """Process incoming alert"""
        # Notify all registered handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
    
    def register_alert_handler(self, handler):
        """Register a handler for alerts"""
        self.alert_handlers.append(handler)
    
    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.Response(text="OK", status=200)
    
    async def start(self):
        """Start the webhook server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        logger.info(f"TradingView webhook server started on port {self.port}")


class TradingViewDataImporter:
    """Import data exported from TradingView"""
    
    def __init__(self):
        self.data_dir = "data/tradingview"
        os.makedirs(self.data_dir, exist_ok=True)
        
    def import_csv(self, filepath: str, symbol: str = None) -> TradingViewData:
        """Import TradingView CSV export"""
        # Read CSV
        df = pd.read_csv(filepath)
        
        # TradingView CSV format typically has:
        # time, open, high, low, close, volume
        
        # Rename columns to standard format
        column_mapping = {
            'time': 'timestamp',
            'Time': 'timestamp',
            'Date': 'timestamp',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }
        
        df.rename(columns=column_mapping, inplace=True)
        
        # Convert timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        
        # Detect symbol from filename if not provided
        if not symbol:
            symbol = os.path.basename(filepath).split('_')[0]
        
        # Detect timeframe
        timeframe = self.detect_timeframe(df)
        
        # Identify indicator columns
        base_columns = ['open', 'high', 'low', 'close', 'volume']
        indicator_columns = [col for col in df.columns if col not in base_columns]
        
        return TradingViewData(
            symbol=symbol,
            timeframe=timeframe,
            data=df,
            indicators=indicator_columns
        )
    
    def detect_timeframe(self, df: pd.DataFrame) -> str:
        """Detect timeframe from data frequency"""
        if len(df) < 2:
            return "unknown"
        
        # Calculate average time difference
        time_diffs = df.index.to_series().diff().dropna()
        avg_diff = time_diffs.mean()
        
        # Map to standard timeframes
        if avg_diff <= timedelta(minutes=1):
            return "1m"
        elif avg_diff <= timedelta(minutes=5):
            return "5m"
        elif avg_diff <= timedelta(minutes=15):
            return "15m"
        elif avg_diff <= timedelta(minutes=30):
            return "30m"
        elif avg_diff <= timedelta(hours=1):
            return "1h"
        elif avg_diff <= timedelta(hours=4):
            return "4h"
        elif avg_diff <= timedelta(days=1):
            return "1d"
        else:
            return "1w"
    
    def process_tradingview_export(self, filepath: str) -> Dict:
        """Process a TradingView export and prepare for backtesting"""
        tv_data = self.import_csv(filepath)
        
        # Add standard technical indicators if not present
        df = tv_data.data
        
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        
        # Add basic indicators if missing
        if 'sma_20' not in df.columns:
            df['sma_20'] = df['close'].rolling(window=20).mean()
        
        if 'sma_50' not in df.columns:
            df['sma_50'] = df['close'].rolling(window=50).mean()
        
        if 'rsi' not in df.columns:
            df['rsi'] = self.calculate_rsi(df['close'])
        
        # Save processed data
        output_file = os.path.join(
            self.data_dir,
            f"{tv_data.symbol}_{tv_data.timeframe}_processed.pkl"
        )
        
        with open(output_file, 'wb') as f:
            pickle.dump(df, f)
        
        return {
            'symbol': tv_data.symbol,
            'timeframe': tv_data.timeframe,
            'data_points': len(df),
            'date_range': f"{df.index[0]} to {df.index[-1]}",
            'indicators': list(df.columns),
            'output_file': output_file
        }
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))


class TradingViewStrategyBridge:
    """Bridge between TradingView strategies and the trading bot"""
    
    def __init__(self, swarm_coordinator):
        self.swarm = swarm_coordinator
        self.webhook_server = TradingViewWebhookServer()
        self.data_importer = TradingViewDataImporter()
        self.active_positions = {}
        
        # Register alert handler
        self.webhook_server.register_alert_handler(self.handle_trading_alert)
    
    async def handle_trading_alert(self, alert: TradingViewAlert):
        """Handle trading alert from TradingView"""
        logger.info(f"Processing TradingView alert: {alert.action} {alert.symbol} at {alert.price}")
        
        # Convert TradingView alert to swarm signal
        signal = {
            'timestamp': alert.timestamp,
            'symbol': alert.symbol,
            'action': self.convert_action(alert.action),
            'price': alert.price,
            'confidence': self.calculate_confidence(alert),
            'source': f"TradingView:{alert.strategy_name}",
            'timeframe': alert.timeframe,
            'indicators': alert.indicators
        }
        
        # Send to swarm for execution
        await self.swarm.process_external_signal(signal)
        
        # Track position
        if alert.action in ['buy', 'long']:
            self.active_positions[alert.symbol] = {
                'entry_price': alert.price,
                'entry_time': alert.timestamp,
                'strategy': alert.strategy_name
            }
        elif alert.action in ['sell', 'close']:
            if alert.symbol in self.active_positions:
                entry = self.active_positions[alert.symbol]
                profit = (alert.price - entry['entry_price']) / entry['entry_price']
                logger.info(f"Position closed: {alert.symbol} - Profit: {profit:.2%}")
                del self.active_positions[alert.symbol]
    
    def convert_action(self, tv_action: str) -> str:
        """Convert TradingView action to swarm action"""
        action_map = {
            'buy': 'BUY',
            'long': 'BUY',
            'sell': 'SELL',
            'short': 'SELL',
            'close': 'CLOSE',
            'exit': 'CLOSE'
        }
        return action_map.get(tv_action.lower(), 'HOLD')
    
    def calculate_confidence(self, alert: TradingViewAlert) -> float:
        """Calculate confidence score from TradingView alert"""
        # Base confidence
        confidence = 0.7
        
        # Adjust based on indicators
        if 'rsi' in alert.indicators:
            rsi = alert.indicators['rsi']
            if (alert.action == 'buy' and rsi < 30) or (alert.action == 'sell' and rsi > 70):
                confidence += 0.1
        
        if 'volume' in alert.indicators:
            # High volume increases confidence
            confidence += 0.1
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    async def start(self):
        """Start the TradingView bridge"""
        await self.webhook_server.start()
        logger.info("TradingView Strategy Bridge started")


# Pine Script Generator for TradingView
class PineScriptGenerator:
    """Generate Pine Script code for TradingView"""
    
    @staticmethod
    def generate_webhook_strategy(strategy_name: str, webhook_url: str) -> str:
        """Generate a Pine Script strategy that sends webhooks"""
        return f'''
//@version=5
strategy("{strategy_name}", overlay=true, pyramiding=1)

// Input parameters
fast_length = input.int(12, "Fast EMA Length")
slow_length = input.int(26, "Slow EMA Length")
rsi_length = input.int(14, "RSI Length")
rsi_oversold = input.int(30, "RSI Oversold")
rsi_overbought = input.int(70, "RSI Overbought")

// Calculate indicators
fast_ema = ta.ema(close, fast_length)
slow_ema = ta.ema(close, slow_length)
rsi = ta.rsi(close, rsi_length)
volume_sma = ta.sma(volume, 20)

// Entry conditions
long_condition = ta.crossover(fast_ema, slow_ema) and rsi < rsi_oversold and volume > volume_sma
short_condition = ta.crossunder(fast_ema, slow_ema) and rsi > rsi_overbought and volume > volume_sma

// Exit conditions
long_exit = rsi > rsi_overbought or ta.crossunder(fast_ema, slow_ema)
short_exit = rsi < rsi_oversold or ta.crossover(fast_ema, slow_ema)

// Webhook message
webhook_message = '{{"symbol": "' + syminfo.ticker + '", "action": "{{{{strategy.order.action}}}}", "price": {{{{strategy.order.price}}}}, "timeframe": "' + timeframe.period + '", "strategy": "{strategy_name}", "indicators": {{"rsi": ' + str.tostring(rsi) + ', "volume_ratio": ' + str.tostring(volume/volume_sma) + '}}}}'

// Strategy logic
if (long_condition)
    strategy.entry("Long", strategy.long, alert_message=webhook_message)
    
if (short_condition)
    strategy.entry("Short", strategy.short, alert_message=webhook_message)
    
if (long_exit and strategy.position_size > 0)
    strategy.close("Long", alert_message=webhook_message)
    
if (short_exit and strategy.position_size < 0)
    strategy.close("Short", alert_message=webhook_message)

// Plot indicators
plot(fast_ema, color=color.blue, title="Fast EMA")
plot(slow_ema, color=color.red, title="Slow EMA")

// Plot signals
plotshape(long_condition, style=shape.triangleup, location=location.belowbar, color=color.green, size=size.small)
plotshape(short_condition, style=shape.triangledown, location=location.abovebar, color=color.red, size=size.small)
'''

    @staticmethod
    def generate_multi_timeframe_strategy() -> str:
        """Generate a multi-timeframe Pine Script strategy"""
        return '''
//@version=5
indicator("Multi-Timeframe Crypto Strategy", overlay=true)

// Timeframe inputs
tf1 = input.timeframe("15", "Timeframe 1")
tf2 = input.timeframe("60", "Timeframe 2")
tf3 = input.timeframe("240", "Timeframe 3")

// Get data from multiple timeframes
close_tf1 = request.security(syminfo.tickerid, tf1, close)
close_tf2 = request.security(syminfo.tickerid, tf2, close)
close_tf3 = request.security(syminfo.tickerid, tf3, close)

rsi_tf1 = request.security(syminfo.tickerid, tf1, ta.rsi(close, 14))
rsi_tf2 = request.security(syminfo.tickerid, tf2, ta.rsi(close, 14))

// Multi-timeframe analysis
trend_tf2 = close_tf2 > ta.sma(close_tf2, 50)
trend_tf3 = close_tf3 > ta.sma(close_tf3, 200)

// Confluence signals
buy_signal = rsi_tf1 < 30 and trend_tf2 and trend_tf3
sell_signal = rsi_tf1 > 70 and not trend_tf2

// Plot signals
bgcolor(buy_signal ? color.new(color.green, 90) : na)
bgcolor(sell_signal ? color.new(color.red, 90) : na)

// Alert conditions
alertcondition(buy_signal, title="MTF Buy Signal", message="Multi-timeframe buy signal detected")
alertcondition(sell_signal, title="MTF Sell Signal", message="Multi-timeframe sell signal detected")
'''


# Example usage functions
async def setup_tradingview_integration():
    """Setup TradingView integration"""
    # 1. Start webhook server
    webhook_server = TradingViewWebhookServer(port=8080)
    await webhook_server.start()
    
    # 2. Generate Pine Script
    pine_script = PineScriptGenerator.generate_webhook_strategy(
        "CryptoSwarmStrategy",
        "http://your-server:8080/webhook/tradingview"
    )
    
    # Save Pine Script
    with open("tradingview_strategy.pine", "w") as f:
        f.write(pine_script)
    
    logger.info("TradingView integration setup complete")
    logger.info("1. Copy the Pine Script to TradingView")
    logger.info("2. Set up alerts with webhook URL: http://your-server:8080/webhook/tradingview")
    logger.info("3. Export historical data as CSV for backtesting")
    
    return webhook_server


def process_tradingview_csv(csv_file: str):
    """Process a TradingView CSV export"""
    importer = TradingViewDataImporter()
    result = importer.process_tradingview_export(csv_file)
    
    logger.info(f"Processed TradingView data:")
    logger.info(f"  Symbol: {result['symbol']}")
    logger.info(f"  Timeframe: {result['timeframe']}")
    logger.info(f"  Data points: {result['data_points']}")
    logger.info(f"  Date range: {result['date_range']}")
    logger.info(f"  Saved to: {result['output_file']}")
    
    return result


if __name__ == "__main__":
    # Example: Start webhook server
    async def main():
        server = await setup_tradingview_integration()
        
        # Keep server running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
    
    asyncio.run(main())