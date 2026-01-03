# Admin Dashboard - User Guide

Complete web-based admin interface for the Distributed Multi-Agent Coordination Platform.

## 🚀 Quick Start

```bash
# 1. Ensure services are running
make start

# 2. Start the admin dashboard
./scripts/start_admin.sh

# 3. Open in browser
open http://localhost:8000
```

## ✨ Features

### 1. **Real-Time Node Visualization**
- Visual network topology of all 3 CouchDB nodes
- Live document counts per node
- Document distribution by type (agents, tasks, knowledge, etc.)
- Node health status monitoring

### 2. **Replication Control**
- Enable/disable replication between any two nodes
- Visual replication status
- Real-time replication metrics

### 3. **Data Generation**
- Manual data generation with custom parameters
- Bring Your Own OpenRouter API Key (BYOK)
- Configurable amounts for:
  - Agents
  - Tasks
  - Knowledge documents
  - Agent states
  - Consensus decisions

### 4. **Automatic Data Generation**
- Schedule automatic data generation every 3-10 minutes
- Persistent API key storage
- Next run time display
- Last generation timestamp

### 5. **Live Metrics & Monitoring**
- Real-time statistics dashboard
- Prometheus metrics integration
- Grafana dashboard access
- API request tracking

### 6. **Quick Access Links**
- CouchDB Admin Interface
- Grafana Dashboards
- Prometheus Metrics
- Raw metrics endpoint

## 📊 Dashboard Sections

### Statistics Overview
- **Total Documents**: All documents across all nodes
- **Active Agents**: Currently active agents
- **Pending Tasks**: Tasks waiting to be processed
- **Active Replications**: Number of active replication streams

### Network Topology
Interactive visualization showing:
- All 3 CouchDB nodes
- Replication connections
- Real-time status updates

### Node Status Cards
Each node displays:
- Health status (green pulse = healthy)
- Total document count
- Documents broken down by type:
  - Agents
  - Tasks
  - Knowledge
  - Agent States
  - Consensus Decisions

## 🔄 Replication Control

### Enable Replication

1. Select **Source Node** from dropdown
2. Select **Target Node** from dropdown
3. Click **✅ Enable**

Replication will start immediately and continuously sync data from source to target.

### Disable Replication

1. Select **Source Node** and **Target Node**
2. Click **❌ Disable**

This stops the replication stream between the selected nodes.

### Common Configurations

**Full Mesh Replication** (all nodes sync with each other):
- Node 1 → Node 2
- Node 1 → Node 3
- Node 2 → Node 1
- Node 2 → Node 3
- Node 3 → Node 1
- Node 3 → Node 2

**Star Topology** (Node 1 as hub):
- Node 1 → Node 2
- Node 1 → Node 3
- Node 2 → Node 1
- Node 3 → Node 1

## 🎲 Data Generation

### Manual Generation

1. **(Optional)** Enter your OpenRouter API key
   - Format: `sk-or-v1-...`
   - Used for AI-generated content
   - If not provided, uses template-based generation

2. Set quantities:
   - **Agents**: Number of agent documents (default: 10)
   - **Tasks**: Number of task documents (default: 30)
   - **Knowledge**: Number of knowledge documents (default: 15)
   - **States**: Number of agent state snapshots (default: 20)

3. Click **🚀 Generate Now**

4. Data generation runs in background
   - Status message appears
   - Dashboard refreshes automatically after completion

### Automatic Generation

Configure scheduled data generation:

1. **Enable automatic generation**
   - Check the "Enable automatic data generation" checkbox

2. **Set interval**
   - Enter interval in minutes (3-10 minutes)
   - Recommended: 5 minutes for testing

3. **(Optional)** Save your OpenRouter API key
   - Key is used for all automatic generations
   - Stored in server memory (not persisted to disk)

4. Click **💾 Save Settings**

5. Monitor status:
   - **Enabled**: Yes/No
   - **Interval**: Minutes between generations
   - **Last Run**: Timestamp of last generation
   - **Next Run**: When next generation will occur

### OpenRouter API Key (BYOK)

**Why provide your own key?**
- Generate more realistic AI-powered content
- Better quality task descriptions
- More diverse agent capabilities
- Richer knowledge base entries

**How to get a key:**
1. Visit https://openrouter.ai
2. Sign up for an account
3. Generate an API key
4. Paste into the dashboard

**What if I don't have a key?**
- System uses template-based generation
- Still creates valid test data
- Less variety in content

## 📈 Metrics & Monitoring

### Prometheus Metrics

Access raw metrics at: http://localhost:8000/metrics

**Available Metrics:**
- `admin_api_requests_total` - Total API requests by endpoint
- `couchdb_replication_status` - Replication status by source/target
- `couchdb_node_documents` - Document count per node and type
- `data_generation_total` - Total data generation runs
- `data_generation_duration_seconds` - Time taken to generate data
- `couchdb_active_replications` - Number of active replications

### Grafana Dashboards

Access Grafana at: http://localhost:3000
- Username: `admin`
- Password: `admin`

**Pre-configured Dashboard:**
- "Distributed Agent Platform - Testing Metrics"
- Real-time document counts
- Replication status
- Data generation metrics
- API performance

## 🔗 Quick Access

| Service | URL | Credentials |
|---------|-----|-------------|
| **Admin Dashboard** | http://localhost:8000 | None |
| **Prometheus** | http://localhost:9090 | None |
| **Grafana** | http://localhost:3000 | admin / admin |
| **CouchDB** | http://localhost:5984/_utils | admin / password |
| **Metrics Endpoint** | http://localhost:8000/metrics | None |

## 🔧 API Endpoints

The admin dashboard provides a REST API:

### Health Check
```bash
GET /api/health
```

### Get All Nodes
```bash
GET /api/nodes
```
Returns status and document counts for all nodes.

### Get Replications
```bash
GET /api/replications
```
Returns list of all replication configurations.

### Control Replication
```bash
POST /api/replication/control
Content-Type: application/json

{
  "source_node": "http://localhost:5984",
  "target_node": "http://localhost:5985",
  "enable": true
}
```

### Generate Data
```bash
POST /api/data/generate
Content-Type: application/json

{
  "openrouter_key": "sk-or-v1-...",
  "agents": 10,
  "tasks": 30,
  "knowledge": 15,
  "states": 20,
  "decisions": 5
}
```

### Configure Auto-Generation
```bash
POST /api/data/auto-generate
Content-Type: application/json

{
  "enabled": true,
  "interval_minutes": 5,
  "openrouter_key": "sk-or-v1-..."
}
```

### Get Auto-Generation Status
```bash
GET /api/data/auto-generate/status
```

### Get Statistics
```bash
GET /api/stats
```
Returns platform-wide statistics.

### Prometheus Metrics
```bash
GET /metrics
```
Returns Prometheus-formatted metrics.

## 🎨 UI Features

### Auto-Refresh
- Dashboard refreshes every 10 seconds
- Latest data automatically loaded
- Last update time displayed

### Visual Indicators
- **Green pulsing dots**: Healthy nodes
- **Red dots**: Error/offline nodes
- **Real-time counters**: Live statistics
- **Interactive network graph**: Click and drag nodes

### Responsive Design
- Works on desktop and tablet
- Mobile-friendly layout
- Adaptive grid system

## 🔍 Monitoring Best Practices

1. **Check Node Status Regularly**
   - Ensure all nodes show "healthy"
   - Verify document counts are similar (for replicated setup)

2. **Monitor Replications**
   - Keep replication count stable
   - Watch for failed replications

3. **Track Data Generation**
   - Monitor generation duration
   - Check for errors in generation

4. **Use Grafana for Long-Term Trends**
   - View historical data
   - Identify patterns
   - Detect anomalies

## 🐛 Troubleshooting

### Dashboard Won't Load

```bash
# Check if admin API is running
curl http://localhost:8000/api/health

# Restart admin dashboard
./scripts/start_admin.sh
```

### Nodes Show as Offline

```bash
# Check CouchDB status
curl http://localhost:5984/_up
curl http://localhost:5985/_up
curl http://localhost:5986/_up

# Restart services if needed
make restart
```

### Replication Not Working

1. Check both nodes are healthy
2. Verify URLs are correct
3. Check Prometheus metrics:
   ```bash
   curl http://localhost:8000/metrics | grep replication
   ```

### Data Generation Fails

1. Verify OpenRouter key is correct (if provided)
2. Check CouchDB is accessible
3. View logs:
   ```bash
   # Check admin API logs in terminal
   ```

### Metrics Not Appearing in Grafana

1. Verify Prometheus is scraping admin API:
   - Open http://localhost:9090/targets
   - Look for "admin-api" target

2. Restart Prometheus:
   ```bash
   docker restart prometheus
   ```

3. Check Grafana datasource:
   - Configuration → Data Sources
   - Test connection

## 🔒 Security Notes

⚠️ **For Development/Testing Only**

- No authentication on admin dashboard
- API keys stored in memory only
- Metrics endpoint is public
- Do not expose to internet

**For Production:**
- Add authentication (OAuth, JWT, etc.)
- Encrypt API keys
- Use HTTPS
- Implement rate limiting
- Add audit logging

## 📝 Example Workflows

### Testing Replication

1. Open admin dashboard
2. Note document counts on all nodes
3. Disable all replications
4. Generate data (agents=5, tasks=10)
5. Note only Node 1 has new data
6. Enable Node 1 → Node 2 replication
7. Wait 10-30 seconds
8. Refresh dashboard
9. Verify Node 2 now has same document count

### Automated Testing

1. Enable auto-generation (5-minute interval)
2. Set up full mesh replication
3. Open Grafana dashboard
4. Watch data grow over time
5. Monitor replication lag
6. Verify all nodes stay in sync

### Load Testing

1. Set auto-generation interval to 3 minutes
2. Set high data amounts (agents=50, tasks=100)
3. Enable all replications
4. Monitor Grafana for:
   - Document growth rate
   - Replication lag
   - API response times
   - System resource usage

## 🚀 Advanced Usage

### Custom Metrics

Add your own metrics in [src/api/admin_api.py](src/api/admin_api.py):

```python
from prometheus_client import Counter, Gauge

my_metric = Counter('my_custom_metric', 'Description')
my_metric.inc()  # Increment
```

### Custom Dashboards

Create new Grafana dashboards:
1. Open Grafana
2. Create → Dashboard
3. Add panels with PromQL queries
4. Save dashboard

### Webhook Integration

Extend the API to send webhooks on events:
```python
@app.post("/api/data/generate")
async def generate_data(...):
    # Generate data
    # Send webhook
    requests.post('https://webhook.site/...', json={...})
```

## 📚 Related Documentation

- [TESTING_README.md](TESTING_README.md) - Testing guide
- [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md) - Comprehensive testing
- [docs/TEST_CREDENTIALS.md](docs/TEST_CREDENTIALS.md) - All credentials
- [README.md](README.md) - Main project documentation

## 🎉 You're Ready!

The admin dashboard provides complete control over your distributed agent platform. Use it to:
- Monitor system health
- Control replication
- Generate test data
- Track metrics
- Visualize topology

Happy testing! 🚀
