'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Bell, 
  Search, 
  User, 
  Wallet,
  TrendingUp,
  TrendingDown,
  Globe,
  ChevronDown,
  Clock
} from 'lucide-react';
import { colors, glassStyle } from '@/lib/design-system';

export default function TopBar() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [marketStatus, setMarketStatus] = useState({
    btc: 45234.67,
    btcChange: 2.34,
    eth: 2356.89,
    ethChange: -1.23,
  });

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
      
      // Simulate market price changes
      setMarketStatus(prev => ({
        btc: prev.btc * (1 + (Math.random() * 0.002 - 0.001)),
        btcChange: Math.random() * 4 - 2,
        eth: prev.eth * (1 + (Math.random() * 0.002 - 0.001)),
        ethChange: Math.random() * 4 - 2,
      }));
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <motion.header
      initial={{ y: -80 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.3 }}
      className="fixed top-0 left-64 right-0 h-16 z-30"
      style={{
        ...glassStyle,
        borderBottom: `1px solid ${colors.neutral[800]}`,
        background: colors.background.secondary,
      }}
    >
      <div className="flex items-center justify-between h-full px-6">
        {/* Left Section - Market Info */}
        <div className="flex items-center gap-6">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="flex items-center gap-4"
          >
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-neutral-400" />
              <span className="text-sm text-neutral-400">Markets</span>
            </div>
            
            <div className="flex items-center gap-3 px-3 py-1.5 rounded-lg bg-neutral-800/50">
              <span className="text-sm text-neutral-400">BTC</span>
              <span className="text-sm font-semibold text-white">
                ${marketStatus.btc.toFixed(2)}
              </span>
              <div className={`flex items-center gap-1 text-sm font-medium ${
                marketStatus.btcChange > 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {marketStatus.btcChange > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                {Math.abs(marketStatus.btcChange).toFixed(2)}%
              </div>
            </div>
            
            <div className="flex items-center gap-3 px-3 py-1.5 rounded-lg bg-neutral-800/50">
              <span className="text-sm text-neutral-400">ETH</span>
              <span className="text-sm font-semibold text-white">
                ${marketStatus.eth.toFixed(2)}
              </span>
              <div className={`flex items-center gap-1 text-sm font-medium ${
                marketStatus.ethChange > 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {marketStatus.ethChange > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                {Math.abs(marketStatus.ethChange).toFixed(2)}%
              </div>
            </div>
          </motion.div>
        </div>

        {/* Center Section - Search */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="flex-1 max-w-md mx-6"
        >
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-neutral-400" />
            <input
              type="text"
              placeholder="Search tokens, strategies, or commands..."
              className="w-full pl-10 pr-4 py-2 bg-neutral-800/50 border border-neutral-700 rounded-lg text-sm text-white placeholder-neutral-400 focus:outline-none focus:border-primary-500 transition-colors"
            />
          </div>
        </motion.div>

        {/* Right Section - User Info */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="flex items-center gap-4"
        >
          {/* Time */}
          <div className="flex items-center gap-2 text-sm text-neutral-400">
            <Clock className="w-4 h-4" />
            <span>{currentTime.toLocaleTimeString()}</span>
          </div>

          {/* Notifications */}
          <button className="relative p-2 rounded-lg hover:bg-neutral-800/50 transition-colors">
            <Bell className="w-5 h-5 text-neutral-400" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          {/* Wallet */}
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-neutral-800/50 hover:bg-neutral-700/50 transition-colors">
            <Wallet className="w-4 h-4 text-neutral-400" />
            <span className="text-sm font-medium text-white">$125,432.67</span>
          </button>

          {/* User Menu */}
          <button className="flex items-center gap-3 px-3 py-1.5 rounded-lg hover:bg-neutral-800/50 transition-colors">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-teal-400 flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-medium text-white">Admin</span>
            <ChevronDown className="w-4 h-4 text-neutral-400" />
          </button>
        </motion.div>
      </div>
    </motion.header>
  );
}