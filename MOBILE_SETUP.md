# 📱 Quantum Swarm Trader - Mobile Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install textual rich  # For TUI

# Install web dependencies
cd web/backend
pip install fastapi uvicorn websockets aioredis

cd ../frontend
npm install
```

### 2. Start the System

#### Option A: Terminal UI (SSH-friendly)
```bash
# Basic TUI
python ui/tui_dashboard.py

# Simple Rich-based TUI
python ui/tui_dashboard.py --simple
```

#### Option B: Web Dashboard + Mobile PWA
```bash
# Terminal 1: Start backend
cd web/backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd web/frontend
npm run dev
```

### 3. Access on Mobile

#### Progressive Web App (Recommended)
1. Open your phone's browser
2. Navigate to `http://your-server-ip:3000`
3. Tap "Add to Home Screen" (iOS) or "Install App" (Android)
4. Launch from home screen for full-screen experience

#### Features on Mobile:
- **Real-time updates** via WebSocket
- **Push notifications** for important events
- **Offline viewing** of recent data
- **Touch-optimized** interface
- **Biometric authentication** (when implemented)

## Mobile-Specific Features

### 1. **Quick Actions**
- Swipe right: View clone details
- Swipe left: View recent trades
- Pull down: Refresh data
- Long press: Emergency stop

### 2. **Notifications**
Configure push notifications for:
- Clone spawning events
- Large profit trades (>5%)
- Risk alerts
- Phase transitions

### 3. **Widgets** (Coming Soon)
- iOS Widget: Capital & P&L at a glance
- Android Widget: Quick stats on home screen

## TUI Features (Terminal UI)

Perfect for SSH access from mobile terminals:

### Textual TUI Commands:
- `Q` - Quit
- `S` - Spawn clone
- `R` - Refresh
- `D` - Toggle dark mode
- `E` - Emergency stop

### Simple TUI Features:
- Automatic refresh every second
- Color-coded profit/loss
- ASCII performance charts
- Minimal bandwidth usage

## API Endpoints for Mobile Apps

If building a native mobile app, use these endpoints:

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://your-server:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'status_update') {
    updateUI(data.data);
  }
};
```

### REST API
```javascript
// Get status
GET /api/status

// Get clones
GET /api/clones

// Spawn clone
POST /api/clones/spawn
{
  "capital_allocation": 100,
  "chain": "solana"
}

// Emergency stop
POST /api/emergency-stop
{
  "reason": "Manual stop from mobile"
}
```

## Performance Tips

### For TUI:
1. Use `--simple` flag for lower bandwidth
2. SSH with compression: `ssh -C user@server`
3. Use tmux/screen for persistent sessions

### For Web/PWA:
1. Enable service worker for offline access
2. Use cellular data saver mode
3. Set update intervals based on connection

## Security on Mobile

1. **Always use HTTPS** in production
2. **Enable 2FA** for mobile access
3. **Set session timeouts** for auto-logout
4. **Use VPN** when on public WiFi
5. **Enable biometric lock** on app

## Troubleshooting

### TUI Issues
- **Garbled display**: Check terminal encoding (UTF-8)
- **Slow updates**: Increase refresh interval
- **Connection drops**: Use tmux/screen

### PWA Issues
- **Won't install**: Ensure HTTPS is enabled
- **No updates**: Clear cache and reinstall
- **WebSocket fails**: Check firewall settings

## Future Mobile Features

- [ ] React Native app
- [ ] iOS/Android widgets  
- [ ] Apple Watch companion
- [ ] Voice commands via Siri/Google
- [ ] AR portfolio visualization
- [ ] NFC tap to trade

## Quick Demo

Try the mobile experience now:

```bash
# Start demo
python example_usage.py

# Then access web UI
# http://localhost:3000
```

---

**Pro Tip**: For the best mobile experience, use the PWA with a modern browser (Chrome/Safari). The TUI is perfect for remote management via SSH clients like Termux (Android) or Blink (iOS).