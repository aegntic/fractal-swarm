'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { 
  Play, 
  Pause, 
  Square, 
  Settings, 
  AlertTriangle, 
  TrendingUp,
  Zap,
  Target,
  Shield,
  DollarSign
} from 'lucide-react';
import { useTradingStore } from '@/store/trading';
import { motion } from 'framer-motion';

interface TradingControlsProps {
  className?: string;
}

export function TradingControls({ className }: TradingControlsProps) {
  const store = useTradingStore();
  
  // Mock trading state
  const isTrading = true;
  const tradingMode = 'active';
  const riskLevel = 35;
  const capitalAllocation = 80;
  const maxPositionSize = 15;
  const stopLossPercentage = 5;
  const takeProfitPercentage = 25;

  const [localSettings, setLocalSettings] = useState({
    riskLevel,
    capitalAllocation,
    maxPositionSize,
    stopLossPercentage,
    takeProfitPercentage
  });

  const handleSettingsUpdate = () => {
    console.log('Settings updated:', localSettings);
  };

  const getRiskColor = (level: number) => {
    if (level <= 30) return 'text-green-400';
    if (level <= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getTradingStatusColor = () => {
    if (tradingMode === 'active') return 'bg-green-500';
    return 'bg-green-500'; // Default to green for demo
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`w-full ${className}`}
    >
      <Card className="bg-dark-800/90 border-dark-600 backdrop-blur-xl">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2">
              <Settings className="w-5 h-5 text-neon-blue" />
              Trading Controls
            </CardTitle>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${getTradingStatusColor()}`} />
              <Badge variant="outline" className="text-white border-dark-500">
                {tradingMode.toUpperCase()}
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Main Controls */}
          <div className="flex gap-3">
            <Button
              onClick={() => console.log('Start trading')}
              disabled={isTrading && tradingMode === 'active'}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white"
            >
              <Play className="w-4 h-4 mr-2" />
              Start
            </Button>
            <Button
              onClick={() => console.log('Pause trading')}
              disabled={!isTrading}
              className="flex-1 bg-yellow-600 hover:bg-yellow-700 text-white"
            >
              <Pause className="w-4 h-4 mr-2" />
              Pause
            </Button>
            <Button
              onClick={() => console.log('Stop trading')}
              disabled={!isTrading}
              className="flex-1 bg-red-600 hover:bg-red-700 text-white"
            >
              <Square className="w-4 h-4 mr-2" />
              Stop
            </Button>
          </div>

          {/* Settings Tabs */}
          <Tabs defaultValue="risk" className="w-full">
            <TabsList className="grid w-full grid-cols-4 bg-dark-700">
              <TabsTrigger value="risk" className="text-white data-[state=active]:bg-neon-blue/20">
                <Shield className="w-4 h-4 mr-1" />
                Risk
              </TabsTrigger>
              <TabsTrigger value="capital" className="text-white data-[state=active]:bg-neon-blue/20">
                <DollarSign className="w-4 h-4 mr-1" />
                Capital
              </TabsTrigger>
              <TabsTrigger value="position" className="text-white data-[state=active]:bg-neon-blue/20">
                <Target className="w-4 h-4 mr-1" />
                Position
              </TabsTrigger>
              <TabsTrigger value="advanced" className="text-white data-[state=active]:bg-neon-blue/20">
                <Zap className="w-4 h-4 mr-1" />
                Advanced
              </TabsTrigger>
            </TabsList>

            <TabsContent value="risk" className="space-y-4 mt-4">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-white font-medium">Risk Level</label>
                  <span className={`font-mono ${getRiskColor(localSettings.riskLevel)}`}>
                    {localSettings.riskLevel}%
                  </span>
                </div>
                <Slider
                  value={[localSettings.riskLevel]}
                  onValueChange={([value]) => 
                    setLocalSettings(prev => ({ ...prev, riskLevel: value }))
                  }
                  min={10}
                  max={90}
                  step={5}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-400">
                  <span>Conservative</span>
                  <span>Moderate</span>
                  <span>Aggressive</span>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-white font-medium">Stop Loss</label>
                  <span className="text-red-400 font-mono">
                    -{localSettings.stopLossPercentage}%
                  </span>
                </div>
                <Slider
                  value={[localSettings.stopLossPercentage]}
                  onValueChange={([value]) => 
                    setLocalSettings(prev => ({ ...prev, stopLossPercentage: value }))
                  }
                  min={1}
                  max={20}
                  step={0.5}
                  className="w-full"
                />
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-white font-medium">Take Profit</label>
                  <span className="text-green-400 font-mono">
                    +{localSettings.takeProfitPercentage}%
                  </span>
                </div>
                <Slider
                  value={[localSettings.takeProfitPercentage]}
                  onValueChange={([value]) => 
                    setLocalSettings(prev => ({ ...prev, takeProfitPercentage: value }))
                  }
                  min={5}
                  max={100}
                  step={5}
                  className="w-full"
                />
              </div>
            </TabsContent>

            <TabsContent value="capital" className="space-y-4 mt-4">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-white font-medium">Capital Allocation</label>
                  <span className="text-neon-blue font-mono">
                    {localSettings.capitalAllocation}%
                  </span>
                </div>
                <Slider
                  value={[localSettings.capitalAllocation]}
                  onValueChange={([value]) => 
                    setLocalSettings(prev => ({ ...prev, capitalAllocation: value }))
                  }
                  min={10}
                  max={95}
                  step={5}
                  className="w-full"
                />
                <p className="text-xs text-gray-400">
                  Percentage of total capital to use for trading
                </p>
              </div>
            </TabsContent>

            <TabsContent value="position" className="space-y-4 mt-4">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-white font-medium">Max Position Size</label>
                  <span className="text-neon-blue font-mono">
                    {localSettings.maxPositionSize}%
                  </span>
                </div>
                <Slider
                  value={[localSettings.maxPositionSize]}
                  onValueChange={([value]) => 
                    setLocalSettings(prev => ({ ...prev, maxPositionSize: value }))
                  }
                  min={1}
                  max={25}
                  step={1}
                  className="w-full"
                />
                <p className="text-xs text-gray-400">
                  Maximum percentage per individual position
                </p>
              </div>
            </TabsContent>

            <TabsContent value="advanced" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center justify-between p-3 bg-dark-700 rounded-lg">
                  <div>
                    <label className="text-white font-medium">Auto Rebalance</label>
                    <p className="text-xs text-gray-400">Automatic portfolio rebalancing</p>
                  </div>
                  <Switch />
                </div>
                <div className="flex items-center justify-between p-3 bg-dark-700 rounded-lg">
                  <div>
                    <label className="text-white font-medium">MEV Hunting</label>
                    <p className="text-xs text-gray-400">Enable MEV opportunity detection</p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between p-3 bg-dark-700 rounded-lg">
                  <div>
                    <label className="text-white font-medium">Smart Slippage</label>
                    <p className="text-xs text-gray-400">Dynamic slippage adjustment</p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between p-3 bg-dark-700 rounded-lg">
                  <div>
                    <label className="text-white font-medium">Flash Loans</label>
                    <p className="text-xs text-gray-400">Enable flash loan strategies</p>
                  </div>
                  <Switch />
                </div>
              </div>
            </TabsContent>
          </Tabs>

          {/* Apply Settings Button */}
          <div className="pt-4 border-t border-dark-600">
            <Button
              onClick={handleSettingsUpdate}
              className="w-full bg-neon-blue hover:bg-neon-blue/80 text-dark-900 font-semibold"
            >
              <TrendingUp className="w-4 h-4 mr-2" />
              Apply Settings
            </Button>
          </div>

          {/* Warning */}
          <div className="flex items-start gap-2 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
            <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-yellow-200">
              Changes will be applied to all active clones. Monitor performance closely after adjustments.
            </p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}