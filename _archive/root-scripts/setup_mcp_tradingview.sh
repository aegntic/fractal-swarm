#!/bin/bash
# Setup script for TradingView MCP Server

echo "Setting up TradingView MCP Server..."

# Install required dependencies
pip install mcp playwright pydantic

# Install Playwright browsers
playwright install chromium

# Create environment file template
cat > .env.tradingview << EOF
# TradingView Credentials
TRADINGVIEW_USERNAME=your_email@example.com
TRADINGVIEW_PASSWORD=your_password

# Optional: Webhook secret for additional security
TRADINGVIEW_WEBHOOK_SECRET=your_secret_key
EOF

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env.tradingview with your TradingView credentials"
echo "2. Copy mcp-config.json to your Claude Desktop config directory:"
echo "   - Mac: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "   - Windows: %APPDATA%/Claude/claude_desktop_config.json"
echo "3. Restart Claude Desktop"
echo ""
echo "You'll then be able to use TradingView tools directly in Claude!"
echo ""
echo "Example usage:"
echo "  - Get BTC chart data: Use tradingview_get_chart_data tool"
echo "  - Check RSI values: Use tradingview_get_indicator tool"
echo "  - Test strategies: Use tradingview_execute_strategy tool"
echo "  - Monitor watchlists: Use tradingview_get_watchlist tool"