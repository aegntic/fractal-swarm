# CLAUDE.md - Implementation Rules for Quantum Swarm Trader

## 🎯 PROJECT CONTEXT
You are implementing the Quantum Swarm Trader with Fractal Clone System - an autonomous crypto trading system that self-replicates to achieve exponential growth from $100 to $100,000+. This is a PRODUCTION system with REAL money at stake.

## ⚡ CORE PRINCIPLES

### 1. ZERO TOLERANCE FOR FAKE CODE
- **NEVER** write placeholder functions or mock data
- **ALWAYS** implement complete, working solutions
- **ALWAYS** handle real API responses and edge cases

### 2. PRODUCTION-FIRST MINDSET
Every function must:
- Connect to real exchanges/blockchains
- Handle actual money transactions
- Include comprehensive error handling
- Log all actions for audit trail
- Implement retry logic and fallbacks

### 3. SECURITY IS PARAMOUNT
- Store private keys in environment variables
- Use hardware security modules when possible
- Implement rate limiting on all endpoints
- Sanitize and validate all inputs
- Regular security audits required

## 📋 IMPLEMENTATION REQUIREMENTS

### Exchange Integration
```python
# Required for each exchange connection:
- API key management with encryption
- Rate limit tracking (per second/minute)
- Automatic retry with backoff
- Balance verification before trades
- Order status monitoring
- WebSocket connections for real-time data
```

### Risk Management
```python
# Mandatory for every trade:
- Position size validation (<20% of capital)
- Stop loss calculation and setting
- Daily loss limit checking
- Correlation analysis between positions
- Slippage estimation
- Gas cost pre-calculation
```
## 🔧 TECHNICAL PATTERNS

### Clone Spawning Pattern
```python
async def spawn_clone(parent_genetics, generation):
    # 1. Verify capital threshold met
    # 2. Generate unique clone ID
    # 3. Mutate parent strategies
    # 4. Deploy new Lambda function
    # 5. Register in swarm registry
    # 6. Initialize with capital allocation
    # 7. Start autonomous operation
```

### MEV Hunting Pattern  
```python
async def hunt_mev_opportunity():
    # 1. Monitor mempool via WebSocket
    # 2. Simulate transaction impact
    # 3. Calculate profit after gas
    # 4. Submit via Flashbots if profitable
    # 5. Monitor inclusion and success
```

### Capital Pooling Pattern
```python
async def request_swarm_capital(amount, opportunity):
    # 1. Check opportunity lock status
    # 2. Calculate expected profit
    # 3. Request from pool contract
    # 4. Execute trade with pooled capital
    # 5. Return capital + profit share
```

## ⚠️ CRITICAL RULES

1. **Real Money Mode Only**
   - Every trade uses actual capital
   - No paper trading or backtesting in production
   - All losses are real and permanent

2. **Distributed Architecture**
   - No single points of failure
   - Every clone can operate independently
   - Shared state via Redis, not local memory

3. **Continuous Operation**
   - System must run 24/7 without intervention
   - Automatic recovery from failures
   - Self-healing and adaptation

4. **Compliance First**
   - Log every transaction for taxes
   - Respect exchange terms of service
   - No wash trading or manipulation

## 📊 MONITORING REQUIREMENTS

### Real-Time Metrics
- Capital per clone and total
- Win rate by strategy
- MEV success rate
- Network fees vs profits
- Clone health status
- Error rates and types

### Alerts (Immediate Action)
- Capital loss >10% in 1 hour
- Clone failure rate >25%
- Exchange API errors
- Smart contract failures
- Unusual trading patterns
## 🚀 IMPLEMENTATION WORKFLOW

### When Starting a New Feature:
1. Review existing code in `/home/tabs/crypto-swarm-trader`
2. Check current infrastructure status
3. Verify all API keys and connections
4. Run integration tests before deployment
5. Monitor for 1 hour after deployment

### Code Standards:
```python
# Every file must include:
- Comprehensive docstrings
- Type hints for all functions
- Unit tests with >80% coverage
- Integration tests for external APIs
- Performance benchmarks
```

### Deployment Process:
1. Test on Polygon testnet first
2. Deploy with 10% of capital limit
3. Monitor for 24 hours
4. Gradually increase limits
5. Full deployment after 72 hours stable

## 💭 DECISION FRAMEWORK

When implementing ANY feature, ask:
1. **Is this using real infrastructure?** (No mocks)
2. **Can this handle $100K+?** (Scale ready)
3. **What happens if it fails?** (Graceful degradation)
4. **Is this detectable?** (Anti-pattern analysis)
5. **Can clones inherit this?** (Genetic compatibility)

## 🔴 ABSOLUTE PROHIBITIONS

**NEVER**:
- Use `time.sleep()` - Use async/await
- Store keys in code - Use environment variables
- Trust external data - Validate everything
- Assume success - Handle every error
- Create infinite loops - Use circuit breakers
- Make synchronous API calls - Always async
- Deploy untested code - Test on testnet first

## ✅ FINAL CHECKLIST

Before ANY commit:
- [ ] All functions handle real money
- [ ] Error handling is comprehensive  
- [ ] Logging provides full audit trail
- [ ] Tests cover edge cases
- [ ] Security best practices followed
- [ ] Documentation is complete
- [ ] Performance is optimized
- [ ] Clone inheritance considered

**Remember**: This system trades REAL MONEY autonomously. Every line of code must be production-grade, secure, and reliable. There are no second chances with other people's money.