'use client';

import React from 'react';

export default function MEVCapture() {
  const mevData = [
    { type: 'Sandwich', count: 12, profit: '$2,341' },
    { type: 'Arbitrage', count: 8, profit: '$1,892' },
    { type: 'Liquidation', count: 3, profit: '$5,123' },
  ];

  const totalProfit = '$9,356';
  const successRate = 87;

  return (
    <div className="space-y-4">
      <div className="text-center mb-4">
        <div className="text-3xl font-bold text-neon-purple">{totalProfit}</div>
        <div className="text-sm text-gray-400">Total MEV Captured</div>
      </div>
      
      <div className="space-y-2">
        {mevData.map((item, index) => (
          <div key={index} className="flex items-center justify-between p-2 rounded-lg bg-white/5">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                index === 0 ? 'bg-neon-blue' : 
                index === 1 ? 'bg-neon-green' : 
                'bg-neon-pink'
              }`} />
              <span className="text-sm text-gray-300">{item.type}</span>
            </div>
            <div className="text-right">
              <div className="text-sm font-semibold text-white">{item.profit}</div>
              <div className="text-xs text-gray-400">{item.count} txs</div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-4 p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">Success Rate</span>
          <span className="text-sm font-bold text-purple-400">{successRate}%</span>
        </div>
      </div>
    </div>
  );
}