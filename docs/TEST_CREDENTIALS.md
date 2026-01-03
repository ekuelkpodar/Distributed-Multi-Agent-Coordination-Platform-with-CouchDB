# Test Admin Credentials

This document contains all test admin credentials for accessing the distributed agent platform services.

## 🔐 Service Credentials

### CouchDB

**Primary Node (Node 1)**
- URL: http://localhost:5984
- Admin Interface: http://localhost:5984/_utils
- Username: `admin`
- Password: `password`
- Database: `agent_coordination`

**Node 2 (Replica)**
- URL: http://localhost:5985
- Admin Interface: http://localhost:5985/_utils
- Username: `admin`
- Password: `password`

**Node 3 (Replica)**
- URL: http://localhost:5986
- Admin Interface: http://localhost:5986/_utils
- Username: `admin`
- Password: `password`

### Redis

- Host: `localhost`
- Port: `6379`
- Password: _(none)_
- Database: `0`

**Connection String**: `redis://localhost:6379/0`

**CLI Access**:
```bash
docker exec -it redis redis-cli
```

### Grafana

- URL: http://localhost:3000
- Username: `admin`
- Password: `admin`

**First Login**: You'll be prompted to change the password. For testing, you can skip this.

### Prometheus

- URL: http://localhost:9090
- Authentication: None (open access)

## 🧪 Test Data Access

### View Mock Data in CouchDB

1. Open CouchDB Admin: http://localhost:5984/_utils
2. Login with `admin` / `password`
3. Navigate to `agent_coordination` database
4. Browse documents by type:
   - Agents: Filter by `type: "agent"`
   - Tasks: Filter by `type: "task"`
   - Knowledge: Filter by `type: "knowledge"`
   - Agent States: Filter by `type: "agent_state"`
   - Decisions: Filter by `type: "consensus_decision"`

### Query Examples

**Get All Agents**:
```bash
curl -X GET http://admin:password@localhost:5984/agent_coordination/_design/agents/_view/by_status?key="active"
```

**Get All Pending Tasks**:
```bash
curl -X GET http://admin:password@localhost:5984/agent_coordination/_design/tasks/_view/by_status?key="pending"
```

**Get Task Statistics**:
```bash
curl -X GET http://admin:password@localhost:5984/agent_coordination/_design/tasks/_view/stats?group=true
```

### Redis Data Access

**View All Keys**:
```bash
docker exec -it redis redis-cli KEYS '*'
```

**Get Task Queue**:
```bash
docker exec -it redis redis-cli LRANGE task_queue 0 -1
```

**Check Agent Registry**:
```bash
docker exec -it redis redis-cli SMEMBERS active_agents
```

## 🔍 Monitoring Access

### Grafana Dashboards

After logging in to Grafana (http://localhost:3000):

1. Navigate to **Dashboards**
2. Default dashboards:
   - Agent Performance Metrics
   - Task Queue Statistics
   - System Health Overview

### Prometheus Metrics

Access Prometheus UI: http://localhost:9090

**Useful Queries**:

- Active agents: `agent_status{status="active"}`
- Task queue size: `task_queue_size`
- Task completion rate: `rate(tasks_completed[5m])`
- System uptime: `up`

## 🧪 Running Tests with Credentials

All credentials are pre-configured in `.env.test` file.

**Run Integration Tests**:
```bash
# Load test environment
cp .env.test .env

# Run all tests
pytest tests/test_integration.py -v

# Run specific test class
pytest tests/test_integration.py::TestDatabaseIntegration -v

# Run with coverage
pytest tests/test_integration.py --cov=src --cov-report=html
```

## 📊 Test Data Statistics

After running `scripts/generate_mock_data.py`, you should have:

- **10 Agents** (various types: research, analysis, coordination, etc.)
- **30 Tasks** (different statuses: pending, in_progress, completed, failed)
- **15 Knowledge Documents** (covering distributed systems topics)
- **20 Agent State Snapshots** (recent agent states)
- **5 Consensus Decisions** (approved/rejected proposals)

**Total**: ~80 test documents

## 🔄 Resetting Test Data

**Clear All Data**:
```bash
# Delete and recreate database
curl -X DELETE http://admin:password@localhost:5984/agent_coordination
python3 scripts/init_database.py

# Regenerate mock data
python3 scripts/generate_mock_data.py
```

**Clear Only Test Documents**:
```bash
# Delete documents with test prefixes
curl -X POST http://admin:password@localhost:5984/agent_coordination/_bulk_docs \
  -H "Content-Type: application/json" \
  -d '{"docs":[{"_id":"test_*","_deleted":true}]}'
```

## 🛠️ Troubleshooting

### CouchDB Access Issues

If you can't access CouchDB:

1. Check if Docker containers are running:
   ```bash
   docker ps
   ```

2. Check CouchDB logs:
   ```bash
   docker logs couchdb-node1
   ```

3. Verify health:
   ```bash
   curl http://localhost:5984/_up
   ```

### Redis Connection Issues

```bash
# Test Redis connection
docker exec -it redis redis-cli ping
# Should return: PONG
```

### Grafana Login Issues

If locked out of Grafana:

```bash
# Reset Grafana admin password
docker exec -it grafana grafana-cli admin reset-admin-password admin
```

## 🔒 Security Notes

⚠️ **These credentials are for LOCAL TESTING ONLY**

- Never use these credentials in production
- Never commit `.env` or `.env.test` with real credentials to git
- Change all default passwords in production environments
- Use environment-specific credential management (e.g., HashiCorp Vault, AWS Secrets Manager)

## 📝 Environment Variables

All credentials can be overridden using environment variables:

```bash
export COUCHDB_USER=your_user
export COUCHDB_PASSWORD=your_password
export REDIS_PASSWORD=your_redis_password
export GRAFANA_PASSWORD=your_grafana_password
```

## 📚 Additional Resources

- [CouchDB Documentation](https://docs.couchdb.org/)
- [Redis Documentation](https://redis.io/documentation)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
