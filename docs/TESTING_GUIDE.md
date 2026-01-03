# Testing Guide

Complete guide for testing the Distributed Multi-Agent Coordination Platform.

## Quick Start

```bash
# 1. Ensure services are running
make start

# 2. Generate mock test data
python3 scripts/generate_mock_data.py

# 3. Run all tests
./scripts/run_tests.sh

# 4. View test results
open test_reports/coverage_integration/index.html
```

## Test Structure

```
Distributed/
├── tests/
│   ├── test_integration.py      # Integration tests
│   ├── test_task_queue.py        # Unit tests
│   └── __init__.py
├── scripts/
│   ├── run_tests.sh              # Comprehensive test runner
│   └── generate_mock_data.py     # Mock data generator
├── .env.test                      # Test credentials
└── test_reports/                  # Generated test reports
```

## Test Categories

### 1. Unit Tests

Test individual components in isolation.

```bash
# Run all unit tests
pytest tests/ --ignore=tests/test_integration.py -v

# Run specific test file
pytest tests/test_task_queue.py -v

# Run with coverage
pytest tests/ --ignore=tests/test_integration.py --cov=src --cov-report=html
```

### 2. Integration Tests

Test components working together.

```bash
# Run all integration tests
pytest tests/test_integration.py -v

# Run specific test class
pytest tests/test_integration.py::TestDatabaseIntegration -v

# Run specific test method
pytest tests/test_integration.py::TestDatabaseIntegration::test_couchdb_connection -v
```

**Integration Test Classes**:
- `TestDatabaseIntegration` - Database connectivity and CRUD operations
- `TestAgentRegistry` - Agent registration and discovery
- `TestTaskQueue` - Task management and prioritization
- `TestCoordinationPatterns` - Task allocation and coordination
- `TestEndToEndWorkflow` - Complete workflows
- `TestReplicationAndConsistency` - Multi-node replication
- `TestSystemHealth` - Service health checks

### 3. System Tests

Test the entire system end-to-end.

```bash
# Run system tests
./scripts/run_tests.sh --system
```

### 4. Performance Tests

Test system performance and throughput.

```bash
# Run performance tests
./scripts/run_tests.sh --performance
```

## Mock Data Generation

### Using OpenRouter API

The mock data generator uses OpenRouter to create realistic test data.

```bash
# Generate default data (10 agents, 30 tasks, etc.)
python3 scripts/generate_mock_data.py

# Custom amounts
python3 scripts/generate_mock_data.py \
  --agents 20 \
  --tasks 50 \
  --knowledge 25 \
  --states 30 \
  --decisions 10

# With API key
OPENROUTER_API_KEY="your-key" python3 scripts/generate_mock_data.py
```

### Generated Data

The generator creates:

1. **Agents** - Different types (research, analysis, coordination, etc.)
   - Distributed across regions
   - Various capabilities and statuses
   - Realistic metadata (version, model, resource limits)

2. **Tasks** - Various states (pending, assigned, in_progress, completed, failed)
   - Priority levels (1-10)
   - Dependencies between tasks
   - Results and error messages
   - Task history

3. **Knowledge Documents** - Domain knowledge entries
   - Topics (distributed systems, ML, data engineering, etc.)
   - Multiple contributors
   - Version tracking

4. **Agent States** - State snapshots
   - Resource usage (memory, CPU)
   - Vector clocks for causality
   - Current workload

5. **Consensus Decisions** - Multi-agent decisions
   - Various decision types
   - Voting records
   - Approval/rejection outcomes

## Test Runner Usage

The `run_tests.sh` script provides comprehensive test execution.

### Basic Usage

```bash
# Run all tests
./scripts/run_tests.sh

# Run specific test suites
./scripts/run_tests.sh --unit
./scripts/run_tests.sh --integration
./scripts/run_tests.sh --system
./scripts/run_tests.sh --performance

# Generate mock data before testing
./scripts/run_tests.sh --generate-data

# Combine options
./scripts/run_tests.sh --generate-data --integration
```

### Test Runner Features

1. **Prerequisites Check**
   - Verifies Docker is installed and running
   - Checks Python and pytest installation
   - Validates Python dependencies

2. **Service Health Checks**
   - CouchDB nodes (all 3)
   - Redis
   - Prometheus
   - Grafana

3. **Test Execution**
   - Unit tests with coverage
   - Integration tests
   - System tests
   - Performance benchmarks

4. **Report Generation**
   - Coverage reports (HTML)
   - Test summary
   - Service status
   - Timestamped reports

## Viewing Test Results

### Coverage Reports

```bash
# Open unit test coverage
open test_reports/coverage_unit/index.html

# Open integration test coverage
open test_reports/coverage_integration/index.html
```

### Test Reports

```bash
# View latest test summary
cat test_reports/test_summary_*.txt

# List all reports
ls -lt test_reports/
```

## Testing Specific Features

### Test Agent Registration

```python
import asyncio
from src.database.client import CouchDBClient
from src.agents.registry import AgentRegistry
from src.core.models import Agent, AgentStatus

async def test():
    async with CouchDBClient() as client:
        registry = AgentRegistry(client)

        agent = Agent(
            agent_id="test_agent_001",
            agent_type="test",
            capabilities=["testing"],
            status=AgentStatus.ACTIVE,
            region="us-east-1"
        )

        await registry.register_agent(agent)
        print(f"✓ Registered agent: {agent.agent_id}")

        # Discover agents
        agents = await registry.discover_agents(agent_type="test")
        print(f"✓ Found {len(agents)} test agents")

asyncio.run(test())
```

### Test Task Queue

```python
import asyncio
from src.database.client import CouchDBClient
from src.core.task_queue import TaskQueue
from src.core.models import Task, TaskStatus

async def test():
    async with CouchDBClient() as client:
        queue = TaskQueue(client)

        # Create task
        task = Task(
            task_id="test_task_001",
            status=TaskStatus.PENDING,
            priority=8,
            task_definition={"type": "test", "action": "process"}
        )

        await queue.add_task(task)
        print(f"✓ Created task: {task.task_id}")

        # Get pending tasks
        pending = await queue.get_pending_tasks(limit=10)
        print(f"✓ Found {len(pending)} pending tasks")

asyncio.run(test())
```

### Test Replication

```python
import asyncio
from src.database.client import CouchDBClient

async def test():
    # Create document on node 1
    client1 = CouchDBClient(url="http://localhost:5984")
    async with client1:
        doc = {
            "_id": "test_repl_doc",
            "type": "test",
            "data": "test data"
        }
        await client1.save_document(doc)
        print("✓ Created document on node 1")

    # Wait for replication
    await asyncio.sleep(2)

    # Check on node 2
    client2 = CouchDBClient(url="http://localhost:5985")
    async with client2:
        replicated = await client2.get_document("test_repl_doc")
        print(f"✓ Document replicated to node 2: {replicated['_id']}")

asyncio.run(test())
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'

    - name: Start services
      run: |
        docker-compose up -d
        sleep 10

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Initialize database
      run: |
        echo "y" | python3 scripts/init_database.py

    - name: Run tests
      run: |
        ./scripts/run_tests.sh

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        files: ./test_reports/coverage_integration/coverage.xml
```

## Troubleshooting

### Tests Hanging

If tests appear to hang:

```bash
# Check if services are responsive
curl http://localhost:5984/_up
docker exec redis redis-cli ping

# Check Docker logs
docker logs couchdb-node1
docker logs redis

# Restart services
make restart
```

### Connection Errors

```bash
# Verify network connectivity
docker network ls
docker network inspect distributed_couchdb-network

# Check port availability
lsof -i :5984
lsof -i :6379
```

### Test Data Issues

```bash
# Clear test data
curl -X DELETE http://admin:password@localhost:5984/agent_coordination
python3 scripts/init_database.py

# Regenerate mock data
python3 scripts/generate_mock_data.py
```

### Coverage Not Generated

```bash
# Install coverage package
pip install pytest-cov

# Run with explicit coverage
pytest tests/test_integration.py --cov=src --cov-report=html --cov-report=term
```

## Best Practices

1. **Always run tests before commits**
   ```bash
   ./scripts/run_tests.sh
   ```

2. **Generate fresh test data for integration tests**
   ```bash
   ./scripts/run_tests.sh --generate-data --integration
   ```

3. **Clean up test artifacts**
   ```bash
   rm -rf test_reports/*
   rm -rf .pytest_cache
   ```

4. **Check coverage regularly**
   - Aim for >80% coverage on core modules
   - View reports to identify untested code

5. **Run performance tests before releases**
   ```bash
   ./scripts/run_tests.sh --performance
   ```

## Test Credentials Reference

All test credentials are documented in [TEST_CREDENTIALS.md](TEST_CREDENTIALS.md).

**Quick Reference**:
- CouchDB: `admin` / `password`
- Grafana: `admin` / `admin`
- Redis: No password

## Additional Resources

- [Integration Tests](../tests/test_integration.py) - Full test source
- [Test Credentials](TEST_CREDENTIALS.md) - All service credentials
- [Mock Data Generator](../scripts/generate_mock_data.py) - Data generation source
- [Test Runner](../scripts/run_tests.sh) - Test execution script
