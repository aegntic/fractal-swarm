'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity,
  TrendingUp,
  TrendingDown,
  Zap,
  Users,
  DollarSign,
  AlertCircle,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react';
import { colors, glassStyle } from '@/lib/design-system';

interface Trade {
  id: string;
  type: 'buy' | 'sell' | 'mev' | 'clone';
  token: string;
  amount: number;
  price: number;
  profit?: number;
  timestamp: Date;
  status: 'success' | 'pending' | 'failed';
  icon: React.ElementType;
}

// Generate mock trades
const generateMockTrade = (): Trade => {
  const types = ['buy', 'sell', 'mev', 'clone'] as const;
  const tokens = ['BTC', 'ETH', 'SOL', 'MATIC', 'ARB', 'OP'];
  const type = types[Math.floor(Math.random() * types.length)];
  
  let icon: React.ElementType;
  switch (type) {
    case 'buy':
      icon = TrendingUp;
      break;
    case 'sell':
      icon = TrendingDown;
      break;
    case 'mev':
      icon = Zap;
      break;
    case 'clone':
      icon = Users;
      break;
  }

  return {
    id: Math.random().toString(36).substr(2, 9),
    type,
    token: tokens[Math.floor(Math.random() * tokens.length)],
    amount: Math.floor(Math.random() * 10000 + 1000),
    price: Math.random() * 1000 + 100,
    profit: type === 'sell' || type === 'mev' ? Math.random() * 500 - 100 : undefined,
    timestamp: new Date(),
    status: Math.random() > 0.1 ? 'success' : Math.random() > 0.5 ? 'pending' : 'failed',
    icon
  };
};

export default function LiveActivity() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [stats, setStats] = useState({
    totalTrades: 342,
    successRate: 87.3,
    activeClones: 27,
    profit24h: 15234.56
  });

  useEffect(() => {
    // Initial trades
    const initialTrades = Array.from({ length: 10 }, generateMockTrade);
    setTrades(initialTrades);

    // Add new trades periodically
    const interval = setInterval(() => {
      setTrades(prev => {
        const newTrade = generateMockTrade();
        return [newTrade, ...prev].slice(0, 20);
      });

      // Update stats
      setStats(prev => ({
        totalTrades: prev.totalTrades + 1,
        successRate: Math.max(80, Math.min(95, prev.successRate + (Math.random() - 0.5))),
        activeClones: Math.max(20, Math.min(35, prev.activeClones + Math.floor(Math.random() * 3 - 1))),
        profit24h: prev.profit24h + (Math.random() * 200 - 50)
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: Trade['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-400" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-400" />;
    }
  };

  const getTypeColor = (type: Trade['type']) => {
    switch (type) {
      case 'buy':
        return 'text-blue-400';
      case 'sell':
        return 'text-purple-400';
      case 'mev':
        return 'text-yellow-400';
      case 'clone':
        return 'text-teal-400';
    }
  };

  return (
    <motion.aside
      initial={{ x: 320 }}
      animate={{ x: 0 }}
      transition={{ duration: 0.3 }}
      className="fixed right-0 top-16 bottom-0 w-80 z-20 overflow-hidden"
      style={{
        ...glassStyle,
        borderLeft: `1px solid ${colors.neutral[800]}`,
        background: colors.background.secondary,
      }}
    >
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="p-4 border-b border-neutral-800">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Live Activity
            </h2>
            <span className="text-xs text-neutral-400">Real-time</span>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-lg bg-neutral-800/50">
              <div className="text-2xl font-bold text-white">{stats.totalTrades}</div>
              <div className="text-xs text-neutral-400">Total Trades</div>
            </div>
            <div className="p-3 rounded-lg bg-neutral-800/50">
              <div className="text-2xl font-bold text-green-400">{stats.successRate.toFixed(1)}%</div>
              <div className="text-xs text-neutral-400">Success Rate</div>
            </div>
            <div className="p-3 rounded-lg bg-neutral-800/50">
              <div className="text-2xl font-bold text-teal-400">{stats.activeClones}</div>
              <div className="text-xs text-neutral-400">Active Clones</div>
            </div>
            <div className="p-3 rounded-lg bg-neutral-800/50">
              <div className="text-2xl font-bold text-white">${(stats.profit24h / 1000).toFixed(1)}k</div>
              <div className="text-xs text-neutral-400">24h Profit</div>
            </div>
          </div>
        </div>

        {/* Activity Feed */}
        <div className="flex-1 overflow-y-auto p-4">
          <AnimatePresence initial={false}>
            {trades.map((trade) => (
              <motion.div
                key={trade.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="mb-3 p-3 rounded-lg bg-neutral-800/30 hover:bg-neutral-800/50 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className={`p-1.5 rounded-lg bg-neutral-800 ${getTypeColor(trade.type)}`}>
                      <trade.icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-white">
                        {trade.type.toUpperCase()} {trade.token}
                      </div>
                      <div className="text-xs text-neutral-400">
                        ${trade.amount.toLocaleString()} @ ${trade.price.toFixed(2)}
                      </div>
                    </div>
                  </div>
                  {getStatusIcon(trade.status)}
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-xs text-neutral-500">
                    {trade.timestamp.toLocaleTimeString()}
                  </span>
                  {trade.profit !== undefined && (
                    <span className={`text-xs font-medium ${
                      trade.profit > 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {trade.profit > 0 ? '+' : ''}${trade.profit.toFixed(2)}
                    </span>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Footer Alert */}
        <div className="p-4 border-t border-neutral-800">
          <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-medium text-yellow-400">High Activity Detected</div>
                <div className="text-xs text-neutral-400 mt-1">
                  Multiple arbitrage opportunities found in SOL/USDC pair
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.aside>
  );
}