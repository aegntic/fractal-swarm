'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Activity, TrendingUp, TrendingDown } from 'lucide-react';

interface Trade {
  id: string;
  type: 'BUY' | 'SELL';
  token: string;
  amount: string;
  price: string;
  time: string;
  profit?: string;
}

export default function SimpleLiveActivity() {
  const [trades, setTrades] = useState<Trade[]>([
    { id: '1', type: 'SELL', token: 'ARB', amount: '$9,040', price: '$818.54', time: '21:16:32', profit: '-$63.57' },
    { id: '2', type: 'BUY', token: 'BTC', amount: '$6,433', price: '$195.38', time: '21:16:29' },
    { id: '3', type: 'BUY', token: 'MATIC', amount: '$6,771', price: '$794.37', time: '21:16:26' },
    { id: '4', type: 'BUY', token: 'OP', amount: '$3,399', price: '$1090.83', time: '21:16:23' },
  ]);

  // Add new trades periodically
  useEffect(() => {
    const interval = setInterval(() => {
      const tokens = ['BTC', 'ETH', 'BNB', 'SOL', 'MATIC', 'ARB', 'OP', 'LINK'];
      const newTrade: Trade = {
        id: Date.now().toString(),
        type: Math.random() > 0.5 ? 'BUY' : 'SELL',
        token: tokens[Math.floor(Math.random() * tokens.length)],
        amount: `$${(Math.random() * 10000 + 1000).toFixed(0)}`,
        price: `$${(Math.random() * 1000 + 100).toFixed(2)}`,
        time: new Date().toLocaleTimeString('en-US', { hour12: false }),
        profit: Math.random() > 0.5 ? `+$${(Math.random() * 500).toFixed(2)}` : `-$${(Math.random() * 500).toFixed(2)}`
      };
      
      setTrades(prev => [newTrade, ...prev.slice(0, 9)]);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <motion.aside 
      initial={{ x: 300 }}
      animate={{ x: 0 }}
      className="fixed right-0 top-0 h-full w-96 bg-[#0f0f10] border-l border-neutral-800 z-20"
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-white">Live Activity</h2>
          </div>
          <span className="text-xs text-neutral-500">Real-time</span>
        </div>
        
        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="p-4 rounded-lg bg-white/5 border border-neutral-800">
            <div className="text-2xl font-bold text-white mb-1">344</div>
            <div className="text-xs text-neutral-500">Total Trades</div>
          </div>
          <div className="p-4 rounded-lg bg-white/5 border border-neutral-800">
            <div className="text-2xl font-bold text-green-400 mb-1">87.2%</div>
            <div className="text-xs text-neutral-500">Success Rate</div>
          </div>
          <div className="p-4 rounded-lg bg-white/5 border border-neutral-800">
            <div className="text-2xl font-bold text-white mb-1">29</div>
            <div className="text-xs text-neutral-500">Active Clones</div>
          </div>
          <div className="p-4 rounded-lg bg-white/5 border border-neutral-800">
            <div className="text-2xl font-bold text-green-400 mb-1">$15.3k</div>
            <div className="text-xs text-neutral-500">24h Profit</div>
          </div>
        </div>
        
        {/* Trade Feed */}
        <div className="space-y-3 overflow-y-auto max-h-[calc(100vh-300px)] no-scrollbar">
          {trades.map((trade, i) => (
            <motion.div
              key={trade.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="p-3 rounded-lg bg-white/5 border border-neutral-800 hover:bg-white/10 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  {trade.type === 'BUY' ? (
                    <TrendingUp className="w-4 h-4 text-green-400" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-400" />
                  )}
                  <span className={`text-sm font-medium ${
                    trade.type === 'BUY' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {trade.type} {trade.token}
                  </span>
                </div>
                <span className="text-xs text-neutral-500">{trade.time}</span>
              </div>
              <div className="flex items-end justify-between">
                <div>
                  <div className="text-sm text-white font-medium">{trade.amount}</div>
                  <div className="text-xs text-neutral-500">@ {trade.price}</div>
                </div>
                {trade.profit && (
                  <span className={`text-sm font-medium ${
                    trade.profit.startsWith('+') ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {trade.profit}
                  </span>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.aside>
  );
}