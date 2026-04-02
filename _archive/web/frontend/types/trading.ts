// Real-time trading data types for Quantum Swarm Trader

export interface CloneMetrics {
  id: string;
  generation: number;
  status: 'active' | 'idle' | 'spawning' | 'error';
  capital: number;
  pnl: number;
  pnlPercentage: number;
  winRate: number;
  totalTrades: number;
  currentPositions: Position[];
  strategy: string;
  lastUpdate: string;
  health: {
    cpu: number;
    memory: number;
    latency: number;
  };
}

export interface Position {
  id: string;
  cloneId: string;
  symbol: string;
  side: 'long' | 'short';
  size: number;
  entryPrice: number;
  currentPrice: number;
  unrealizedPnl: number;
  unrealizedPnlPercentage: number;
  stopLoss: number;
  takeProfit: number;
  openTime: string;
  exchange: string;
}

export interface Trade {
  id: string;
  cloneId: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit' | 'stop';
  price: number;
  quantity: number;
  fee: number;
  pnl?: number;
  timestamp: string;
  exchange: string;
  strategy: string;
  metadata?: Record<string, any>;
}

export interface MEVOpportunity {
  id: string;
  type: 'arbitrage' | 'sandwich' | 'liquidation' | 'frontrun';
  profitEstimate: number;
  gasEstimate: number;
  netProfit: number;
  confidence: number;
  deadline: string;
  status: 'pending' | 'executing' | 'completed' | 'failed';
  details: {
    chain: string;
    tokens: string[];
    protocols: string[];
    txHash?: string;
  };
}

export interface MarketData {
  symbol: string;
  price: number;
  volume24h: number;
  change24h: number;
  high24h: number;
  low24h: number;
  bid: number;
  ask: number;
  lastUpdate: string;
}

export interface SwarmStats {
  totalCapital: number;
  totalPnl: number;
  totalPnlPercentage: number;
  activeClones: number;
  totalClones: number;
  successRate: number;
  totalTrades: number;
  mevCaptured: number;
  gasSpent: number;
  uptime: number;
  generation: number;
}

export interface Alert {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  timestamp: string;
  cloneId?: string;
  actionRequired: boolean;
  metadata?: Record<string, any>;
}

export interface Performance {
  timestamp: string;
  capital: number;
  pnl: number;
  trades: number;
  winRate: number;
  sharpeRatio: number;
  maxDrawdown: number;
  cloneCount: number;
}

// WebSocket message types
export type WSMessage = 
  | { type: 'clone_update'; data: CloneMetrics }
  | { type: 'new_trade'; data: Trade }
  | { type: 'position_update'; data: Position }
  | { type: 'mev_opportunity'; data: MEVOpportunity }
  | { type: 'market_update'; data: MarketData }
  | { type: 'swarm_stats'; data: SwarmStats }
  | { type: 'alert'; data: Alert }
  | { type: 'performance_update'; data: Performance }
  | { type: 'clone_spawned'; data: { parentId: string; childId: string; generation: number } }
  | { type: 'error'; data: { message: string; code: string } };

export interface WSConfig {
  url: string;
  reconnectInterval: number;
  maxReconnectAttempts: number;
  heartbeatInterval: number;
  authToken?: string;
}

export interface ConnectionState {
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastConnected?: string;
  reconnectAttempts: number;
  error?: string;
}