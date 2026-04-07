'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  Home, 
  TrendingUp, 
  BarChart3, 
  Wallet, 
  Settings, 
  Users,
  Zap,
  History,
  Shield,
  HelpCircle,
  ChevronRight
} from 'lucide-react';
import { colors, glassStyle } from '@/lib/design-system';

interface NavItem {
  icon: React.ElementType;
  label: string;
  href: string;
  badge?: string;
  active?: boolean;
}

const navItems: NavItem[] = [
  { icon: Home, label: 'Dashboard', href: '/', active: true },
  { icon: TrendingUp, label: 'Trading', href: '/trading', badge: 'Live' },
  { icon: BarChart3, label: 'Analytics', href: '/analytics' },
  { icon: Users, label: 'Swarm Status', href: '/swarm', badge: '27' },
  { icon: Zap, label: 'MEV Hunter', href: '/mev' },
  { icon: Wallet, label: 'Portfolio', href: '/portfolio' },
  { icon: History, label: 'History', href: '/history' },
  { icon: Shield, label: 'Risk Control', href: '/risk' },
  { icon: Settings, label: 'Settings', href: '/settings' },
  { icon: HelpCircle, label: 'Help', href: '/help' },
];

export default function Sidebar() {
  return (
    <motion.aside
      initial={{ x: -250 }}
      animate={{ x: 0 }}
      transition={{ duration: 0.3 }}
      className="fixed left-0 top-0 h-full w-64 z-40"
      style={{
        ...glassStyle,
        borderRight: `1px solid ${colors.neutral[800]}`,
        background: colors.background.secondary,
      }}
    >
      <div className="flex flex-col h-full">
        {/* Logo */}
        <div className="p-6 border-b border-neutral-800">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="flex items-center gap-3"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-teal-400 flex items-center justify-center">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Quantum Swarm</h1>
              <p className="text-xs text-neutral-400">Trading System v1.0</p>
            </div>
          </motion.div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 overflow-y-auto">
          <ul className="space-y-1">
            {navItems.map((item, index) => (
              <motion.li
                key={item.label}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 + index * 0.05 }}
              >
                <a
                  href={item.href}
                  className={`
                    flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200
                    ${item.active 
                      ? 'bg-primary-500/20 text-primary-400 shadow-lg shadow-primary-500/10' 
                      : 'text-neutral-400 hover:text-white hover:bg-neutral-800/50'
                    }
                  `}
                >
                  <item.icon className="w-5 h-5 flex-shrink-0" />
                  <span className="flex-1 font-medium">{item.label}</span>
                  {item.badge && (
                    <span className={`
                      px-2 py-0.5 text-xs rounded-full
                      ${item.badge === 'Live' 
                        ? 'bg-green-500/20 text-green-400' 
                        : 'bg-neutral-700 text-neutral-300'
                      }
                    `}>
                      {item.badge}
                    </span>
                  )}
                  {item.active && (
                    <ChevronRight className="w-4 h-4" />
                  )}
                </a>
              </motion.li>
            ))}
          </ul>
        </nav>

        {/* Bottom Stats */}
        <div className="p-4 border-t border-neutral-800">
          <div className="space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-neutral-400">System Status</span>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-green-400">Online</span>
              </div>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-neutral-400">Active Trades</span>
              <span className="text-white font-semibold">342</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-neutral-400">24h Volume</span>
              <span className="text-white font-semibold">$2.4M</span>
            </div>
          </div>
        </div>
      </div>
    </motion.aside>
  );
}