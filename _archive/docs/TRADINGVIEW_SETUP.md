# TradingView Integration Setup Guide

This guide explains how to integrate your TradingView Premium account with the Crypto Swarm Trader.

## Overview

The integration provides three main features:
1. **Real-time Alerts**: Receive trading signals from TradingView strategies
2. **Historical Data Import**: Use TradingView's premium data for backtesting
3. **Strategy Synchronization**: Run TradingView strategies alongside the swarm

## Setup Steps

### 1. Webhook Server Setup

First, start the webhook server to receive TradingView alerts:

```bash
# Start the webhook server
python tradingview_webhook_server.py
```

The server will run on port 8080 by default. For production, use a reverse proxy (nginx) with SSL.

### 2. TradingView Strategy Setup

#### Option A: Use the Generated Pine Script

1. Copy the generated Pine Script:
```bash
cat tradingview_strategy.pine
```

2. In TradingView:
   - Open Pine Editor
   - Paste the script
   - Click "Add to Chart"
   - Configure the strategy parameters

#### Option B: Modify Your Existing Strategy

Add webhook alerts to your existing Pine Script:

```pine
// Add this to your strategy
webhook_message = '{"symbol": "' + syminfo.ticker + '", "action": "' + action + '", "price": ' + str.tostring(close) + '}'

// In your entry/exit conditions
if (buy_condition)
    strategy.entry("Long", strategy.long, alert_message=webhook_message)
```

### 3. Create Alerts

1. Right-click on your strategy in TradingView
2. Select "Add Alert"
3. Configure:
   - **Condition**: Your strategy
   - **Alert actions**: Webhook URL
   - **Webhook URL**: `http://your-server:8080/webhook/tradingview`
   - **Message**: Leave as `{{strategy.order.alert_message}}`

### 4. Export Historical Data

With TradingView Premium, you can export historical data:

1. Open the chart with your desired symbol and timeframe
2. Click the "Export" button (or use Alt+Shift+E)
3. Select "Export chart data"
4. Save the CSV file

### 5. Import Data to Swarm Trader

```bash
# Import TradingView CSV data
python import_tradingview_data.py --file BTCUSDT_1h.csv

# Or use the Python API
from tradingview_integration import process_tradingview_csv
process_tradingview_csv("BTCUSDT_1h.csv")
```

## Advanced Configuration

### Multi-Timeframe Analysis

The system supports multi-timeframe strategies. Configure in TradingView:

```pine
// Request data from multiple timeframes
htf_close = request.security(syminfo.tickerid, "240", close)
ltf_rsi = request.security(syminfo.tickerid, "15", ta.rsi(close, 14))
```

### Custom Indicators

Export custom indicator values in the webhook:

```pine
webhook_message = '{"symbol": "' + syminfo.ticker + '", ' + 
                  '"action": "buy", ' +
                  '"indicators": {' +
                  '"custom_indicator": ' + str.tostring(my_indicator) + ', ' +
                  '"trend_strength": ' + str.tostring(trend_value) + '}}'
```

### Security

1. **Webhook Authentication**: Set a secret key:
```bash
export TRADINGVIEW_WEBHOOK_SECRET="your-secret-key"
```

2. **HTTPS**: Use SSL certificate for production:
```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /webhook {
        proxy_pass http://localhost:8080;
    }
}
```

## Data Flow

1. **TradingView** → Generates signal based on strategy
2. **Webhook** → Sends alert to your server
3. **Integration Module** → Processes and validates signal
4. **Swarm Coordinator** → Executes trade through best available agent
5. **Performance Tracker** → Records results

## Best Practices

### 1. Strategy Alignment
- Ensure TradingView strategies complement swarm strategies
- Use TradingView for technical analysis, swarm for execution

### 2. Risk Management
- Set position size limits in both systems
- Use TradingView alerts as signals, not direct orders

### 3. Backtesting
- Test strategies with historical data before live trading
- Compare TradingView backtest results with swarm results

### 4. Monitoring
- Set up alerts for webhook failures
- Monitor execution latency
- Track signal accuracy

## Troubleshooting

### Webhook Not Receiving Alerts
1. Check firewall settings
2. Verify webhook URL in TradingView
3. Check server logs: `tail -f logs/webhook.log`

### Data Import Issues
1. Ensure CSV format matches expected columns
2. Check date/time format
3. Verify symbol naming convention

### Performance Issues
1. Use Redis for caching
2. Limit concurrent webhook processing
3. Optimize Pine Script calculations

## Example Integration Flow

```python
# Start the complete integration
import asyncio
from tradingview_integration import TradingViewStrategyBridge
from swarm_coordinator import SwarmCoordinator

async def main():
    # Initialize swarm
    swarm = SwarmCoordinator()
    await swarm.initialize()
    
    # Setup TradingView bridge
    tv_bridge = TradingViewStrategyBridge(swarm)
    await tv_bridge.start()
    
    # System is now ready to receive TradingView signals
    logger.info("TradingView integration active")
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

1. Test with paper trading first
2. Start with small position sizes
3. Monitor performance metrics
4. Adjust strategies based on results
5. Scale up gradually

For support, check the logs in `logs/tradingview/` or run diagnostics:
```bash
python check_tradingview_connection.py
```