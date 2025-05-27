'use client';

import React from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Zap, 
  Users, 
  DollarSign,
  AlertCircle 
} from 'lucide-react';

interface Activity {
  id: string;
  type: 'trade' | 'clone' | 'mev' | 'alert';
  action: string;
  value?: string;
  time: string;
  status: 'success' | 'warning' | 'error';
}

export default function ActivityFeed() {
  const activities: Activity[] = [
    {
      id: '1',
      type: 'trade',
      action: 'ETH/USDT Long',
      value: '+$342.50',
      time: '2m ago',
      status: 'success'
    },
    {
      id: '2',
      type: 'clone',
      action: 'Clone #28 spawned',
      time: '5m ago',
      status: 'success'
    },
    {
      id: '3',
      type: 'mev',
      action: 'MEV Captured',
      value: '+$89.20',
      time: '8m ago',
      status: 'success'
    },
    {
      id: '4',
      type: 'trade',
      action: 'BTC/USDT Short',
      value: '-$156.30',
      time: '12m ago',
      status: 'error'
    },
    {
      id: '5',
      type: 'alert',
      action: 'High volatility detected',
      time: '15m ago',
      status: 'warning'
    }
  ];

  const getIcon = (type: string) => {
    switch (type) {
      case 'trade': return TrendingUp;
      case 'clone': return Users;
      case 'mev': return Zap;
      case 'alert': return AlertCircle;
      default: return DollarSign;
    }
  };

  const getIconColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="space-y-3 max-h-64 overflow-y-auto pr-2">
      {activities.map((activity) => {
        const Icon = getIcon(activity.type);
        return (
          <div 
            key={activity.id} 
            className="flex items-start gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
          >
            <div className={`p-2 rounded-lg bg-white/5 ${getIconColor(activity.status)}`}>
              <Icon className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white font-medium truncate">
                {activity.action}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-gray-400">{activity.time}</span>
                {activity.value && (
                  <>
                    <span className="text-xs text-gray-400">•</span>
                    <span className={`text-xs font-semibold ${
                      activity.value.startsWith('+') ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {activity.value}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}