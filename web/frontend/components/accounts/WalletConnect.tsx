'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Wallet,
  Link,
  CheckCircle,
  XCircle,
  Loader2,
  Copy,
  ExternalLink,
  Shield,
  Unlink
} from 'lucide-react'

interface ConnectedWallet {
  address: string
  chain: string
  chainId: number
  balance: string
  provider: string
  isConnected: boolean
  ensName?: string
}

interface WalletProvider {
  id: string
  name: string
  icon: string
  installed: boolean
}

const SUPPORTED_WALLETS: WalletProvider[] = [
  { id: 'metamask', name: 'MetaMask', icon: '🦊', installed: false },
  { id: 'walletconnect', name: 'WalletConnect', icon: '🔗', installed: true },
  { id: 'coinbase', name: 'Coinbase Wallet', icon: '💙', installed: false },
  { id: 'rainbow', name: 'Rainbow', icon: '🌈', installed: false },
  { id: 'phantom', name: 'Phantom', icon: '👻', installed: false },
]

const SUPPORTED_CHAINS = [
  { id: 1, name: 'Ethereum', icon: 'Ξ', color: 'bg-blue-500' },
  { id: 137, name: 'Polygon', icon: 'Ⓜ', color: 'bg-purple-500' },
  { id: 56, name: 'BSC', icon: 'BNB', color: 'bg-yellow-500' },
  { id: 42161, name: 'Arbitrum', icon: 'ARB', color: 'bg-blue-600' },
  { id: 10, name: 'Optimism', icon: 'OP', color: 'bg-red-500' },
]

export default function WalletConnect() {
  const [connectedWallets, setConnectedWallets] = useState<ConnectedWallet[]>([])
  const [isConnecting, setIsConnecting] = useState(false)
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    checkInstalledWallets()
    loadConnectedWallets()
  }, [])

  const checkInstalledWallets = () => {
    // Check for installed wallet providers
    if (typeof window !== 'undefined') {
      SUPPORTED_WALLETS.forEach(wallet => {
        if (wallet.id === 'metamask' && (window as any).ethereum?.isMetaMask) {
          wallet.installed = true
        }
        // Add checks for other wallets
      })
    }
  }

  const loadConnectedWallets = async () => {
    try {
      const response = await fetch('/api/wallets')
      const data = await response.json()
      setConnectedWallets(data.wallets)
    } catch (error) {
      console.error('Failed to load wallets:', error)
    }
  }

  const connectWallet = async (providerId: string) => {
    setIsConnecting(true)
    setSelectedProvider(providerId)
    setError(null)

    try {
      // Simulate wallet connection
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      const newWallet: ConnectedWallet = {
        address: '0x742d35Cc6634C0532925a3b844Bc9e7595f6bEd2',
        chain: 'Ethereum',
        chainId: 1,
        balance: '2.451',
        provider: providerId,
        isConnected: true,
        ensName: 'vitalik.eth'
      }
      
      setConnectedWallets([...connectedWallets, newWallet])
    } catch (error: any) {
      setError(error.message || 'Failed to connect wallet')
    } finally {
      setIsConnecting(false)
      setSelectedProvider(null)
    }
  }

  const disconnectWallet = async (address: string) => {
    try {
      await fetch(`/api/wallets/${address}`, { method: 'DELETE' })
      setConnectedWallets(connectedWallets.filter(w => w.address !== address))
    } catch (error) {
      console.error('Failed to disconnect wallet:', error)
    }
  }

  const copyAddress = (address: string) => {
    navigator.clipboard.writeText(address)
    // You could add a toast notification here
  }

  const getChainInfo = (chainId: number) => {
    return SUPPORTED_CHAINS.find(chain => chain.id === chainId) || {
      id: chainId,
      name: 'Unknown',
      icon: '?',
      color: 'bg-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      {/* Connected Wallets */}
      {connectedWallets.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Connected Wallets</h3>
          <div className="grid gap-4">
            {connectedWallets.map((wallet) => {
              const chainInfo = getChainInfo(wallet.chainId)
              return (
                <Card key={wallet.address}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg">
                          <Wallet className="w-5 h-5" />
                        </div>
                        <div>
                          <CardTitle className="text-lg">
                            {wallet.ensName || `${wallet.address.slice(0, 6)}...${wallet.address.slice(-4)}`}
                          </CardTitle>
                          <CardDescription className="flex items-center gap-2">
                            <Badge variant="outline" className={`${chainInfo.color} bg-opacity-10`}>
                              {chainInfo.icon} {chainInfo.name}
                            </Badge>
                            <span className="text-xs">{wallet.provider}</span>
                          </CardDescription>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {wallet.isConnected ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                          <XCircle className="w-4 h-4 text-red-500" />
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Balance</span>
                        <span className="font-semibold">{wallet.balance} ETH</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Address</span>
                        <div className="flex items-center gap-2">
                          <code className="text-xs bg-muted px-2 py-1 rounded">
                            {wallet.address.slice(0, 10)}...{wallet.address.slice(-8)}
                          </code>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyAddress(wallet.address)}
                          >
                            <Copy className="w-3 h-3" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => window.open(`https://etherscan.io/address/${wallet.address}`, '_blank')}
                          >
                            <ExternalLink className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                      <div className="flex gap-2 pt-2">
                        <Button variant="outline" size="sm" className="flex-1">
                          <Shield className="w-3 h-3 mr-2" />
                          Permissions
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => disconnectWallet(wallet.address)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Unlink className="w-3 h-3 mr-2" />
                          Disconnect
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      )}

      {/* Available Wallets */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Connect a Wallet</h3>
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {SUPPORTED_WALLETS.map((wallet) => (
            <Card
              key={wallet.id}
              className={`cursor-pointer transition-all hover:shadow-md ${
                selectedProvider === wallet.id ? 'ring-2 ring-primary' : ''
              }`}
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="text-3xl">{wallet.icon}</div>
                    <div>
                      <CardTitle className="text-lg">{wallet.name}</CardTitle>
                      <CardDescription>
                        {wallet.installed ? 'Installed' : 'Not installed'}
                      </CardDescription>
                    </div>
                  </div>
                  {!wallet.installed && wallet.id !== 'walletconnect' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => window.open(`https://www.${wallet.id}.io`, '_blank')}
                    >
                      <ExternalLink className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <Button
                  className="w-full"
                  onClick={() => connectWallet(wallet.id)}
                  disabled={!wallet.installed || isConnecting}
                >
                  {isConnecting && selectedProvider === wallet.id ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Connecting...
                    </>
                  ) : (
                    <>
                      <Link className="w-4 h-4 mr-2" />
                      Connect
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Security Notice */}
      <Alert>
        <Shield className="w-4 h-4" />
        <AlertDescription>
          <strong>Security Notice:</strong> Only connect wallets you trust. Never share your
          private keys or seed phrases with anyone.
        </AlertDescription>
      </Alert>
    </div>
  )
}