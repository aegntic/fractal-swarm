import { useEffect, useRef, useCallback, useState } from 'react';
import { useTradingStore } from '@/store/trading';
import { getWebSocketManager, initializeWebSocket, WebSocketManager } from '@/lib/websocket';
import { WSConfig, WSMessage, ConnectionState } from '@/types/trading';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: string) => void;
  onMessage?: (message: WSMessage) => void;
}

interface UseWebSocketReturn {
  connectionState: ConnectionState;
  connect: () => void;
  disconnect: () => void;
  send: (message: any) => void;
  isConnected: boolean;
}

const DEFAULT_WS_CONFIG: WSConfig = {
  url: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
  reconnectInterval: 1000,
  maxReconnectAttempts: 10,
  heartbeatInterval: 30000,
  authToken: undefined // Will be set from auth context or localStorage
};

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const { 
    autoConnect = true, 
    onConnect, 
    onDisconnect, 
    onError,
    onMessage 
  } = options;

  const wsManagerRef = useRef<WebSocketManager | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  
  const { 
    connectionState, 
    setConnectionState, 
    handleWSMessage 
  } = useTradingStore();

  // Initialize WebSocket manager
  useEffect(() => {
    // Get auth token from localStorage or auth context
    const authToken = localStorage.getItem('authToken');
    
    const config: WSConfig = {
      ...DEFAULT_WS_CONFIG,
      authToken: authToken || undefined
    };

    try {
      wsManagerRef.current = initializeWebSocket(config);
    } catch (error) {
      console.error('[useWebSocket] Failed to initialize WebSocket:', error);
      setConnectionState({ 
        status: 'error', 
        error: 'Failed to initialize WebSocket',
        reconnectAttempts: 0 
      });
    }

    return () => {
      if (wsManagerRef.current) {
        wsManagerRef.current.disconnect();
        wsManagerRef.current = null;
      }
    };
  }, [setConnectionState]);

  // Set up message and connection handlers
  useEffect(() => {
    if (!wsManagerRef.current) return;

    // Subscribe to messages
    const unsubscribeMessage = wsManagerRef.current.subscribe((message) => {
      // Handle message in store
      handleWSMessage(message);
      
      // Call custom handler if provided
      if (onMessage) {
        onMessage(message);
      }
    });

    // Subscribe to connection state changes
    const unsubscribeConnection = wsManagerRef.current.onConnectionChange((state) => {
      setConnectionState(state);
      setIsConnected(state.status === 'connected');

      // Call lifecycle handlers
      if (state.status === 'connected' && onConnect) {
        onConnect();
      } else if (state.status === 'disconnected' && onDisconnect) {
        onDisconnect();
      } else if (state.status === 'error' && onError && state.error) {
        onError(state.error);
      }
    });

    return () => {
      unsubscribeMessage();
      unsubscribeConnection();
    };
  }, [handleWSMessage, setConnectionState, onConnect, onDisconnect, onError, onMessage]);

  // Auto-connect
  useEffect(() => {
    if (autoConnect && wsManagerRef.current) {
      wsManagerRef.current.connect();
    }
  }, [autoConnect]);

  // Connection control functions
  const connect = useCallback(() => {
    if (wsManagerRef.current) {
      wsManagerRef.current.connect();
    }
  }, []);

  const disconnect = useCallback(() => {
    if (wsManagerRef.current) {
      wsManagerRef.current.disconnect();
    }
  }, []);

  const send = useCallback((message: any) => {
    if (wsManagerRef.current) {
      wsManagerRef.current.send(message);
    } else {
      console.warn('[useWebSocket] Cannot send message - WebSocket not initialized');
    }
  }, []);

  return {
    connectionState,
    connect,
    disconnect,
    send,
    isConnected
  };
}

// Specialized hooks for specific data streams
export function useCloneUpdates(cloneId?: string) {
  const clones = useTradingStore(state => state.clones);
  const clone = cloneId ? clones.get(cloneId) : undefined;
  const allClones = Array.from(clones.values());
  
  return { clone, clones: allClones };
}

export function usePositions(cloneId?: string) {
  const positions = useTradingStore(state => state.positions);
  const allPositions = Array.from(positions.values());
  
  if (cloneId) {
    return allPositions.filter(p => p.cloneId === cloneId);
  }
  
  return allPositions;
}

export function useTrades(limit = 20) {
  const trades = useTradingStore(state => state.recentTrades);
  return trades.slice(0, limit);
}

export function useMEVOpportunities() {
  const opportunities = useTradingStore(state => state.mevOpportunities);
  return Array.from(opportunities.values());
}

export function useMarketData(symbol?: string) {
  const marketData = useTradingStore(state => state.marketData);
  
  if (symbol) {
    return marketData.get(symbol);
  }
  
  return Array.from(marketData.values());
}

export function useAlerts(severity?: 'low' | 'medium' | 'high' | 'critical') {
  const alerts = useTradingStore(state => state.alerts);
  const dismissAlert = useTradingStore(state => state.dismissAlert);
  
  const filteredAlerts = severity 
    ? alerts.filter(a => a.severity === severity)
    : alerts;
    
  return { alerts: filteredAlerts, dismissAlert };
}

export function useSwarmStats() {
  return useTradingStore(state => state.swarmStats);
}

export function usePerformanceHistory(hours = 24) {
  const history = useTradingStore(state => state.performanceHistory);
  const pointsToShow = hours * 60; // Assuming 1-minute intervals
  return history.slice(-pointsToShow);
}

// Connection status hook with retry functionality
export function useConnectionStatus() {
  const connectionState = useTradingStore(state => state.connectionState);
  const { connect, disconnect } = useWebSocket({ autoConnect: false });
  
  const retry = useCallback(() => {
    disconnect();
    setTimeout(connect, 100);
  }, [connect, disconnect]);
  
  return {
    ...connectionState,
    retry
  };
}