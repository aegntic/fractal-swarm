"""
FastAPI Backend for Quantum Swarm Trader
Provides REST API and WebSocket endpoints
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import json
import redis.asyncio as aioredis
from decimal import Decimal
import jwt
from passlib.context import CryptContext

# For production, these would import the real coordinator
# from quantum_swarm_coordinator import QuantumSwarmCoordinator

app = FastAPI(title="Quantum Swarm Trader API", version="1.0.0")

# CORS for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key-here"  # Use env var in production
ALGORITHM = "HS256"

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Mock data for development
class MockSwarmCoordinator:
    def __init__(self):
        self.capital = 1234.56
        self.clones = 12
        self.phase = "GROWTH"
        
    async def get_status(self):
        return {
            "total_capital": self.capital,
            "trading_phase": self.phase,
            "total_clones": self.clones,
            "solana_clones": 8,
            "ethereum_clones": 4,
            "profit_tracker": {
                "total_trades": 1847,
                "winning_trades": 1352,
                "win_rate": 0.732,
                "total_profit": 234.56,
            },
            "quantum_state": {
                "active_superpositions": 42,
                "decisions_made": 1523,
            }
        }
    
    async def get_clone_list(self):
        clones = []
        for i in range(self.clones):
            clones.append({
                "id": f"clone_{i+1}",
                "chain": "solana" if i < 8 else "ethereum",
                "specialization": ["MEV Hunter", "Arbitrage", "Liquidity", "Social"][i % 4],
                "generation": (i // 4) + 1,
                "balance": 50 + (i * 10),
                "trades_count": 100 + (i * 20),
                "profit": -10 + (i * 5),
                "status": "active" if i % 3 != 0 else "idle",
                "spawn_time": datetime.now().isoformat(),
            })
        return clones

# Initialize mock coordinator
coordinator = MockSwarmCoordinator()

# Pydantic models
class SwarmStatus(BaseModel):
    total_capital: float
    trading_phase: str
    total_clones: int
    solana_clones: int
    ethereum_clones: int
    profit_tracker: Dict[str, Any]
    quantum_state: Dict[str, Any]

class CloneInfo(BaseModel):
    id: str
    chain: str
    specialization: str
    generation: int
    balance: float
    trades_count: int
    profit: float
    status: str
    spawn_time: str

class TradeInfo(BaseModel):
    id: str
    timestamp: str
    clone_id: str
    pair: str
    type: str  # MEV, ARB, SWAP
    side: str  # BUY, SELL
    amount: float
    price: float
    profit: float
    gas_cost: float
    chain: str
    tx_hash: str

class SpawnCloneRequest(BaseModel):
    capital_allocation: float
    specialization: Optional[str] = None
    chain: str = "solana"

class StrategyUpdate(BaseModel):
    strategy_name: str
    weight: float

class EmergencyStopRequest(BaseModel):
    reason: str
    liquidate: bool = False

# Authentication endpoints
@app.post("/api/auth/login")
async def login(username: str, password: str):
    # Mock authentication
    if username == "admin" and password == "quantum":
        token = jwt.encode(
            {"sub": username, "exp": datetime.utcnow().timestamp() + 86400},
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# API endpoints
@app.get("/api/status", response_model=SwarmStatus)
async def get_status():
    """Get current swarm status"""
    return await coordinator.get_status()

@app.get("/api/clones", response_model=List[CloneInfo])
async def get_clones():
    """Get list of all active clones"""
    return await coordinator.get_clone_list()

@app.get("/api/clones/{clone_id}")
async def get_clone_details(clone_id: str):
    """Get detailed information about a specific clone"""
    clones = await coordinator.get_clone_list()
    for clone in clones:
        if clone["id"] == clone_id:
            return clone
    raise HTTPException(status_code=404, detail="Clone not found")

@app.get("/api/trades")
async def get_trades(limit: int = 100, clone_id: Optional[str] = None):
    """Get recent trades"""
    # Mock trade data
    trades = []
    import random
    
    for i in range(limit):
        trades.append({
            "id": f"trade_{i}",
            "timestamp": datetime.now().isoformat(),
            "clone_id": clone_id or f"clone_{random.randint(1, 12)}",
            "pair": ["SOL/USDC", "ETH/USDC", "RAY/USDC"][i % 3],
            "type": ["MEV", "ARB", "SWAP"][i % 3],
            "side": ["BUY", "SELL"][i % 2],
            "amount": 100 + (i * 10),
            "price": 100.5 + (i * 0.1),
            "profit": -2 + (i * 0.5),
            "gas_cost": 0.01 + (i * 0.001),
            "chain": ["solana", "ethereum"][i % 2],
            "tx_hash": f"0x{'a' * 64}",
        })
    
    return trades

@app.post("/api/clones/spawn")
async def spawn_clone(request: SpawnCloneRequest):
    """Manually spawn a new clone"""
    # In production, this would call coordinator.spawn_clone()
    return {
        "success": True,
        "clone_id": f"clone_{coordinator.clones + 1}",
        "message": f"Clone spawned with {request.capital_allocation} capital"
    }

@app.put("/api/strategies/{strategy_name}")
async def update_strategy(strategy_name: str, update: StrategyUpdate):
    """Update strategy weights"""
    return {
        "success": True,
        "strategy": strategy_name,
        "new_weight": update.weight,
        "message": "Strategy updated successfully"
    }

@app.post("/api/emergency-stop")
async def emergency_stop(request: EmergencyStopRequest):
    """Emergency stop all trading"""
    # In production, this would trigger actual emergency stop
    return {
        "success": True,
        "stopped_at": datetime.now().isoformat(),
        "reason": request.reason,
        "clones_stopped": coordinator.clones,
        "positions_closed": 0 if not request.liquidate else 23
    }

@app.get("/api/performance/history")
async def get_performance_history(period: str = "24h"):
    """Get historical performance data"""
    # Mock performance data
    data_points = []
    import random
    
    points = 24 if period == "24h" else 168 if period == "7d" else 720
    base_capital = 1000
    
    for i in range(points):
        base_capital *= (1 + random.uniform(-0.02, 0.03))
        data_points.append({
            "timestamp": datetime.now().timestamp() - (points - i) * 3600,
            "capital": base_capital,
            "trades": random.randint(10, 50),
            "clones": min(12, 1 + i // 10),
        })
    
    return data_points

@app.get("/api/alerts")
async def get_alerts():
    """Get active alerts and notifications"""
    return [
        {
            "id": "alert_1",
            "type": "info",
            "message": "Clone spawn threshold reached",
            "timestamp": datetime.now().isoformat(),
        },
        {
            "id": "alert_2", 
            "type": "warning",
            "message": "High gas fees on Ethereum",
            "timestamp": datetime.now().isoformat(),
        }
    ]

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            # Send updates every second
            status = await coordinator.get_status()
            await manager.send_personal_message(
                json.dumps({
                    "type": "status_update",
                    "data": status,
                    "timestamp": datetime.now().isoformat()
                }),
                websocket
            )
            
            # Also send trade updates
            if asyncio.get_event_loop().time() % 5 < 1:  # Every 5 seconds
                await manager.send_personal_message(
                    json.dumps({
                        "type": "new_trade",
                        "data": {
                            "clone_id": "clone_3",
                            "pair": "SOL/USDC",
                            "profit": 2.34,
                            "timestamp": datetime.now().isoformat()
                        }
                    }),
                    websocket
                )
            
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Metrics endpoint for monitoring
@app.get("/metrics")
async def get_metrics():
    """Prometheus-style metrics"""
    metrics = f"""
# HELP swarm_total_capital Total capital under management
# TYPE swarm_total_capital gauge
swarm_total_capital {coordinator.capital}

# HELP swarm_active_clones Number of active clones
# TYPE swarm_active_clones gauge
swarm_active_clones {coordinator.clones}

# HELP swarm_trades_total Total number of trades executed
# TYPE swarm_trades_total counter
swarm_trades_total 1847

# HELP swarm_win_rate Current win rate
# TYPE swarm_win_rate gauge
swarm_win_rate 0.732
"""
    return metrics


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)