'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Key,
  Shield,
  AlertTriangle,
  CheckCircle,
  Copy,
  Eye,
  EyeOff,
  Plus,
  Trash2,
  RefreshCw,
  Lock,
  Unlock,
  Settings,
  Info
} from 'lucide-react'

interface APIKey {
  id: string
  name: string
  exchange: string
  permissions: string[]
  createdAt: Date
  lastUsed: Date
  status: 'active' | 'inactive' | 'expired'
  ipWhitelist: string[]
  isEncrypted: boolean
  keyPreview: string
}

export default function APIKeyManager() {
  const [apiKeys, setApiKeys] = useState<APIKey[]>([
    {
      id: '1',
      name: 'Main Trading Bot',
      exchange: 'binance',
      permissions: ['spot', 'futures', 'read', 'trade'],
      createdAt: new Date('2024-01-15'),
      lastUsed: new Date(),
      status: 'active',
      ipWhitelist: ['192.168.1.100', '10.0.0.5'],
      isEncrypted: true,
      keyPreview: 'Xk9p...3nR2'
    },
    {
      id: '2',
      name: 'Read-Only Analytics',
      exchange: 'coinbase',
      permissions: ['read'],
      createdAt: new Date('2024-02-01'),
      lastUsed: new Date(Date.now() - 86400000),
      status: 'active',
      ipWhitelist: [],
      isEncrypted: true,
      keyPreview: 'CB2a...9xP1'
    }
  ])

  const [showAddDialog, setShowAddDialog] = useState(false)
  const [showSecret, setShowSecret] = useState<string | null>(null)
  const [newKeyForm, setNewKeyForm] = useState({
    name: '',
    exchange: '',
    apiKey: '',
    apiSecret: '',
    passphrase: '',
    permissions: [] as string[]
  })

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-500/10 text-green-500">Active</Badge>
      case 'inactive':
        return <Badge className="bg-gray-500/10 text-gray-500">Inactive</Badge>
      case 'expired':
        return <Badge className="bg-red-500/10 text-red-500">Expired</Badge>
      default:
        return null
    }
  }

  const toggleKeyStatus = (keyId: string) => {
    setApiKeys(keys => 
      keys.map(key => 
        key.id === keyId 
          ? { ...key, status: key.status === 'active' ? 'inactive' : 'active' }
          : key
      )
    )
  }

  const deleteKey = (keyId: string) => {
    if (window.confirm('Are you sure you want to delete this API key?')) {
      setApiKeys(keys => keys.filter(key => key.id !== keyId))
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    // You could add a toast notification here
  }

  return (
    <div className="space-y-6">
      {/* Security Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Security Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <Lock className="w-5 h-5 text-green-500" />
              </div>
              <div>
                <p className="text-sm font-medium">Encryption</p>
                <p className="text-xs text-muted-foreground">All keys encrypted</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Shield className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <p className="text-sm font-medium">2FA Status</p>
                <p className="text-xs text-muted-foreground">Enabled</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <Key className="w-5 h-5 text-purple-500" />
              </div>
              <div>
                <p className="text-sm font-medium">Active Keys</p>
                <p className="text-xs text-muted-foreground">{apiKeys.filter(k => k.status === 'active').length} keys</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-500/10 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-yellow-500" />
              </div>
              <div>
                <p className="text-sm font-medium">Last Audit</p>
                <p className="text-xs text-muted-foreground">2 days ago</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* API Keys Management */}
      <Tabs defaultValue="keys">
        <div className="flex justify-between items-center mb-4">
          <TabsList>
            <TabsTrigger value="keys">API Keys</TabsTrigger>
            <TabsTrigger value="permissions">Permissions</TabsTrigger>
            <TabsTrigger value="audit">Audit Log</TabsTrigger>
          </TabsList>
          <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Add API Key
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Add New API Key</DialogTitle>
                <DialogDescription>
                  Securely add a new exchange API key. All keys are encrypted at rest.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 mt-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <Label>Key Name</Label>
                    <Input
                      placeholder="e.g., Main Trading Bot"
                      value={newKeyForm.name}
                      onChange={(e) => setNewKeyForm({ ...newKeyForm, name: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Exchange</Label>
                    <select
                      className="w-full h-10 px-3 rounded-md border border-input bg-background"
                      value={newKeyForm.exchange}
                      onChange={(e) => setNewKeyForm({ ...newKeyForm, exchange: e.target.value })}
                    >
                      <option value="">Select exchange</option>
                      <option value="binance">Binance</option>
                      <option value="coinbase">Coinbase</option>
                      <option value="kraken">Kraken</option>
                    </select>
                  </div>
                </div>
                <div>
                  <Label>API Key</Label>
                  <Input
                    type="password"
                    placeholder="Enter your API key"
                    value={newKeyForm.apiKey}
                    onChange={(e) => setNewKeyForm({ ...newKeyForm, apiKey: e.target.value })}
                  />
                </div>
                <div>
                  <Label>API Secret</Label>
                  <Input
                    type="password"
                    placeholder="Enter your API secret"
                    value={newKeyForm.apiSecret}
                    onChange={(e) => setNewKeyForm({ ...newKeyForm, apiSecret: e.target.value })}
                  />
                </div>
                <Alert>
                  <Info className="w-4 h-4" />
                  <AlertDescription>
                    Your API keys are encrypted using AES-256 encryption and stored securely.
                    We never store plain text credentials.
                  </AlertDescription>
                </Alert>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setShowAddDialog(false)}>
                    Cancel
                  </Button>
                  <Button onClick={() => setShowAddDialog(false)}>
                    Add Key
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        <TabsContent value="keys" className="space-y-4">
          {apiKeys.map((apiKey) => (
            <Card key={apiKey.id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Key className="w-5 h-5" />
                      {apiKey.name}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      {apiKey.exchange.charAt(0).toUpperCase() + apiKey.exchange.slice(1)} API Key
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(apiKey.status)}
                    {apiKey.isEncrypted && (
                      <Badge variant="secondary">
                        <Lock className="w-3 h-3 mr-1" />
                        Encrypted
                      </Badge>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <p className="text-sm text-muted-foreground">API Key</p>
                    <div className="flex items-center gap-2 mt-1">
                      <code className="text-sm bg-muted px-2 py-1 rounded">
                        {showSecret === apiKey.id ? 'Xk9pL2mN3oR4sT5uV6wX7yZ8' : apiKey.keyPreview}
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowSecret(showSecret === apiKey.id ? null : apiKey.id)}
                      >
                        {showSecret === apiKey.id ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard('API_KEY_HERE')}
                      >
                        <Copy className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Created</p>
                    <p className="text-sm mt-1">{apiKey.createdAt.toLocaleDateString()}</p>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground mb-2">Permissions</p>
                  <div className="flex gap-2 flex-wrap">
                    {apiKey.permissions.map(perm => (
                      <Badge key={perm} variant="secondary">
                        {perm}
                      </Badge>
                    ))}
                  </div>
                </div>

                {apiKey.ipWhitelist.length > 0 && (
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">IP Whitelist</p>
                    <div className="flex gap-2 flex-wrap">
                      {apiKey.ipWhitelist.map(ip => (
                        <Badge key={ip} variant="outline">
                          {ip}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between pt-4 border-t">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <CheckCircle className="w-4 h-4" />
                    Last used: {apiKey.lastUsed.toLocaleString()}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => toggleKeyStatus(apiKey.id)}
                    >
                      {apiKey.status === 'active' ? (
                        <>
                          <Lock className="w-3 h-3 mr-2" />
                          Disable
                        </>
                      ) : (
                        <>
                          <Unlock className="w-3 h-3 mr-2" />
                          Enable
                        </>
                      )}
                    </Button>
                    <Button variant="outline" size="sm">
                      <RefreshCw className="w-3 h-3 mr-2" />
                      Rotate
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => deleteKey(apiKey.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="permissions">
          <Card>
            <CardHeader>
              <CardTitle>Permission Management</CardTitle>
              <CardDescription>
                Configure default permissions and security settings for API keys
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Require IP Whitelist</p>
                    <p className="text-sm text-muted-foreground">
                      All API keys must have IP restrictions
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Auto-disable Inactive Keys</p>
                    <p className="text-sm text-muted-foreground">
                      Disable keys not used for 30 days
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Withdrawal Whitelist</p>
                    <p className="text-sm text-muted-foreground">
                      Restrict withdrawals to whitelisted addresses
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="audit">
          <Card>
            <CardHeader>
              <CardTitle>API Key Audit Log</CardTitle>
              <CardDescription>
                Recent API key activities and security events
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { action: 'API Key Created', key: 'Main Trading Bot', time: '2 hours ago', icon: Plus },
                  { action: 'Key Rotated', key: 'Analytics Key', time: '1 day ago', icon: RefreshCw },
                  { action: 'Key Disabled', key: 'Old Bot Key', time: '3 days ago', icon: Lock },
                  { action: 'Failed Auth Attempt', key: 'Main Trading Bot', time: '5 days ago', icon: AlertTriangle },
                ].map((log, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-3 rounded-lg border">
                    <div className="p-2 bg-muted rounded-lg">
                      <log.icon className="w-4 h-4" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{log.action}</p>
                      <p className="text-xs text-muted-foreground">{log.key}</p>
                    </div>
                    <p className="text-xs text-muted-foreground">{log.time}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Security Recommendations */}
      <Alert>
        <AlertTriangle className="w-4 h-4" />
        <AlertDescription>
          <strong>Security Reminder:</strong> Never share your API keys. Enable 2FA on all exchange
          accounts and use IP whitelisting when possible. Regularly rotate your keys for maximum security.
        </AlertDescription>
      </Alert>
    </div>
  )
}