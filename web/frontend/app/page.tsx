"use client";

import { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  DollarSign, 
  TrendingUp, 
  Users, 
  Activity,
  AlertTriangle,
  Zap,
  Brain,
  StopCircle
} from 'lucide-react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { toast } from 'react-hot-toast';

// API client
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchStatus() {
  const res = await fetch(`${API_URL}/api/status`);
  return res.json();
}

async function fetchClones() {
  const res = await fetch(`${API_URL}/api/clones`);
  return res.json();
}

async function fetchTrades() {
  const res = await fetch(`${API_URL}/api/trades?limit=20`);
  return res.json();
}

async function fetchPerformance() {
  const res = await fetch(`${API_URL}/api/performance/history?period=24h`);
  return res.json();
}

export default function Dashboard() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const queryClient = useQueryClient();

  // Queries
  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: fetchStatus,
    refetchInterval: 5000,
  });

  const { data: clones } = useQuery({
    queryKey: ['clones'],
    queryFn: fetchClones,
    refetchInterval: 10000,
  });

  const { data: trades } = useQuery({
    queryKey: ['trades'],
    queryFn: fetchTrades,
    refetchInterval: 5000,
  });

  const { data: performance } = useQuery({
    queryKey: ['performance'],
    queryFn: fetchPerformance,
    refetchInterval: 60000,
  });

  // WebSocket connection
  useEffect(() => {
    const newSocket = io(API_URL.replace('http', 'ws'), {
      path: '/ws',
      transports: ['websocket'],
    });

    newSocket.on('connect', () => {
      setIsConnected(true);
      toast.success('Connected to swarm');
    });

    newSocket.on('disconnect', () => {
      setIsConnected(false);
      toast.error('Disconnected from swarm');
    });

    newSocket.on('status_update', (data) => {
      queryClient.setQueryData(['status'], data.data);
    });

    newSocket.on('new_trade', (data) => {
      toast.success(`New trade: ${data.data.pair} +${data.data.profit}%`);
      queryClient.invalidateQueries({ queryKey: ['trades'] });
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, [queryClient]);

  const handleEmergencyStop = async () => {
    if (confirm('Are you sure you want to emergency stop all trading?')) {
      try {
        const res = await fetch(`${API_URL}/api/emergency-stop`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reason: 'Manual emergency stop', liquidate: false }),
        });
        
        if (res.ok) {
          toast.error('Emergency stop activated!');
        }
      } catch (error) {
        toast.error('Failed to activate emergency stop');
      }
    }
  };

  const handleSpawnClone = async () => {
    try {
      const res = await fetch(`${API_URL}/api/clones/spawn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ capital_allocation: 100, chain: 'solana' }),
      });
      
      if (res.ok) {
        toast.success('New clone spawned!');
        queryClient.invalidateQueries({ queryKey: ['clones'] });
      }
    } catch (error) {
      toast.error('Failed to spawn clone');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 text-white p-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-600 bg-clip-text text-transparent">
            Quantum Swarm Trader
          </h1>
          <p className="text-gray-400">Autonomous Trading System</p>
        </div>
        <div className="flex gap-4">
          <Badge variant={isConnected ? "default" : "destructive"}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </Badge>
          <Button 
            variant="destructive" 
            onClick={handleEmergencyStop}
            className="flex items-center gap-2"
          >
            <StopCircle className="w-4 h-4" />
            Emergency Stop
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Capital</CardTitle>
            <DollarSign className="h-4 w-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${status?.total_capital.toLocaleString() || '0'}</div>
            <p className="text-xs text-green-400">+{status?.profit_tracker.total_profit || 0}% today</p>
          </CardContent>
        </Card>

        <Card className="bg-gray-800 border-gray-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Clones</CardTitle>
            <Users className="h-4 w-4 text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{status?.total_clones || 0}</div>
            <p className="text-xs text-gray-400">
              SOL: {status?.solana_clones || 0} | ETH: {status?.ethereum_clones || 0}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gray-800 border-gray-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-yellow-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {((status?.profit_tracker.win_rate || 0) * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-gray-400">
              {status?.profit_tracker.total_trades || 0} trades
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gray-800 border-gray-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Trading Phase</CardTitle>
            <Brain className="h-4 w-4 text-purple-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{status?.trading_phase || 'INIT'}</div>
            <p className="text-xs text-gray-400">
              Quantum States: {status?.quantum_state.active_superpositions || 0}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="bg-gray-800">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="clones">Clones</TabsTrigger>
          <TabsTrigger value="trades">Trades</TabsTrigger>
          <TabsTrigger value="strategies">Strategies</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Performance Chart */}
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle>Capital Growth (24h)</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={performance}>
                  <defs>
                    <linearGradient id="colorCapital" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(ts) => new Date(ts * 1000).toLocaleTimeString()}
                    stroke="#9ca3af"
                  />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                    labelFormatter={(ts) => new Date(ts * 1000).toLocaleString()}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="capital" 
                    stroke="#06b6d4" 
                    fillOpacity={1} 
                    fill="url(#colorCapital)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button 
                  onClick={handleSpawnClone}
                  className="w-full bg-gradient-to-r from-cyan-500 to-blue-500"
                >
                  <Zap className="w-4 h-4 mr-2" />
                  Spawn New Clone
                </Button>
                <Button variant="outline" className="w-full">
                  Adjust Risk Parameters
                </Button>
                <Button variant="outline" className="w-full">
                  Export Trade History
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <CardTitle>Recent Alerts</CardTitle>
              </CardHeader>
              <CardContent>
                <Alert className="bg-blue-950 border-blue-800">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Clone spawn threshold reached at $2,000
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="clones" className="space-y-4">
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle>Active Clones</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {clones?.map((clone: any) => (
                  <div 
                    key={clone.id} 
                    className="flex items-center justify-between p-3 bg-gray-900 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${
                        clone.status === 'active' ? 'bg-green-400' : 'bg-yellow-400'
                      }`} />
                      <div>
                        <p className="font-medium">{clone.id}</p>
                        <p className="text-sm text-gray-400">
                          {clone.specialization} | Gen {clone.generation}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">${clone.balance.toFixed(2)}</p>
                      <p className={`text-sm ${
                        clone.profit > 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {clone.profit > 0 ? '+' : ''}{clone.profit.toFixed(2)}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trades" className="space-y-4">
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle>Recent Trades</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left p-2">Time</th>
                      <th className="text-left p-2">Pair</th>
                      <th className="text-left p-2">Type</th>
                      <th className="text-left p-2">Clone</th>
                      <th className="text-right p-2">Profit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades?.slice(0, 10).map((trade: any) => (
                      <tr key={trade.id} className="border-b border-gray-800">
                        <td className="p-2 text-sm">
                          {new Date(trade.timestamp).toLocaleTimeString()}
                        </td>
                        <td className="p-2">{trade.pair}</td>
                        <td className="p-2">
                          <Badge variant="outline" className="text-xs">
                            {trade.type}
                          </Badge>
                        </td>
                        <td className="p-2 text-sm text-gray-400">{trade.clone_id}</td>
                        <td className={`p-2 text-right font-medium ${
                          trade.profit > 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {trade.profit > 0 ? '+' : ''}{trade.profit.toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="strategies" className="space-y-4">
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle>Strategy Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {['MEV Hunting', 'Cross-Chain Arbitrage', 'Liquidity Provision', 'Social Momentum'].map((strategy) => (
                  <div key={strategy} className="space-y-2">
                    <div className="flex justify-between">
                      <span>{strategy}</span>
                      <span className="text-green-400">+{(Math.random() * 10).toFixed(2)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-cyan-500 to-blue-500 h-2 rounded-full"
                        style={{ width: `${Math.random() * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}