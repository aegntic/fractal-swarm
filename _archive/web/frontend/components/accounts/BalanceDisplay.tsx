'use client'

import React, { useState, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid
} from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Eye,
  EyeOff,
  RefreshCw,
  Download,
  Filter
} from 'lucide-react'

interface Account {
  id: string
  name: string
  type: 'wallet' | 'exchange'
  provider: string
  balanceUSD: number
  assets: Asset[]
}

interface Asset {
  symbol: string
  name: string
  balance: number
  balanceUSD: number
  price: number
  change24h: number
}

interface BalanceDisplayProps {
  accounts: Account[]
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D']

export default function BalanceDisplay({ accounts }: BalanceDisplayProps) {
  const [showBalances, setShowBalances] = useState(true)
  const [selectedAsset, setSelectedAsset] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'allocation' | 'performance'>('allocation')

  // Aggregate all assets across accounts
  const aggregatedAssets = useMemo(() => {
    const assetMap = new Map<string, Asset>()
    
    accounts.forEach(account => {
      account.assets.forEach(asset => {
        if (assetMap.has(asset.symbol)) {
          const existing = assetMap.get(asset.symbol)!
          assetMap.set(asset.symbol, {
            ...existing,
            balance: existing.balance + asset.balance,
            balanceUSD: existing.balanceUSD + asset.balanceUSD
          })
        } else {
          assetMap.set(asset.symbol, { ...asset })
        }
      })
    })
    
    return Array.from(assetMap.values()).sort((a, b) => b.balanceUSD - a.balanceUSD)
  }, [accounts])

  const totalBalance = useMemo(() => {
    return aggregatedAssets.reduce((sum, asset) => sum + asset.balanceUSD, 0)
  }, [aggregatedAssets])

  const pieChartData = aggregatedAssets.map(asset => ({
    name: asset.symbol,
    value: asset.balanceUSD,
    percentage: ((asset.balanceUSD / totalBalance) * 100).toFixed(2)
  }))

  const performanceData = aggregatedAssets.map(asset => ({
    name: asset.symbol,
    value: asset.balanceUSD,
    change: asset.change24h,
    profit: asset.balanceUSD * (asset.change24h / 100)
  }))

  const formatBalance = (value: number) => {
    if (!showBalances) return '****'
    return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border rounded-lg p-3 shadow-lg">
          <p className="font-semibold">{payload[0].name}</p>
          <p className="text-sm">Value: ${formatBalance(payload[0].value)}</p>
          <p className="text-sm">Percentage: {payload[0].payload.percentage}%</p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Portfolio Breakdown</h3>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowBalances(!showBalances)}
          >
            {showBalances ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </Button>
          <Button variant="ghost" size="sm">
            <RefreshCw className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="sm">
            <Download className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* View Mode Tabs */}
      <Tabs defaultValue={viewMode}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="allocation">Asset Allocation</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="allocation" className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-2">
            {/* Pie Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Portfolio Distribution</CardTitle>
                <CardDescription>
                  Visual breakdown of your asset allocation
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Asset List */}
            <Card>
              <CardHeader>
                <CardTitle>Holdings</CardTitle>
                <CardDescription>
                  Detailed breakdown by asset
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-[300px] overflow-y-auto">
                  {aggregatedAssets.map((asset, index) => (
                    <div
                      key={asset.symbol}
                      className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 cursor-pointer transition-colors"
                      onClick={() => setSelectedAsset(asset.symbol)}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <div>
                          <p className="font-medium">{asset.symbol}</p>
                          <p className="text-sm text-muted-foreground">{asset.name}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">${formatBalance(asset.balanceUSD)}</p>
                        <div className="flex items-center gap-1 justify-end">
                          {asset.change24h >= 0 ? (
                            <TrendingUp className="w-3 h-3 text-green-500" />
                          ) : (
                            <TrendingDown className="w-3 h-3 text-red-500" />
                          )}
                          <span className={`text-sm ${asset.change24h >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                            {asset.change24h >= 0 ? '+' : ''}{asset.change24h.toFixed(2)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Selected Asset Details */}
          {selectedAsset && (
            <Card>
              <CardHeader>
                <CardTitle>Asset Details: {selectedAsset}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-4">
                  {accounts
                    .filter(acc => acc.assets.some(a => a.symbol === selectedAsset))
                    .map(account => {
                      const asset = account.assets.find(a => a.symbol === selectedAsset)!
                      return (
                        <div key={account.id} className="space-y-1">
                          <p className="text-sm font-medium">{account.name}</p>
                          <p className="text-2xl font-bold">${formatBalance(asset.balanceUSD)}</p>
                          <p className="text-sm text-muted-foreground">
                            {asset.balance} {asset.symbol}
                          </p>
                        </div>
                      )
                    })}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>24h Performance by Asset</CardTitle>
              <CardDescription>
                Profit/Loss breakdown for each holding
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="profit" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Performance Summary */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Gain/Loss</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold flex items-center gap-2">
                  {performanceData.reduce((sum, d) => sum + d.profit, 0) >= 0 ? (
                    <TrendingUp className="w-5 h-5 text-green-500" />
                  ) : (
                    <TrendingDown className="w-5 h-5 text-red-500" />
                  )}
                  ${formatBalance(Math.abs(performanceData.reduce((sum, d) => sum + d.profit, 0)))}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Best Performer</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {performanceData.sort((a, b) => b.change - a.change)[0]?.name || '-'}
                </div>
                <p className="text-sm text-green-500">
                  +{performanceData.sort((a, b) => b.change - a.change)[0]?.change.toFixed(2)}%
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Worst Performer</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {performanceData.sort((a, b) => a.change - b.change)[0]?.name || '-'}
                </div>
                <p className="text-sm text-red-500">
                  {performanceData.sort((a, b) => a.change - b.change)[0]?.change.toFixed(2)}%
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}