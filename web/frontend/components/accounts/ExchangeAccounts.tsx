'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Building,
  Key,
  CheckCircle,
  XCircle,
  AlertCircle,
  Plus,
  Settings,
  Shield,
  TrendingUp,
  Clock,
  DollarSign,
  Activity
} from 'lucide-react'

interface ExchangeAccount {
  id: string
  name: string
  exchange: string
  apiKeyName: string
  isActive: boolean
  permissions: string[]
  balance: {
    total: number
    available: number
    locked: number
  }
  tradingVolume24h: number
  profitLoss24h: number
  lastActivity: Date
  rateLimit: {
    used: number
    total: number
    resetAt: Date
  }
}

const SUPPORTED_EXCHANGES = [
  { id: 'binance', name: 'Binance', icon: '🔶', color: 'bg-yellow-500' },
  { id: 'coinbase', name: 'Coinbase', icon: '🔵', color: 'bg-blue-500' },
  { id: 'kraken', name: 'Kraken', icon: '🐙', color: 'bg-purple-500' },
  { id: 'okx', name: 'OKX', icon: '⚫', color: 'bg-gray-700' },
  { id: 'bybit', name: 'Bybit', icon: '📊', color: 'bg-orange-500' },
]

export default function ExchangeAccounts() {
  const [accounts, setAccounts] = useState<ExchangeAccount[]>([
    {
      id: '1',
      name: 'Main Trading Account',
      exchange: 'binance',
      apiKeyName: 'Trading Bot API',
      isActive: true,
      permissions: ['spot', 'futures', 'read', 'trade'],
      balance: {
        total: 15420.50,
        available: 12300.00,
        locked: 3120.50
      },
      tradingVolume24h: 45000,
      profitLoss24h: 234.56,
      lastActivity: new Date(),
      rateLimit: {
        used: 450,
        total: 1200,
        resetAt: new Date(Date.now() + 3600000)
      }
    },
    {
      id: '2',
      name: 'Arbitrage Account',
      exchange: 'coinbase',
      apiKeyName: 'Arbitrage Bot',
      isActive: true,
      permissions: ['spot', 'read', 'trade'],
      balance: {
        total: 8500.00,
        available: 8500.00,
        locked: 0
      },
      tradingVolume24h: 12000,
      profitLoss24h: -45.23,
      lastActivity: new Date(Date.now() - 300000),
      rateLimit: {
        used: 150,
        total: 600,
        resetAt: new Date(Date.now() + 3600000)
      }
    }
  ])

  const [activeTab, setActiveTab] = useState('active')
  const [showAddAccount, setShowAddAccount] = useState(false)

  const getExchangeInfo = (exchangeId: string) => {
    return SUPPORTED_EXCHANGES.find(ex => ex.id === exchangeId) || {
      id: exchangeId,
      name: exchangeId,
      icon: '🏦',
      color: 'bg-gray-500'
    }
  }

  const getRateLimitColor = (used: number, total: number) => {
    const percentage = (used / total) * 100
    if (percentage < 50) return 'text-green-500'
    if (percentage < 80) return 'text-yellow-500'
    return 'text-red-500'
  }

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Balance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${accounts.reduce((sum, acc) => sum + acc.balance.total, 0).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">Across all exchanges</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">24h Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${accounts.reduce((sum, acc) => sum + acc.tradingVolume24h, 0).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">Trading volume</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">24h P&L</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold flex items-center gap-1">
              {accounts.reduce((sum, acc) => sum + acc.profitLoss24h, 0) >= 0 ? (
                <TrendingUp className="w-4 h-4 text-green-500" />
              ) : (
                <TrendingUp className="w-4 h-4 text-red-500 rotate-180" />
              )}
              ${Math.abs(accounts.reduce((sum, acc) => sum + acc.profitLoss24h, 0)).toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground">
              {accounts.reduce((sum, acc) => sum + acc.profitLoss24h, 0) >= 0 ? 'Profit' : 'Loss'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Active Accounts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{accounts.filter(a => a.isActive).length}</div>
            <p className="text-xs text-muted-foreground">Of {accounts.length} total</p>
          </CardContent>
        </Card>
      </div>

      {/* Account Management Tabs */}
      <Tabs defaultValue={activeTab}>
        <div className="flex justify-between items-center mb-4">
          <TabsList>
            <TabsTrigger value="active">Active Accounts</TabsTrigger>
            <TabsTrigger value="all">All Accounts</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
          </TabsList>
          <Button onClick={() => setShowAddAccount(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Add Exchange
          </Button>
        </div>

        <TabsContent value="active" className="space-y-4">
          {accounts.filter(acc => acc.isActive).map((account) => {
            const exchangeInfo = getExchangeInfo(account.exchange)
            return (
              <Card key={account.id}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-3">
                      <div className={`text-2xl p-2 rounded-lg ${exchangeInfo.color} bg-opacity-10`}>
                        {exchangeInfo.icon}
                      </div>
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          {account.name}
                          <Badge className="bg-green-500/10 text-green-500">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Active
                          </Badge>
                        </CardTitle>
                        <CardDescription className="flex items-center gap-2 mt-1">
                          <Building className="w-3 h-3" />
                          {exchangeInfo.name}
                          <span className="text-xs">• API: {account.apiKeyName}</span>
                        </CardDescription>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">
                      <Settings className="w-4 h-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Balance Info */}
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Total Balance</p>
                      <p className="text-xl font-bold">${account.balance.total.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Available</p>
                      <p className="text-xl font-bold">${account.balance.available.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">In Orders</p>
                      <p className="text-xl font-bold">${account.balance.locked.toLocaleString()}</p>
                    </div>
                  </div>

                  {/* Performance Metrics */}
                  <div className="flex items-center justify-between py-3 border-t border-b">
                    <div className="flex items-center gap-2">
                      <Activity className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm">24h Volume: ${account.tradingVolume24h.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <DollarSign className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm">24h P&L: </span>
                      <span className={`font-semibold ${account.profitLoss24h >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {account.profitLoss24h >= 0 ? '+' : ''}
                        ${account.profitLoss24h.toFixed(2)}
                      </span>
                    </div>
                  </div>

                  {/* API Permissions */}
                  <div>
                    <p className="text-sm font-medium mb-2">API Permissions</p>
                    <div className="flex gap-2 flex-wrap">
                      {account.permissions.map(perm => (
                        <Badge key={perm} variant="secondary" className="text-xs">
                          <Shield className="w-3 h-3 mr-1" />
                          {perm}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Rate Limit Status */}
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">API Rate Limit</p>
                      <p className={`text-sm font-medium ${getRateLimitColor(account.rateLimit.used, account.rateLimit.total)}`}>
                        {account.rateLimit.used} / {account.rateLimit.total} requests
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">Last Activity</p>
                      <p className="text-sm flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(account.lastActivity).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </TabsContent>

        <TabsContent value="all">
          <Alert>
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>
              Showing all accounts including inactive ones. Inactive accounts cannot execute trades.
            </AlertDescription>
          </Alert>
        </TabsContent>

        <TabsContent value="performance">
          <Card>
            <CardHeader>
              <CardTitle>Performance Analytics</CardTitle>
              <CardDescription>
                Detailed performance metrics across all exchange accounts
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Performance charts and analytics coming soon...</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Security Alert */}
      <Alert>
        <Shield className="w-4 h-4" />
        <AlertDescription>
          <strong>Security Best Practices:</strong> Use API keys with minimal required permissions,
          enable IP whitelisting, and regularly rotate your keys.
        </AlertDescription>
      </Alert>
    </div>
  )
}