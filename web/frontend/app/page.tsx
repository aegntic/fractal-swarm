'use client';

import React from 'react';
import { motion } from 'framer-motion';
import dynamic from 'next/dynamic';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  DollarSign,
  Users,
  Zap,
  BarChart3,
  PieChart,
  Layers,
  Eye,
  Brain,
  Trophy
} from 'lucide-react';

// Dynamic imports for heavy components
const PerformanceChart = dynamic(() => import('@/components/charts/PerformanceChart'), { ssr: false });
const VolumeChart = dynamic(() => import('@/components/charts/VolumeChart'), { ssr: false });
const CloneDistribution = dynamic(() => import('@/components/charts/CloneDistribution'), { ssr: false });
const MEVCapture = dynamic(() => import('@/components/charts/MEVCapture'), { ssr: false });
const WinRateGauge = dynamic(() => import('@/components/charts/WinRateGauge'), { ssr: false });
const ActivityFeed = dynamic(() => import('@/components/ActivityFeed'), { ssr: false });
const MetricCard = dynamic(() => import('@/components/MetricCard'), { ssr: false });

export default function Dashboard() {
  return (
    <div className="min-h-screen p-4 md:p-6 lg:p-8">
      {/* Header */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl md:text-4xl font-bold gradient-text mb-2">
          Quantum Swarm Trader
        </h1>
        <p className="text-gray-400">Real-time autonomous trading dashboard</p>
      </motion.div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 lg:gap-6">
        
        {/* Overall Performance - Large Card */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="col-span-1 md:col-span-2 lg:col-span-2 xl:col-span-2 glass-card rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Overall Performance</h2>
            <span className="text-sm text-gray-400">Last 30 days</span>
          </div>
          <PerformanceChart />
        </motion.div>

        {/* Key Metrics */}
        <MetricCard
          title="Total Capital"
          value="$125,432.67"
          change="+15.3%"
          trend="up"
          icon={DollarSign}
          delay={0.2}
        />

        <MetricCard
          title="Active Clones"
          value="27"
          change="+3"
          trend="up"
          icon={Users}
          delay={0.3}
        />

        {/* Volume Chart */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4 }}
          className="col-span-1 md:col-span-2 lg:col-span-1 glass-card rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">24h Volume</h2>
            <BarChart3 className="w-5 h-5 text-gray-400" />
          </div>
          <VolumeChart />
        </motion.div>

        {/* Win Rate Gauge */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
          className="col-span-1 glass-card rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Win Rate</h2>
            <Trophy className="w-5 h-5 text-yellow-400" />
          </div>
          <WinRateGauge />
        </motion.div>

        {/* Clone Distribution */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.6 }}
          className="col-span-1 glass-card rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Clone Distribution</h2>
            <PieChart className="w-5 h-5 text-gray-400" />
          </div>
          <CloneDistribution />
        </motion.div>

        {/* MEV Capture */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.7 }}
          className="col-span-1 glass-card rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">MEV Capture</h2>
            <Zap className="w-5 h-5 text-purple-400" />
          </div>
          <MEVCapture />
        </motion.div>

        {/* Strategy Performance */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.8 }}
          className="col-span-1 md:col-span-2 lg:col-span-2 glass-card rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Strategy Performance</h2>
            <Brain className="w-5 h-5 text-blue-400" />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-neon-green">87%</div>
              <div className="text-sm text-gray-400">Arbitrage</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-neon-blue">72%</div>
              <div className="text-sm text-gray-400">Trend Follow</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-neon-purple">91%</div>
              <div className="text-sm text-gray-400">MEV Hunter</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-neon-pink">68%</div>
              <div className="text-sm text-gray-400">Market Make</div>
            </div>
          </div>
        </motion.div>

        {/* Quick Stats */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.9 }}
          className="col-span-1 glass-card rounded-2xl p-6"
        >
          <h2 className="text-lg font-semibold text-white mb-4">Quick Stats</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Avg Trade Size</span>
              <span className="text-white font-semibold">$2,543</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Risk Score</span>
              <span className="text-green-400 font-semibold">Low</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Daily Trades</span>
              <span className="text-white font-semibold">342</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Success Rate</span>
              <span className="text-white font-semibold">78.4%</span>
            </div>
          </div>
        </motion.div>

        {/* Activity Feed */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1.0 }}
          className="col-span-1 md:col-span-2 lg:col-span-1 xl:col-span-1 glass-card rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Recent Activity</h2>
            <Activity className="w-5 h-5 text-gray-400" />
          </div>
          <ActivityFeed />
        </motion.div>

      </div>

      {/* Bottom Control Panel */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.1 }}
        className="mt-8 glass-card rounded-2xl p-6"
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-6">
            <button className="px-6 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-xl transition-colors">
              Start Trading
            </button>
            <button className="px-6 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 rounded-xl transition-colors">
              Pause
            </button>
            <button className="px-6 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-xl transition-colors">
              Emergency Stop
            </button>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-gray-400">System Online</span>
            </div>
            <div className="text-gray-400">|</div>
            <span className="text-gray-400">Latency: 12ms</span>
            <div className="text-gray-400">|</div>
            <span className="text-gray-400">API: Connected</span>
          </div>
        </div>
      </motion.div>
    </div>
  );
}