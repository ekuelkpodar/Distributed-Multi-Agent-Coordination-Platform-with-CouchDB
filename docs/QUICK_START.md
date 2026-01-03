# Quick Start Guide

This guide will help you get the Distributed Multi-Agent Coordination Platform up and running in minutes.

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- 4GB+ RAM available
- Git

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Distributed
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys (optional for basic usage)
# Required only if using LLM integrations:
# - OPENAI_API_KEY
# - ANTHROPIC_API_KEY
```

### 4. Start the Platform

```bash
# Start CouchDB cluster and services
./scripts/start_platform.sh
```

This script will:
- Start a 3-node CouchDB cluster
- Initialize Redis for caching
- Set up Prometheus and Grafana for monitoring
- Create the database and indexes
- Verify the setup

### 5. Verify Installation

Access the web interfaces:

- **CouchDB Admin**: http://localhost:5984/_utils
  - Username: `admin`
  - Password: `password`

- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: `admin`

- **Prometheus**: http://localhost:9090

## Running Examples

### Distributed Research Example

This example demonstrates the map-reduce coordination pattern with multiple research agents:

```bash
python3 examples/distributed_research.py
```

Expected output:
```
======================================================================
Distributed Research Example - Map-Reduce Pattern
======================================================================

1. Starting research agents...
   ✓ Started agent: research-a1b2c3d4 in us-east-1
   ✓ Started agent: research-e5f6g7h8 in eu-west-1
   ✓ Started agent: research-i9j0k1l2 in ap-south-1

2. Discovered 3 active agents
   - research-a1b2c3d4: ['web_search', 'document_analysis', 'summarization']
   - research-e5f6g7h8: ['web_search', 'document_analysis', 'summarization']
   - research-i9j0k1l2: ['web_search', 'document_analysis', 'summarization']

3. Starting map-reduce research on 10 topics...
   Allocated tasks to 3 agents

4. Map-Reduce Results:
   Total items processed: 10
   Chunks processed: 3
   Final result: Reduced 10 items from 3 chunks

5. Task Queue Statistics:
   completed: 4
   pending: 0

6. Stopping agents...
   ✓ Stopped agent: research-a1b2c3d4
   ✓ Stopped agent: research-e5f6g7h8
   ✓ Stopped agent: research-i9j0k1l2

======================================================================
Example completed successfully!
======================================================================
```

## Creating Your First Agent

Create a custom agent by extending the `BaseAgent` class:

```python
from src.agents.base_agent import BaseAgent
from src.core.models import Task

class MyCustomAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_type="custom",
            capabilities=["custom_task"],
            **kwargs
        )
    
    async def _execute_task_logic(self, task: Task):
        """Implement your task logic here."""
        action = task.task_definition.get("action")
        
        if action == "custom_task":
            # Your custom logic
            return {"result": "success"}
        
        raise ValueError(f"Unknown action: {action}")
```

Use your agent:

```python
import asyncio
from src.database.client import CouchDBClient
from src.core.task_queue import TaskQueue

async def main():
    # Create agent
    agent = MyCustomAgent(region="us-east-1")
    await agent.start()
    
    # Create task
    async with CouchDBClient() as client:
        task_queue = TaskQueue(client)
        task = await task_queue.create_task(
            task_definition={"action": "custom_task"}
        )
    
    # Agent will automatically pick up and execute the task
    await asyncio.sleep(5)
    
    # Stop agent
    await agent.stop()

asyncio.run(main())
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_task_queue.py

# Run with coverage
pytest --cov=src tests/
```

## Common Operations

### View Active Agents

```bash
# Using CouchDB HTTP API
curl http://admin:password@localhost:5984/agent_coordination/_design/agents/_view/by_status?key="active"
```

### View Task Queue

```bash
# View pending tasks
curl http://admin:password@localhost:5984/agent_coordination/_design/tasks/_view/pending_by_priority?descending=true
```

### Monitor Replication

```bash
# Check replication status
curl http://admin:password@localhost:5984/_active_tasks
```

## Stopping the Platform

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (cleans all data)
docker-compose down -v
```

## Troubleshooting

### CouchDB not starting

```bash
# Check Docker logs
docker-compose logs couchdb-node1

# Restart services
docker-compose restart
```

### Port conflicts

If ports are already in use, edit `docker-compose.yml` and change the port mappings.

### Database initialization fails

```bash
# Manually run initialization
python3 scripts/init_database.py
```

### Agent not picking up tasks

1. Check agent is registered:
   ```bash
   curl http://admin:password@localhost:5984/agent_coordination/_design/agents/_view/by_status
   ```

2. Check task status:
   ```bash
   curl http://admin:password@localhost:5984/agent_coordination/task:TASK_ID
   ```

3. Check agent heartbeat is updating

## Next Steps

- Read the [Architecture Overview](architecture.md)
- Explore [API Reference](api_reference.md)
- Learn about [Coordination Patterns](coordination_patterns.md)
- Set up [Production Deployment](deployment.md)

## Getting Help

- Check the [FAQ](faq.md)
- Review [Examples](../examples/)
- Report issues on GitHub

## Key Concepts

### Agents
Autonomous workers that execute tasks. Each agent has:
- Unique ID
- Capabilities (what it can do)
- Region (geographic location)
- Status (active/inactive/failed)

### Tasks
Units of work with:
- Priority (1-10)
- Dependencies (other tasks that must complete first)
- Assignment (which agent is working on it)
- Status (pending/assigned/in_progress/completed/failed)

### Coordination Patterns
- **Map-Reduce**: Parallel processing with aggregation
- **Pipeline**: Sequential processing stages
- **Auction**: Dynamic task allocation through bidding

### Conflict Resolution
- **Vector Clocks**: Track causality
- **Last-Write-Wins**: Simple timestamp-based
- **Merge**: Combine non-conflicting changes
