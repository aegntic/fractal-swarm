import React from 'react';
import { 
  useWebSocket, 
  useCloneUpdates, 
  usePositions, 
  useTrades,
  useMEVOpportunities,
  useAlerts,
  useSwarmStats,
  useConnectionStatus
} from '@/hooks/useWebSocket';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function WebSocketExample() {
  // Main WebSocket connection
  const { isConnected, send } = useWebSocket({
    onConnect: () => console.log('WebSocket connected'),
    onDisconnect: () => console.log('WebSocket disconnected'),
    onError: (error) => console.error('WebSocket error:', error),
    onMessage: (message) => console.log('Received message:', message.type)
  });

  // Connection status with retry
  const connectionStatus = useConnectionStatus();

  // Data hooks
  const { clones } = useCloneUpdates();
  const positions = usePositions();
  const trades = useTrades(5);
  const mevOpportunities = useMEVOpportunities();
  const { alerts, dismissAlert } = useAlerts('high');
  const swarmStats = useSwarmStats();

  // Example: Send a command to a specific clone
  const sendCloneCommand = (cloneId: string, command: string) => {
    send({
      type: 'clone_command',
      data: {
        cloneId,
        command,
        timestamp: new Date().toISOString()
      }
    });
  };

  // Example: Request market data update
  const requestMarketUpdate = (symbol: string) => {
    send({
      type: 'market_data_request',
      data: { symbol }
    });
  };

  return (
    <div className="space-y-4 p-4">
      {/* Connection Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            WebSocket Connection
            <Badge variant={isConnected ? 'default' : 'destructive'}>
              {connectionStatus.status}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {connectionStatus.status === 'error' && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>
                {connectionStatus.error}
              </AlertDescription>
            </Alert>
          )}
          
          {connectionStatus.status === 'disconnected' && (
            <Button onClick={connectionStatus.retry} size="sm">
              Reconnect
            </Button>
          )}
          
          {connectionStatus.lastConnected && (
            <p className="text-sm text-muted-foreground">
              Last connected: {new Date(connectionStatus.lastConnected).toLocaleString()}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Swarm Statistics */}
      {swarmStats && (
        <Card>
          <CardHeader>
            <CardTitle>Swarm Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Total Capital</p>
                <p className="text-2xl font-bold">
                  ${swarmStats.totalCapital.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total P&L</p>
                <p className={`text-2xl font-bold ${swarmStats.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ${swarmStats.totalPnl.toLocaleString()} ({swarmStats.totalPnlPercentage.toFixed(2)}%)
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Active Clones</p>
                <p className="text-2xl font-bold">
                  {swarmStats.activeClones} / {swarmStats.totalClones}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Success Rate</p>
                <p className="text-2xl font-bold">
                  {swarmStats.successRate.toFixed(1)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active Clones */}
      <Card>
        <CardHeader>
          <CardTitle>Active Clones ({clones.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {clones.slice(0, 5).map(clone => (
              <div key={clone.id} className="flex items-center justify-between p-2 border rounded">
                <div>
                  <p className="font-medium">Clone {clone.id.slice(0, 8)}</p>
                  <p className="text-sm text-muted-foreground">
                    Gen {clone.generation} • {clone.strategy}
                  </p>
                </div>
                <div className="text-right">
                  <p className={`font-bold ${clone.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ${clone.pnl.toFixed(2)} ({clone.pnlPercentage.toFixed(2)}%)
                  </p>
                  <Badge variant={clone.status === 'active' ? 'default' : 'secondary'}>
                    {clone.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Trades */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {trades.map(trade => (
              <div key={trade.id} className="flex items-center justify-between p-2 border rounded">
                <div>
                  <p className="font-medium">{trade.symbol}</p>
                  <p className="text-sm text-muted-foreground">
                    {trade.side} {trade.quantity} @ ${trade.price}
                  </p>
                </div>
                <div className="text-right">
                  {trade.pnl !== undefined && (
                    <p className={`font-bold ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ${trade.pnl.toFixed(2)}
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    {new Date(trade.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* High Priority Alerts */}
      {alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>High Priority Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {alerts.map(alert => (
                <Alert key={alert.id} variant={alert.type === 'error' ? 'destructive' : 'default'}>
                  <AlertDescription className="flex items-start justify-between">
                    <div>
                      <p className="font-medium">{alert.title}</p>
                      <p className="text-sm">{alert.message}</p>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => dismissAlert(alert.id)}
                    >
                      Dismiss
                    </Button>
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* MEV Opportunities */}
      {mevOpportunities.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>MEV Opportunities</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {mevOpportunities.filter(o => o.status === 'pending').map(opp => (
                <div key={opp.id} className="flex items-center justify-between p-2 border rounded">
                  <div>
                    <p className="font-medium">{opp.type}</p>
                    <p className="text-sm text-muted-foreground">
                      Net Profit: ${opp.netProfit.toFixed(2)} • Confidence: {opp.confidence}%
                    </p>
                  </div>
                  <Badge variant={opp.status === 'pending' ? 'default' : 'secondary'}>
                    {opp.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}