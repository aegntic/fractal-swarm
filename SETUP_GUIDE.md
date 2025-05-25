# 🚀 Quantum Swarm Trader - Setup Guide

## Overview

The Quantum Swarm Trader is now enhanced with **Solana Agent Kit** integration and **MegaETH** cross-chain support. This guide will help you set up and run the system.

## Prerequisites

- Python 3.9+
- Redis server
- Node.js 16+ (for some dependencies)
- Solana CLI tools (optional but recommended)
- 100+ SOL for initial trading capital
- VPS or cloud server for 24/7 operation

## Quick Start

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/your-repo/crypto-swarm-trader.git
cd crypto-swarm-trader

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
# Solana Configuration
SOLANA_PRIVATE_KEY=your_base58_private_key_here
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_DEVNET_URL=https://api.devnet.solana.com

# API Keys
OPENAI_API_KEY=your_openai_key_here  # Required for Solana Agent Kit
HELIUS_API_KEY=your_helius_key_here  # Optional for better RPC
BIRDEYE_API_KEY=your_birdeye_key_here  # Optional for market data

# MegaETH Configuration (when available)
MEGAETH_RPC_URL=https://rpc.megaeth.com
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Exchange APIs (optional)
BINANCE_API_KEY=your_key
BINANCE_SECRET=your_secret
```

### 3. Start Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# Or install locally
sudo apt-get install redis-server
redis-server
```

### 4. Initialize the Swarm

```bash
# Initialize with your Solana wallet
python quantum_main.py init

# Or use testnet for testing
python quantum_main.py init --testnet
```

### 5. Start Trading

```bash
# Start the quantum swarm trader
python quantum_main.py start

# Start with dashboard
python quantum_main.py start --dashboard
```

## Detailed Configuration

### Solana Wallet Setup

1. **Generate a new wallet** (if needed):
```bash
solana-keygen new --outfile ~/quantum-swarm-wallet.json
```

2. **Get the base58 private key**:
```python
import json
import base58

# Load the keypair file
with open('~/quantum-swarm-wallet.json', 'r') as f:
    keypair = json.load(f)

# Convert to base58
private_key = base58.b58encode(bytes(keypair[:32])).decode()
print(private_key)
```

3. **Fund the wallet** with at least 1 SOL for operations + your trading capital

### Strategy Configuration

Edit `config_solana.py` to customize:

- Clone spawning thresholds
- Maximum number of clones
- Strategy specializations
- Risk parameters

### Advanced Features

#### 1. Manual Clone Spawning
```bash
python quantum_main.py clone
```

#### 2. Strategy Management
```bash
# View all strategies
python quantum_main.py strategies

# View specific strategy
python quantum_main.py strategies --strategy mev
```

#### 3. Interactive Mode
```bash
python quantum_main.py interactive
```

## Architecture Overview

### Core Components

1. **Quantum Swarm Coordinator** (`quantum_swarm_coordinator.py`)
   - Master orchestrator for all operations
   - Manages cross-chain coordination
   - Implements quantum decision engine

2. **Solana Agent Wrapper** (`solana_agent_wrapper.py`)
   - Integrates Solana Agent Kit
   - Manages Solana-specific operations
   - Handles clone spawning on Solana

3. **Fractal Clone System**
   - Self-replicating agents with behavioral mutations
   - Anti-detection through randomization
   - Specialized roles (MEV, arbitrage, liquidity)

### Trading Phases

1. **Phase 1: MICRO ($100 → $1,000)**
   - MEV hunting on Solana using Jito
   - Micro arbitrage between Raydium/Orca/Jupiter
   - High-frequency trading with small positions

2. **Phase 2: GROWTH ($1,000 → $10,000)**
   - Cross-chain arbitrage (Solana ↔ Ethereum)
   - Flash loan cascading
   - Social momentum trading

3. **Phase 3: SCALE ($10,000 → $100,000)**
   - Market making on multiple DEXs
   - Yield optimization across protocols
   - Portfolio diversification

## Monitoring & Management

### Dashboard

Access the web dashboard at `http://localhost:8501` when running with `--dashboard` flag.

### Logs

```bash
# View logs
python quantum_main.py logs

# Follow logs in real-time
python quantum_main.py logs --tail
```

### Status Checking

```bash
# Check swarm status
python quantum_main.py status
```

## Safety Features

1. **Stop Loss**: Automatic position closing at -5% (Phase 1)
2. **Daily Drawdown Limit**: Max 15% daily loss (Phase 1)
3. **Clone Collision Prevention**: Redis-based atomic locking
4. **Exchange Detection Avoidance**: Behavioral randomization

## Troubleshooting

### Common Issues

1. **"No Solana private key provided"**
   - Ensure `SOLANA_PRIVATE_KEY` is set in `.env`
   - Check the key is valid base58 format

2. **"Redis connection refused"**
   - Ensure Redis is running: `redis-cli ping`
   - Check Redis host/port in `.env`

3. **"Insufficient SOL balance"**
   - Fund your wallet with at least 1 SOL for operations
   - Check balance: `solana balance <your-wallet-address>`

### Performance Optimization

1. **Use premium RPC endpoints** (Helius, QuickNode) for better performance
2. **Distribute clones across multiple RPC endpoints** to avoid rate limits
3. **Monitor Redis memory usage** and configure accordingly

## Security Considerations

1. **Never share your private keys**
2. **Use a dedicated wallet** for the trading system
3. **Set up monitoring alerts** for unusual activity
4. **Regular backups** of swarm state

## Next Steps

1. **Test on Devnet** first to ensure everything works
2. **Start with small capital** ($100-500) to validate strategies
3. **Monitor closely** for the first 48 hours
4. **Join our Discord** for support and updates

## Support

- Discord: [Join our server]
- GitHub Issues: [Report bugs]
- Documentation: [Full docs]

---

**⚠️ DISCLAIMER**: Trading cryptocurrencies involves substantial risk. Only trade with funds you can afford to lose. Past performance does not guarantee future results.