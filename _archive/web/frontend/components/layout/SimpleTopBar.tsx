'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Search, Bell, ChevronDown } from 'lucide-react';

export default function SimpleTopBar() {
  return (
    <motion.header 
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="fixed top-0 left-72 right-96 h-20 bg-[#0f0f10]/80 backdrop-blur-xl border-b border-neutral-800 z-10"
    >
      <div className="h-full px-8 flex items-center justify-between">
        {/* Left side - Market data */}
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <span className="text-sm text-neutral-500">Markets</span>
          </div>
          
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-neutral-400">BTC</span>
              <span className="text-sm font-semibold text-white">$45,205.41</span>
              <span className="text-xs text-green-400">▲ 0.90%</span>
            </div>
            
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-neutral-400">ETH</span>
              <span className="text-sm font-semibold text-white">$2,353.43</span>
              <span className="text-xs text-red-400">▼ 0.51%</span>
            </div>
          </div>
        </div>
        
        {/* Center - Search */}
        <div className="flex-1 max-w-md mx-8">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-neutral-500" />
            <input
              type="text"
              placeholder="Search tokens, strategies..."
              className="w-full pl-10 pr-4 py-2 bg-white/5 border border-neutral-800 rounded-lg text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-primary-500 focus:bg-white/10 transition-all duration-200"
            />
          </div>
        </div>
        
        {/* Right side - User info */}
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-xs text-neutral-500">21:16:32</div>
            <div className="text-sm font-semibold text-white">$125,432.67</div>
          </div>
          
          <button className="relative p-2 rounded-lg hover:bg-white/5 transition-colors">
            <Bell className="w-5 h-5 text-neutral-400" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-primary-400 rounded-full"></span>
          </button>
          
          <button className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center">
              <span className="text-xs font-semibold text-white">A</span>
            </div>
            <span className="text-sm font-medium text-white">Admin</span>
            <ChevronDown className="w-4 h-4 text-neutral-400" />
          </button>
        </div>
      </div>
    </motion.header>
  );
}