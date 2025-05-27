'use client';

import React, { Suspense } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity, 
  DollarSign, 
  Users, 
  TrendingUp, 
  Zap, 
  Shield,
  Globe,
  BarChart3,
  Settings,
  User,
  BookOpen,
  Eye,
  EyeOff
} from 'lucide-react';
import SwarmVisualization from '@/components/3d/SwarmVisualization';
import { TradingControls } from '@/components/controls/TradingControls';
import { useTradingStore } from '@/store/trading';
import { useConnectionStatus } from '@/hooks/useWebSocket';
import { useState } from 'react';

export default function Dashboard() {
  const { status: connectionStatus } = useConnectionStatus();
  const { 
    swarmStats,
    clones,
    positions,
    recentTrades,
    alerts
  } = useTradingStore();

  // Compute derived values
  const totalCapital = swarmStats?.totalCapital || 0;
  const totalClones = clones.size || 0;
  const winRate = swarmStats?.successRate || 0;
  const dailyPnL = swarmStats?.totalPnlPercentage || 0;

  const [show3D, setShow3D] = useState(true);

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'bg-green-500';
      case 'connecting': return 'bg-yellow-500';
      case 'disconnected': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900 p-4 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl lg:text-4xl font-bold bg-gradient-to-r from-neon-blue to-neon-purple bg-clip-text text-transparent">
            Quantum Swarm Trader
          </h1>
          <p className="text-gray-400 mt-1">Real-time autonomous trading dashboard</p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getConnectionStatusColor()}`} />
            <span className="text-sm text-gray-300 capitalize">{connectionStatus}</span>
          </div>
          <Badge variant="outline" className="text-white border-neon-blue">
            v1.0.0
          </Badge>
        </div>
      </motion.div>

      {/* Key Metrics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <Card className="bg-dark-800/90 border-dark-600 backdrop-blur-xl">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-300">Total Capital</CardTitle>
            <DollarSign className="h-4 w-4 text-neon-blue" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{formatCurrency(totalCapital)}</div>
            <p className="text-xs text-gray-400">
              <span className={`${dailyPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {formatPercentage(dailyPnL)}
              </span> from yesterday
            </p>
          </CardContent>
        </Card>

        <Card className="bg-dark-800/90 border-dark-600 backdrop-blur-xl">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-300">Active Clones</CardTitle>
            <Users className="h-4 w-4 text-neon-purple" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{totalClones}</div>
            <p className="text-xs text-gray-400">
              {swarmStats?.activeClones || 0} active, {(swarmStats?.totalClones || 0) - (swarmStats?.activeClones || 0)} spawning
            </p>
          </CardContent>
        </Card>

        <Card className="bg-dark-800/90 border-dark-600 backdrop-blur-xl">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-300">Win Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{winRate.toFixed(1)}%</div>
            <p className="text-xs text-gray-400">
              {recentTrades.filter(t => t.pnl && t.pnl > 0).length} / {recentTrades.length} trades
            </p>
          </CardContent>
        </Card>

        <Card className="bg-dark-800/90 border-dark-600 backdrop-blur-xl">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-300">MEV Captured</CardTitle>
            <Zap className="h-4 w-4 text-yellow-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{formatCurrency(swarmStats?.mevCaptured || 0)}</div>
            <p className="text-xs text-gray-400">
              24 opportunities found
            </p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Dashboard */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 xl:grid-cols-3 gap-6"
      >
        {/* 3D Visualization */}
        <div className="xl:col-span-2">
          <Card className="bg-dark-800/90 border-dark-600 backdrop-blur-xl h-[600px]">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white flex items-center gap-2">
                  <Activity className="w-5 h-5 text-neon-blue" />
                  Swarm Visualization
                </CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShow3D(!show3D)}
                  className="border-dark-500 text-white hover:bg-dark-700"
                >
                  {show3D ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  {show3D ? 'Hide 3D' : 'Show 3D'}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="h-[500px] p-0">
              {show3D ? (
                <Suspense fallback={
                  <div className="h-full flex items-center justify-center text-gray-400">
                    Loading 3D visualization...
                  </div>
                }>
                  <SwarmVisualization 
                    clones={[
                      { id: 'clone-1', generation: 0, performance: 0.15, status: 'active', capital: 150, trades: 25, winRate: 0.72, strategy: 'MEV Hunter' },
                      { id: 'clone-2', generation: 1, performance: 0.23, status: 'active', capital: 230, trades: 18, winRate: 0.83, strategy: 'Arbitrage' },
                      { id: 'clone-3', generation: 1, performance: -0.05, status: 'inactive', capital: 95, trades: 12, winRate: 0.42, strategy: 'Grid Trading' },
                      { id: 'clone-4', generation: 2, performance: 0.34, status: 'spawning', capital: 340, trades: 8, winRate: 0.88, strategy: 'Flash Loan' }
                    ]}
                    connections={[
                      { from: 'clone-1', to: 'clone-2', strength: 0.8 },
                      { from: 'clone-1', to: 'clone-3', strength: 0.3 },
                      { from: 'clone-2', to: 'clone-4', strength: 0.9 }
                    ]}
                    trades={[]}
                  />
                </Suspense>
              ) : (
                <div className="h-full flex items-center justify-center text-gray-400">
                  3D visualization hidden
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Trading Controls */}
        <div>
          <TradingControls />
        </div>
      </motion.div>

      {/* Detailed Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-5 bg-dark-800/90 border border-dark-600">
            <TabsTrigger value="overview" className="text-white data-[state=active]:bg-neon-blue/20">
              <BarChart3 className="w-4 h-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="clones" className="text-white data-[state=active]:bg-neon-blue/20">
              <Users className="w-4 h-4 mr-2" />
              Clones
            </TabsTrigger>
            <TabsTrigger value="positions" className="text-white data-[state=active]:bg-neon-blue/20">
              <Globe className="w-4 h-4 mr-2" />
              Positions
            </TabsTrigger>
            <TabsTrigger value="accounts" className="text-white data-[state=active]:bg-neon-blue/20">
              <User className="w-4 h-4 mr-2" />
              Accounts
            </TabsTrigger>
            <TabsTrigger value="help" className="text-white data-[state=active]:bg-neon-blue/20">
              <BookOpen className="w-4 h-4 mr-2" />
              Help
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="bg-dark-800/90 border-dark-600 backdrop-blur-xl">
                <CardHeader>
                  <CardTitle className="text-white">Performance Metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-400">24h Volume</p>
                      <p className="text-lg font-semibold text-white">{formatCurrency(125000)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-400">Total Trades</p>
                      <p className="text-lg font-semibold text-white">{swarmStats?.totalTrades || 0}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-400">Avg Trade Size</p>
                      <p className="text-lg font-semibold text-white">{formatCurrency(2500)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-400">Risk Score</p>
                      <p className="text-lg font-semibold text-yellow-400">35/100</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-dark-800/90 border-dark-600 backdrop-blur-xl">
                <CardHeader>
                  <CardTitle className="text-white">Recent Activity</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {recentTrades.slice(0, 5).map((trade, index) => (
                    <div key={trade.id} className="flex items-center justify-between p-2 bg-dark-700/50 rounded">
                      <div>
                        <p className="text-sm text-white">{trade.symbol}</p>
                        <p className="text-xs text-gray-400">{trade.side} • {trade.quantity}</p>
                      </div>
                      <div className="text-right">
                        <p className={`text-sm font-semibold ${(trade.pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {formatCurrency(trade.pnl || 0)}
                        </p>
                        <p className="text-xs text-gray-400">{new Date(trade.timestamp).toLocaleTimeString()}</p>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="clones" className="mt-6">
            <Card className="bg-dark-800/90 border-dark-600 backdrop-blur-xl">
              <CardHeader>
                <CardTitle className="text-white">Clone Management</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-400">Clone management interface coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="positions" className="mt-6">
            <Card className="bg-dark-800/90 border-dark-600 backdrop-blur-xl">
              <CardHeader>
                <CardTitle className="text-white">Active Positions</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-400">Position management interface coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="accounts" className="mt-6">
            <Card className="bg-dark-800/90 border-dark-600 backdrop-blur-xl">
              <CardHeader>
                <CardTitle className="text-white">Account Management</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-400">Account management interface coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="help" className="mt-6">
            <Card className="bg-dark-800/90 border-dark-600 backdrop-blur-xl">
              <CardHeader>
                <CardTitle className="text-white">Getting Started</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-dark-700/50 rounded-lg">
                    <h3 className="text-lg font-semibold text-white mb-2">Quick Start</h3>
                    <ul className="text-sm text-gray-300 space-y-1">
                      <li>• Connect your trading accounts</li>
                      <li>• Set your risk parameters</li>
                      <li>• Choose initial strategies</li>
                      <li>• Start with conservative settings</li>
                    </ul>
                  </div>
                  <div className="p-4 bg-dark-700/50 rounded-lg">
                    <h3 className="text-lg font-semibold text-white mb-2">Safety Tips</h3>
                    <ul className="text-sm text-gray-300 space-y-1">
                      <li>• Start with small capital amounts</li>
                      <li>• Monitor performance regularly</li>
                      <li>• Use emergency stop if needed</li>
                      <li>• Keep API keys secure</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
}