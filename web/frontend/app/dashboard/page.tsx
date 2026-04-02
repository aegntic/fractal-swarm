'use client';

import React from 'react';

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Quantum Swarm Trading Dashboard</h1>
        
        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-sm text-gray-400 mb-2">Total Value</h3>
            <p className="text-2xl font-bold text-green-400">$125,432.67</p>
            <p className="text-sm text-gray-500 mt-1">+12.3% today</p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-sm text-gray-400 mb-2">Active Trades</h3>
            <p className="text-2xl font-bold">342</p>
            <p className="text-sm text-gray-500 mt-1">27 clones active</p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-sm text-gray-400 mb-2">Win Rate</h3>
            <p className="text-2xl font-bold text-blue-400">87.2%</p>
            <p className="text-sm text-gray-500 mt-1">Last 24h</p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-sm text-gray-400 mb-2">24h Volume</h3>
            <p className="text-2xl font-bold">$2.4M</p>
            <p className="text-sm text-gray-500 mt-1">Across all pairs</p>
          </div>
        </div>
        
        {/* Main Chart Area */}
        <div className="grid grid-cols-3 gap-6">
          {/* Large Chart */}
          <div className="col-span-2 bg-gray-800 rounded-lg p-6 border border-gray-700 h-96">
            <h2 className="text-xl font-semibold mb-4">BTC/USDT Price Chart</h2>
            <div className="w-full h-full bg-gray-900 rounded flex items-center justify-center">
              <p className="text-gray-500">Chart will render here</p>
            </div>
          </div>
          
          {/* Side Panel */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
            <div className="space-y-3">
              <div className="p-3 bg-gray-900 rounded">
                <div className="flex justify-between items-center">
                  <span className="text-green-400 font-medium">BUY BTC</span>
                  <span className="text-sm text-gray-400">2m ago</span>
                </div>
                <p className="text-sm text-gray-300 mt-1">$5,432 @ $45,201</p>
              </div>
              
              <div className="p-3 bg-gray-900 rounded">
                <div className="flex justify-between items-center">
                  <span className="text-red-400 font-medium">SELL ETH</span>
                  <span className="text-sm text-gray-400">5m ago</span>
                </div>
                <p className="text-sm text-gray-300 mt-1">$3,210 @ $2,351</p>
              </div>
              
              <div className="p-3 bg-gray-900 rounded">
                <div className="flex justify-between items-center">
                  <span className="text-green-400 font-medium">BUY SOL</span>
                  <span className="text-sm text-gray-400">8m ago</span>
                </div>
                <p className="text-sm text-gray-300 mt-1">$1,854 @ $98.43</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Bottom Section */}
        <div className="mt-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4">Active Strategies</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left border-b border-gray-700">
                  <th className="pb-3 text-sm text-gray-400">Strategy</th>
                  <th className="pb-3 text-sm text-gray-400">Status</th>
                  <th className="pb-3 text-sm text-gray-400">P&L</th>
                  <th className="pb-3 text-sm text-gray-400">Trades</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-700/50">
                  <td className="py-3">Cross-Chain Arbitrage</td>
                  <td className="py-3">
                    <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-sm">Active</span>
                  </td>
                  <td className="py-3 text-green-400">+$12,345</td>
                  <td className="py-3">156</td>
                </tr>
                <tr className="border-b border-gray-700/50">
                  <td className="py-3">MEV Hunter</td>
                  <td className="py-3">
                    <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-sm">Active</span>
                  </td>
                  <td className="py-3 text-green-400">+$8,234</td>
                  <td className="py-3">89</td>
                </tr>
                <tr>
                  <td className="py-3">Trend Following</td>
                  <td className="py-3">
                    <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-sm">Paused</span>
                  </td>
                  <td className="py-3 text-red-400">-$1,234</td>
                  <td className="py-3">234</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}