import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import {
  CloneMetrics,
  Position,
  Trade,
  MEVOpportunity,
  MarketData,
  SwarmStats,
  Alert,
  Performance,
  ConnectionState,
  WSMessage
} from '@/types/trading';

interface TradingState {
  // Connection state
  connectionState: ConnectionState;
  
  // Swarm data
  swarmStats: SwarmStats | null;
  clones: Map<string, CloneMetrics>;
  
  // Trading data
  positions: Map<string, Position>;
  recentTrades: Trade[];
  mevOpportunities: Map<string, MEVOpportunity>;
  
  // Market data
  marketData: Map<string, MarketData>;
  
  // System data
  alerts: Alert[];
  performanceHistory: Performance[];
  
  // Actions
  setConnectionState: (state: ConnectionState) => void;
  updateSwarmStats: (stats: SwarmStats) => void;
  updateClone: (clone: CloneMetrics) => void;
  removeClone: (cloneId: string) => void;
  updatePosition: (position: Position) => void;
  removePosition: (positionId: string) => void;
  addTrade: (trade: Trade) => void;
  updateMEVOpportunity: (opportunity: MEVOpportunity) => void;
  removeMEVOpportunity: (opportunityId: string) => void;
  updateMarketData: (data: MarketData) => void;
  addAlert: (alert: Alert) => void;
  dismissAlert: (alertId: string) => void;
  addPerformanceData: (data: Performance) => void;
  handleWSMessage: (message: WSMessage) => void;
  reset: () => void;
}

const MAX_TRADES = 100;
const MAX_ALERTS = 50;
const MAX_PERFORMANCE_HISTORY = 1440; // 24 hours at 1-minute intervals

export const useTradingStore = create<TradingState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        connectionState: { status: 'disconnected', reconnectAttempts: 0 },
        swarmStats: null,
        clones: new Map(),
        positions: new Map(),
        recentTrades: [],
        mevOpportunities: new Map(),
        marketData: new Map(),
        alerts: [],
        performanceHistory: [],

        // Connection actions
        setConnectionState: (state) => set({ connectionState: state }),

        // Swarm actions
        updateSwarmStats: (stats) => set({ swarmStats: stats }),

        updateClone: (clone) => set((state) => {
          const clones = new Map(state.clones);
          clones.set(clone.id, clone);
          return { clones };
        }),

        removeClone: (cloneId) => set((state) => {
          const clones = new Map(state.clones);
          clones.delete(cloneId);
          
          // Also remove positions for this clone
          const positions = new Map(state.positions);
          for (const [id, position] of positions) {
            if (position.cloneId === cloneId) {
              positions.delete(id);
            }
          }
          
          return { clones, positions };
        }),

        // Position actions
        updatePosition: (position) => set((state) => {
          const positions = new Map(state.positions);
          positions.set(position.id, position);
          return { positions };
        }),

        removePosition: (positionId) => set((state) => {
          const positions = new Map(state.positions);
          positions.delete(positionId);
          return { positions };
        }),

        // Trade actions
        addTrade: (trade) => set((state) => {
          const trades = [trade, ...state.recentTrades].slice(0, MAX_TRADES);
          return { recentTrades: trades };
        }),

        // MEV actions
        updateMEVOpportunity: (opportunity) => set((state) => {
          const opportunities = new Map(state.mevOpportunities);
          opportunities.set(opportunity.id, opportunity);
          return { mevOpportunities: opportunities };
        }),

        removeMEVOpportunity: (opportunityId) => set((state) => {
          const opportunities = new Map(state.mevOpportunities);
          opportunities.delete(opportunityId);
          return { mevOpportunities: opportunities };
        }),

        // Market data actions
        updateMarketData: (data) => set((state) => {
          const marketData = new Map(state.marketData);
          marketData.set(data.symbol, data);
          return { marketData };
        }),

        // Alert actions
        addAlert: (alert) => set((state) => {
          const alerts = [alert, ...state.alerts].slice(0, MAX_ALERTS);
          return { alerts };
        }),

        dismissAlert: (alertId) => set((state) => ({
          alerts: state.alerts.filter(a => a.id !== alertId)
        })),

        // Performance actions
        addPerformanceData: (data) => set((state) => {
          const history = [...state.performanceHistory, data].slice(-MAX_PERFORMANCE_HISTORY);
          return { performanceHistory: history };
        }),

        // WebSocket message handler
        handleWSMessage: (message) => {
          const state = get();
          
          switch (message.type) {
            case 'clone_update':
              state.updateClone(message.data);
              break;
              
            case 'new_trade':
              state.addTrade(message.data);
              break;
              
            case 'position_update':
              state.updatePosition(message.data);
              break;
              
            case 'mev_opportunity':
              state.updateMEVOpportunity(message.data);
              break;
              
            case 'market_update':
              state.updateMarketData(message.data);
              break;
              
            case 'swarm_stats':
              state.updateSwarmStats(message.data);
              break;
              
            case 'alert':
              state.addAlert(message.data);
              break;
              
            case 'performance_update':
              state.addPerformanceData(message.data);
              break;
              
            case 'clone_spawned':
              // Handle clone spawning event if needed
              state.addAlert({
                id: `spawn-${Date.now()}`,
                type: 'success',
                severity: 'medium',
                title: 'Clone Spawned',
                message: `Clone ${message.data.childId} spawned from ${message.data.parentId} (Gen ${message.data.generation})`,
                timestamp: new Date().toISOString(),
                actionRequired: false
              });
              break;
              
            case 'error':
              state.addAlert({
                id: `error-${Date.now()}`,
                type: 'error',
                severity: 'high',
                title: 'System Error',
                message: message.data.message,
                timestamp: new Date().toISOString(),
                actionRequired: true,
                metadata: { code: message.data.code }
              });
              break;
          }
        },

        // Reset store
        reset: () => set({
          connectionState: { status: 'disconnected', reconnectAttempts: 0 },
          swarmStats: null,
          clones: new Map(),
          positions: new Map(),
          recentTrades: [],
          mevOpportunities: new Map(),
          marketData: new Map(),
          alerts: [],
          performanceHistory: []
        })
      }),
      {
        name: 'quantum-swarm-trading',
        // Only persist certain data
        partialize: (state) => ({
          alerts: state.alerts.slice(0, 10), // Keep last 10 alerts
          performanceHistory: state.performanceHistory.slice(-60) // Keep last hour
        })
      }
    )
  )
);

// Selectors
export const selectActiveClones = (state: TradingState) => 
  Array.from(state.clones.values()).filter(c => c.status === 'active');

export const selectOpenPositions = (state: TradingState) => 
  Array.from(state.positions.values());

export const selectPendingMEVs = (state: TradingState) => 
  Array.from(state.mevOpportunities.values()).filter(o => o.status === 'pending');

export const selectCriticalAlerts = (state: TradingState) => 
  state.alerts.filter(a => a.severity === 'critical' && a.actionRequired);

export const selectTotalPnL = (state: TradingState) => {
  const clones = Array.from(state.clones.values());
  return clones.reduce((total, clone) => total + clone.pnl, 0);
};

export const selectTotalCapital = (state: TradingState) => {
  const clones = Array.from(state.clones.values());
  return clones.reduce((total, clone) => total + clone.capital, 0);
};