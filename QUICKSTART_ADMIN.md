# Admin Dashboard - Quick Start

## 🚀 Launch the Dashboard

```bash
# Start in one command
./scripts/start_admin.sh
```

Then open: **http://localhost:8000**

## 📊 What You Can Do

### 1. Monitor Nodes
- View all 3 CouchDB nodes
- See document counts in real-time
- Check node health status

### 2. Control Replication
```
1. Select source node (e.g., Node 1 - 5984)
2. Select target node (e.g., Node 2 - 5985)
3. Click "✅ Enable" to start replication
```

### 3. Generate Test Data
```
1. (Optional) Enter OpenRouter API key: sk-or-v1-...
2. Set amounts (Agents: 10, Tasks: 30, etc.)
3. Click "🚀 Generate Now"
```

### 4. Auto-Generate Every 3-10 Minutes
```
1. Check "Enable automatic data generation"
2. Set interval (3-10 minutes)
3. (Optional) Save OpenRouter key
4. Click "💾 Save Settings"
```

## 🔗 Quick Links from Dashboard

- **CouchDB Admin**: Click 📊 icon → Opens http://localhost:5984/_utils
- **Grafana**: Click 📈 icon → Opens http://localhost:3000
- **Prometheus**: Click 🎯 icon → Opens http://localhost:9090
- **Metrics**: Click 📊 icon → Opens /metrics endpoint

## 🎯 Common Tasks

### View Replication in Action

1. Note document count on Node 1
2. Disable all replications
3. Generate 10 agents, 20 tasks
4. Only Node 1 has new data
5. Enable Node 1 → Node 2 replication
6. Wait 30 seconds, refresh
7. Node 2 now has same data!

### Set Up Auto-Generation

1. Enable auto-generation
2. Set to 5 minutes
3. Paste your OpenRouter key (optional)
4. Save settings
5. Watch data grow automatically
6. Monitor in Grafana

### Monitor Live Metrics

1. Click "Grafana" link in dashboard
2. Login: admin / admin
3. Find "Distributed Agent Platform - Testing Metrics"
4. Watch live graphs update

## 📱 Dashboard Features

- **Auto-refresh**: Updates every 10 seconds
- **Status dots**: Green (healthy), Red (error)
- **Live counters**: Total docs, active agents, pending tasks
- **Network graph**: Interactive topology visualization
- **Quick actions**: One-click access to all services

## ⚙️ Credentials

| Service | Username | Password |
|---------|----------|----------|
| Dashboard | None | None |
| Grafana | admin | admin |
| CouchDB | admin | password |

## 🐛 Troubleshooting

**Dashboard won't open?**
```bash
# Check if running
curl http://localhost:8000/api/health

# Restart
./scripts/start_admin.sh
```

**Can't see nodes?**
```bash
# Check CouchDB is running
curl http://localhost:5984/_up

# Restart services
make restart
```

## 📚 Full Documentation

- **ADMIN_DASHBOARD.md** - Complete user guide with all features
- **TESTING_README.md** - Testing infrastructure overview
- **docs/TEST_CREDENTIALS.md** - All service credentials

## 🎉 You're Ready!

The admin dashboard is your control center for the distributed agent platform. Use it to monitor, control, and test your system!

**Dashboard URL**: http://localhost:8000
