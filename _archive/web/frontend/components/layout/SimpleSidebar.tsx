'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  LayoutDashboard,
  TrendingUp,
  Activity,
  Users,
  Zap,
  Briefcase,
  History,
  Shield,
  Settings,
  HelpCircle
} from 'lucide-react';

const menuItems = [
  { icon: LayoutDashboard, label: 'Dashboard', active: true },
  { icon: TrendingUp, label: 'Trading', badge: 'Live' },
  { icon: Activity, label: 'Analytics' },
  { icon: Users, label: 'Swarm Status', badge: '27' },
  { icon: Zap, label: 'MEV Hunter' },
  { icon: Briefcase, label: 'Portfolio' },
  { icon: History, label: 'History' },
  { icon: Shield, label: 'Risk Control' },
  { icon: Settings, label: 'Settings' },
  { icon: HelpCircle, label: 'Help' },
];

export default function SimpleSidebar() {
  return (
    <motion.aside 
      initial={{ x: -300 }}
      animate={{ x: 0 }}
      className="fixed left-0 top-0 h-full w-72 bg-[#0f0f10] border-r border-neutral-800 z-20"
    >
      <div className="p-6">
        {/* Logo */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white mb-1">Quantum Swarm</h1>
          <p className="text-sm text-neutral-500">Trading System v1.0</p>
        </div>
        
        {/* Navigation */}
        <nav className="space-y-1">
          {menuItems.map((item, i) => (
            <motion.button
              key={i}
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.98 }}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition-all duration-200 ${
                item.active 
                  ? 'bg-primary-500/10 text-primary-400 border-l-2 border-primary-400' 
                  : 'text-neutral-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-3">
                <item.icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </div>
              {item.badge && (
                <span className={`text-xs px-2 py-1 rounded-full ${
                  item.badge === 'Live' 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-neutral-700 text-neutral-300'
                }`}>
                  {item.badge}
                </span>
              )}
            </motion.button>
          ))}
        </nav>
        
        {/* System Status */}
        <div className="mt-8 p-4 rounded-lg bg-white/5 border border-neutral-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-neutral-400">System Status</span>
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
          </div>
          <p className="text-xs text-green-400 font-medium">Online</p>
          <div className="mt-3 space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-neutral-500">Active Trades</span>
              <span className="text-white font-medium">342</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-neutral-500">24h Volume</span>
              <span className="text-white font-medium">$2.4M</span>
            </div>
          </div>
        </div>
      </div>
    </motion.aside>
  );
}