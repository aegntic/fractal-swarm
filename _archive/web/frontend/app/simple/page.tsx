'use client';

import React from 'react';
import dynamic from 'next/dynamic';

const SimpleCandlestickChart = dynamic(() => import('@/components/charts/SimpleCandlestickChart'), { ssr: false });
const SimpleAreaChart = dynamic(() => import('@/components/charts/SimpleAreaChart'), { ssr: false });
const SimpleRadialChart = dynamic(() => import('@/components/charts/SimpleRadialChart'), { ssr: false });
const SimpleHeatmapChart = dynamic(() => import('@/components/charts/SimpleHeatmapChart'), { ssr: false });

export default function SimpleDashboard() {
  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      {/* Simple Grid Layout */}
      <div className="grid grid-cols-12 min-h-screen">
        
        {/* Sidebar */}
        <div className="col-span-2 bg-[#0f0f10] border-r border-neutral-800 p-6">
          <h1 className="text-2xl font-bold mb-8">Quantum Swarm</h1>
          <nav className="space-y-2">
            <div className="px-4 py-2 bg-primary-500/10 text-primary-400 rounded">Dashboard</div>
            <div className="px-4 py-2 text-neutral-400">Trading</div>
            <div className="px-4 py-2 text-neutral-400">Analytics</div>
          </nav>
        </div>
        
        {/* Main Content */}
        <div className="col-span-8 p-8">
          <h2 className="text-3xl font-bold mb-8">Trading Dashboard</h2>
          
          {/* Charts Grid */}
          <div className="grid grid-cols-2 gap-6">
            {/* Candlestick Chart */}
            <div className="col-span-2 bg-white/5 backdrop-blur rounded-lg p-6 border border-white/10">
              <h3 className="text-xl font-semibold mb-4">BTC/USDT Price Action</h3>
              <div className="h-[400px]">
                <SimpleCandlestickChart />
              </div>
            </div>
            
            {/* Area Chart */}
            <div className="bg-white/5 backdrop-blur rounded-lg p-6 border border-white/10">
              <h3 className="text-xl font-semibold mb-4">Portfolio Value</h3>
              <SimpleAreaChart />
            </div>
            
            {/* Radial Chart */}
            <div className="bg-white/5 backdrop-blur rounded-lg p-6 border border-white/10">
              <h3 className="text-xl font-semibold mb-4">Performance Metrics</h3>
              <SimpleRadialChart />
            </div>
            
            {/* Heatmap */}
            <div className="col-span-2 bg-white/5 backdrop-blur rounded-lg p-6 border border-white/10">
              <h3 className="text-xl font-semibold mb-4">Market Overview</h3>
              <SimpleHeatmapChart />
            </div>
          </div>
        </div>
        
        {/* Right Sidebar */}
        <div className="col-span-2 bg-[#0f0f10] border-l border-neutral-800 p-6">
          <h2 className="text-xl font-bold mb-6">Live Activity</h2>
          <div className="space-y-3">
            <div className="p-3 bg-white/5 rounded">
              <div className="text-green-400 text-sm">BUY BTC</div>
              <div className="text-white">$5,432</div>
            </div>
            <div className="p-3 bg-white/5 rounded">
              <div className="text-red-400 text-sm">SELL ETH</div>
              <div className="text-white">$3,210</div>
            </div>
          </div>
        </div>
        
      </div>
    </div>
  );
}