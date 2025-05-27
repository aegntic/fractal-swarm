'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  AlertCircle,
  DollarSign,
  Activity,
  Shield,
  Plus
} from 'lucide-react'
import WalletConnect from './WalletConnect'
import ExchangeAccounts from './ExchangeAccounts'
import BalanceDisplay from './BalanceDisplay'
// import TransactionHistory from './TransactionHistory'
import APIKeyManager from './APIKeyManager'

interface Account {
  id: string
  name: string
  type: 'wallet' | 'exchange'
  provider: string
  address?: string
  balance: number
  balanceUSD: number
  health: 'good' | 'warning' | 'error'
  lastSync: Date
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

export default function AccountOverview() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [totalBalance, setTotalBalance] = useState(0)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null)

  useEffect(() => {
    fetchAccounts()
    const interval = setInterval(fetchAccounts, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchAccounts = async () => {
    try {
      const response = await fetch('/api/accounts')
      const data = await response.json()
      setAccounts(data.accounts)
      setTotalBalance(data.totalBalanceUSD)
    } catch (error) {
      console.error('Failed to fetch accounts:', error)
    }
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await fetchAccounts()
    setTimeout(() => setIsRefreshing(false), 1000)
  }

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'good': return 'text-green-500'
      case 'warning': return 'text-yellow-500'
      case 'error': return 'text-red-500'
      default: return 'text-gray-500'
    }
  }

  const getHealthBadge = (health: string) => {
    switch (health) {
      case 'good': return <Badge className="bg-green-500/10 text-green-500">Healthy</Badge>
      case 'warning': return <Badge className="bg-yellow-500/10 text-yellow-500">Warning</Badge>
      case 'error': return <Badge className="bg-red-500/10 text-red-500">Error</Badge>
      default: return null
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Account Management</h1>
          <p className="text-muted-foreground mt-1">
            Manage your wallets and exchange accounts
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button size="sm">
            <Plus className="w-4 h-4 mr-2" />
            Add Account
          </Button>
        </div>
      </div>

      {/* Total Balance Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="w-5 h-5" />
            Total Portfolio Value
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline gap-4">
            <span className="text-4xl font-bold">
              ${totalBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <Badge className="bg-green-500/10 text-green-500">
              <TrendingUp className="w-3 h-3 mr-1" />
              +12.5%
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            Across {accounts.length} accounts
          </p>
        </CardContent>
      </Card>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="wallets">Wallets</TabsTrigger>
          <TabsTrigger value="exchanges">Exchanges</TabsTrigger>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Account Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {accounts.map((account) => (
              <Card
                key={account.id}
                className="cursor-pointer hover:shadow-lg transition-shadow"
                onClick={() => setSelectedAccount(account)}
              >
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-2">
                      {account.type === 'wallet' ? (
                        <Wallet className="w-5 h-5" />
                      ) : (
                        <Activity className="w-5 h-5" />
                      )}
                      <CardTitle className="text-lg">{account.name}</CardTitle>
                    </div>
                    {getHealthBadge(account.health)}
                  </div>
                  <CardDescription>{account.provider}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <p className="text-2xl font-bold">
                        ${account.balanceUSD.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {account.assets.length} assets
                      </p>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Last sync</span>
                      <span>{new Date(account.lastSync).toLocaleTimeString()}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Quick Stats */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Active Accounts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{accounts.length}</div>
                <p className="text-xs text-muted-foreground">
                  {accounts.filter(a => a.type === 'wallet').length} wallets,{' '}
                  {accounts.filter(a => a.type === 'exchange').length} exchanges
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">24h Change</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold flex items-center gap-1">
                  <TrendingUp className="w-4 h-4 text-green-500" />
                  +$2,451.23
                </div>
                <p className="text-xs text-muted-foreground">+12.5%</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Security Score</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold flex items-center gap-1">
                  <Shield className="w-4 h-4 text-green-500" />
                  95/100
                </div>
                <p className="text-xs text-muted-foreground">Excellent</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Pending Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold flex items-center gap-1">
                  <AlertCircle className="w-4 h-4 text-yellow-500" />
                  3
                </div>
                <p className="text-xs text-muted-foreground">Requires attention</p>
              </CardContent>
            </Card>
          </div>

          {/* Balance Display */}
          <BalanceDisplay accounts={accounts} />
        </TabsContent>

        <TabsContent value="wallets">
          <WalletConnect />
        </TabsContent>

        <TabsContent value="exchanges">
          <ExchangeAccounts />
        </TabsContent>

        <TabsContent value="transactions">
          <div className="text-gray-400 p-4">Transaction history coming soon...</div>
        </TabsContent>

        <TabsContent value="settings">
          <APIKeyManager />
        </TabsContent>
      </Tabs>

      {/* Account Health Alerts */}
      {accounts.some(a => a.health !== 'good') && (
        <Alert>
          <AlertCircle className="w-4 h-4" />
          <AlertDescription>
            Some accounts require attention. Check the health status of your accounts.
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}