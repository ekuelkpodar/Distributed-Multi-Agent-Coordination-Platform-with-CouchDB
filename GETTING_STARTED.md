# Getting Started - Checklist

Follow these steps to get your Distributed Multi-Agent Coordination Platform up and running.

## ✅ Pre-Flight Checklist

### System Requirements
- [ ] Python 3.11 or higher installed
- [ ] Docker Desktop installed and running
- [ ] At least 4GB RAM available
- [ ] Git installed
- [ ] Terminal/Command line access

### Verify Installations

```bash
# Check Python version
python3 --version  # Should be 3.11+

# Check Docker
docker --version
docker-compose --version

# Check Docker is running
docker info
```

## 🚀 Quick Start (5 minutes)

### Step 1: Setup Project

```bash
# Clone repository (or you're already in it)
cd Distributed

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
# OR
make install
```

- [ ] Virtual environment created
- [ ] Dependencies installed (should see ~40 packages)

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env if needed (optional for basic usage)
# nano .env
```

- [ ] .env file created

### Step 3: Start Platform

```bash
# Option 1: Using helper script
./scripts/start_platform.sh

# Option 2: Using Makefile
make start

# Option 3: Manual
docker-compose up -d
sleep 10
python3 scripts/init_database.py
```

**Expected output:**
```
==========================================
Starting Distributed Agent Platform
==========================================

1. Starting CouchDB cluster...
   ✓ Node on port 5984 is ready
   ✓ Node on port 5985 is ready
   ✓ Node on port 5986 is ready

2. Initializing database...
   ✓ Database exists: agent_coordination
   
==========================================
Platform started successfully!
==========================================
```

- [ ] All 3 CouchDB nodes started
- [ ] Database initialized
- [ ] Redis started
- [ ] Prometheus started
- [ ] Grafana started

### Step 4: Verify Installation

```bash
# Check service status
make status

# OR manually check endpoints
curl http://localhost:5984/_up  # CouchDB node 1
curl http://localhost:5985/_up  # CouchDB node 2
curl http://localhost:5986/_up  # CouchDB node 3
```

**Access web interfaces:**
- [ ] CouchDB Admin: http://localhost:5984/_utils (admin/password)
- [ ] Grafana: http://localhost:3000 (admin/admin)
- [ ] Prometheus: http://localhost:9090

### Step 5: Run Example

```bash
# Run distributed research example
python3 examples/distributed_research.py

# OR
make example
```

**Expected output:**
```
======================================================================
Distributed Research Example - Map-Reduce Pattern
======================================================================

1. Starting research agents...
   ✓ Started agent: research-a1b2c3d4 in us-east-1
   ✓ Started agent: research-e5f6g7h8 in eu-west-1
   ✓ Started agent: research-i9j0k1l2 in ap-south-1

2. Discovered 3 active agents

3. Starting map-reduce research on 10 topics...

4. Map-Reduce Results:
   Total items processed: 10
   Chunks processed: 3

5. Task Queue Statistics:
   completed: 4

6. Stopping agents...

======================================================================
Example completed successfully!
======================================================================
```

- [ ] Example ran successfully
- [ ] 3 agents started
- [ ] Tasks completed
- [ ] Agents stopped cleanly

## 🎯 Next Steps

### Learn the Basics

1. **Read Documentation**
   - [ ] [Quick Start Guide](docs/QUICK_START.md)
   - [ ] [Architecture Overview](docs/ARCHITECTURE.md)
   - [ ] [Project Summary](PROJECT_SUMMARY.md)

2. **Explore CouchDB**
   - [ ] Open CouchDB Admin UI
   - [ ] Browse `agent_coordination` database
   - [ ] Explore design documents and views
   - [ ] Check replication status

3. **Understand the Code**
   - [ ] Review [src/agents/base_agent.py](src/agents/base_agent.py)
   - [ ] Study [src/core/task_queue.py](src/core/task_queue.py)
   - [ ] Examine [src/coordination/patterns.py](src/coordination/patterns.py)

### Build Your First Agent

Create `my_agent.py`:

```python
import asyncio
from src.agents.base_agent import BaseAgent
from src.core.models import Task

class MyAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_type="my_agent",
            capabilities=["custom_task"],
            **kwargs
        )
    
    async def _execute_task_logic(self, task: Task):
        print(f"Executing task: {task.task_id}")
        # Your logic here
        return {"status": "completed"}

async def main():
    agent = MyAgent(region="us-east-1")
    await agent.start()
    
    # Keep agent running
    try:
        await asyncio.sleep(60)
    except KeyboardInterrupt:
        pass
    
    await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python3 my_agent.py
```

- [ ] Custom agent created
- [ ] Agent runs successfully
- [ ] Agent appears in CouchDB

### Run Tests

```bash
# Run all tests
pytest -v

# Run with coverage
make test-coverage

# View coverage report
open htmlcov/index.html
```

- [ ] Tests pass
- [ ] Coverage report generated

### Explore Coordination Patterns

1. **Map-Reduce Pattern**
   - [ ] Review example in [examples/distributed_research.py](examples/distributed_research.py)
   - [ ] Modify to process your own data
   - [ ] Test with different numbers of mappers

2. **Pipeline Pattern**
   ```python
   from src.coordination.patterns import PipelineCoordinator
   
   result = await pipeline.execute(
       initial_input=data,
       stages=[
           {"action": "step1", "parameters": {}},
           {"action": "step2", "parameters": {}},
       ]
   )
   ```

3. **Auction Pattern**
   ```python
   from src.coordination.patterns import AuctionCoordinator
   
   winner = await auction.execute(
       task=task,
       auction_timeout=10
   )
   ```

## 🔧 Common Operations

### View Active Agents
```bash
# Via CouchDB API
curl http://admin:password@localhost:5984/agent_coordination/_design/agents/_view/by_status?key="active"

# Via Python
python3 -c "
import asyncio
from src.database.client import CouchDBClient
from src.agents.registry import AgentRegistry

async def main():
    async with CouchDBClient() as client:
        registry = AgentRegistry(client)
        agents = await registry.discover_agents()
        for agent in agents:
            print(f'{agent.agent_id}: {agent.status}')

asyncio.run(main())
"
```

### View Task Queue
```bash
curl http://admin:password@localhost:5984/agent_coordination/_design/tasks/_view/pending_by_priority
```

### Monitor Replication
```bash
curl http://admin:password@localhost:5984/_active_tasks
```

### Check Logs
```bash
# All services
make logs

# CouchDB only
make logs-couchdb

# Specific service
docker-compose logs -f redis
```

## 🛑 Stopping & Cleanup

### Stop Services
```bash
# Stop services (keeps data)
make stop
# OR
docker-compose down

# Stop and remove all data
make clean
# OR
docker-compose down -v
```

### Deactivate Virtual Environment
```bash
deactivate
```

## 🐛 Troubleshooting

### Issue: Port already in use

**Solution:**
```bash
# Check what's using port 5984
lsof -i :5984

# Kill the process or change port in docker-compose.yml
```

### Issue: CouchDB not starting

**Solution:**
```bash
# Check Docker logs
docker-compose logs couchdb-node1

# Restart services
make restart
```

### Issue: Database initialization fails

**Solution:**
```bash
# Manually initialize
python3 scripts/init_database.py

# Check CouchDB is accessible
curl http://localhost:5984/_up
```

### Issue: Agent not picking up tasks

**Solution:**
1. Verify agent is registered and active in CouchDB
2. Check agent heartbeat is updating
3. Verify task status is "pending"
4. Check agent capabilities match task requirements

### Issue: Tests failing

**Solution:**
```bash
# Clean test database
# (Tests create/destroy test_db automatically)

# Run single test for debugging
pytest tests/test_task_queue.py::TestTaskQueue::test_create_task -v
```

## 📚 Additional Resources

### Documentation
- [ ] [README.md](README.md) - Project overview
- [ ] [QUICK_START.md](docs/QUICK_START.md) - Detailed guide
- [ ] [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- [ ] [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - What's implemented

### Code Examples
- [ ] [examples/distributed_research.py](examples/distributed_research.py)
- [ ] [src/agents/research_agent.py](src/agents/research_agent.py)
- [ ] [tests/test_task_queue.py](tests/test_task_queue.py)

### Useful Commands
```bash
make help          # Show all available commands
make status        # Check service status
make example       # Run example
make test          # Run tests
make logs          # View logs
make shell         # Open CouchDB admin
```

## ✨ You're Ready!

Congratulations! You now have a fully functional distributed multi-agent coordination platform running.

### What You Can Do Now:
- ✅ Create custom agents
- ✅ Define tasks with priorities and dependencies
- ✅ Use coordination patterns (Map-Reduce, Pipeline, Auction)
- ✅ Monitor with Prometheus and Grafana
- ✅ Scale across multiple regions
- ✅ Handle failures gracefully

### Next Challenges:
1. Create an agent that uses an actual LLM (OpenAI/Anthropic)
2. Build a pipeline with 5+ stages
3. Set up cross-region replication
4. Create custom CouchDB views
5. Implement a new coordination pattern

**Happy coding!** 🚀
