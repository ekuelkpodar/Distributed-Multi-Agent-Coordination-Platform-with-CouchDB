# Distributed Multi-Agent Coordination Platform

A production-ready distributed multi-agent coordination platform leveraging CouchDB's conflict-free replication and eventual consistency model for autonomous AI agent coordination.

## Features

- **Distributed Agent Coordination**: Multi-agent task distribution and execution across geographic regions
- **Conflict-Free Replication**: CouchDB-based eventual consistency with intelligent conflict resolution
- **Multi-LLM Support**: Integration with OpenAI, Anthropic, and open-source models
- **Advanced Coordination Patterns**: Map-Reduce, Pipeline, Auction-based allocation
- **Production-Ready**: Monitoring, observability, and scalability built-in

## Architecture

```mermaid
graph TB
    subgraph "Global Distribution Layer"
        CDB1[CouchDB US<br/>Primary]
        CDB2[CouchDB EU<br/>Replica]
        CDB3[CouchDB APAC<br/>Replica]

        CDB1 <-->|Bi-directional<br/>Replication| CDB2
        CDB2 <-->|Bi-directional<br/>Replication| CDB3
        CDB3 <-->|Bi-directional<br/>Replication| CDB1
    end

    subgraph "Agent Coordination Layer"
        AR[Agent Registry<br/>Discovery & Health]
        TQ[Task Queue<br/>Priority & Dependencies]
        CP[Coordination Patterns<br/>MapReduce/Pipeline/Auction]
        SM[State Manager<br/>Vector Clocks]

        AR <--> TQ
        TQ <--> CP
        CP <--> SM
    end

    subgraph "Agent Pool"
        A1[Research Agent<br/>US-East]
        A2[Analysis Agent<br/>EU-West]
        A3[Synthesis Agent<br/>APAC]
        A4[Research Agent<br/>US-East]

        A1 --> AR
        A2 --> AR
        A3 --> AR
        A4 --> AR
    end

    subgraph "Data Layer"
        AGENT[Agent Docs<br/>Registration & Heartbeat]
        TASK[Task Docs<br/>Queue & Status]
        STATE[State Docs<br/>Vector Clocks]
        KNOWLEDGE[Knowledge Docs<br/>Shared Learning]
    end

    subgraph "Monitoring Stack"
        PROM[Prometheus<br/>Metrics Collection]
        GRAF[Grafana<br/>Dashboards]
        REDIS[Redis<br/>Cache & Session]

        PROM --> GRAF
    end

    %% Connections
    CDB1 --> AR
    CDB2 --> AR
    CDB3 --> AR

    AR --> AGENT
    TQ --> TASK
    SM --> STATE
    CP --> KNOWLEDGE

    A1 --> TQ
    A2 --> TQ
    A3 --> TQ
    A4 --> TQ

    AR -.->|Metrics| PROM
    TQ -.->|Metrics| PROM
    A1 -.->|Metrics| PROM
    A2 -.->|Metrics| PROM

    TQ --> REDIS

    classDef database fill:#4CAF50,stroke:#2E7D32,color:#fff
    classDef agent fill:#2196F3,stroke:#1565C0,color:#fff
    classDef coord fill:#FF9800,stroke:#E65100,color:#fff
    classDef monitor fill:#9C27B0,stroke:#6A1B9A,color:#fff

    class CDB1,CDB2,CDB3,AGENT,TASK,STATE,KNOWLEDGE database
    class A1,A2,A3,A4,AR agent
    class TQ,CP,SM coord
    class PROM,GRAF,REDIS monitor
```

### Task Execution Flow

```mermaid
sequenceDiagram
    participant Client
    participant TaskQueue
    participant AgentRegistry
    participant Agent
    participant CouchDB
    participant Coordinator

    Client->>TaskQueue: Create Task
    TaskQueue->>CouchDB: Store Task (status: pending)

    par Heartbeat Loop
        Agent->>AgentRegistry: Send Heartbeat
        AgentRegistry->>CouchDB: Update Agent Status
    end

    TaskQueue->>AgentRegistry: Find Available Agent
    AgentRegistry-->>TaskQueue: Return Agent by Load/Capability

    TaskQueue->>CouchDB: Assign Task to Agent
    TaskQueue->>Agent: Notify Task Assignment

    Agent->>CouchDB: Update Task (status: in_progress)
    Agent->>Agent: Execute Task Logic

    alt Task Succeeds
        Agent->>CouchDB: Update Task (status: completed, result)
        Agent->>TaskQueue: Task Complete
    else Task Fails
        Agent->>CouchDB: Update Task (status: failed, error)
        TaskQueue->>TaskQueue: Check Retry Count
        alt Retry Available
            TaskQueue->>CouchDB: Reset Task (status: pending)
        else Max Retries Exceeded
            TaskQueue->>Client: Task Failed Permanently
        end
    end

    Note over Coordinator: Coordination Patterns

    rect rgb(255, 200, 150)
        Note right of Coordinator: Map-Reduce Pattern
        Coordinator->>TaskQueue: Create Map Tasks (N)
        TaskQueue->>Agent: Distribute to Multiple Agents
        Agent-->>Coordinator: Return Map Results
        Coordinator->>TaskQueue: Create Reduce Task
        TaskQueue->>Agent: Assign Reduce Task
        Agent-->>Coordinator: Return Final Result
    end
```

### Coordination Patterns Visualization

```mermaid
graph LR
    subgraph "Map-Reduce Pattern"
        Input1[Input Data] --> Split[Split into Chunks]
        Split --> Map1[Map Task 1]
        Split --> Map2[Map Task 2]
        Split --> Map3[Map Task 3]
        Map1 --> Reduce[Reduce Task]
        Map2 --> Reduce
        Map3 --> Reduce
        Reduce --> Output1[Final Result]
    end

    subgraph "Pipeline Pattern"
        Input2[Input] --> Stage1[Parse]
        Stage1 --> Stage2[Transform]
        Stage2 --> Stage3[Validate]
        Stage3 --> Output2[Output]
    end

    subgraph "Auction Pattern"
        Task[New Task] --> Auction[Auction Coordinator]
        Auction --> Agent1[Agent 1: Bid $80]
        Auction --> Agent2[Agent 2: Bid $95]
        Auction --> Agent3[Agent 3: Bid $60]
        Agent2 -.->|Winner| Assign[Task Assignment]
    end

    style Map1 fill:#E3F2FD
    style Map2 fill:#E3F2FD
    style Map3 fill:#E3F2FD
    style Reduce fill:#FFF9C4
    style Stage1 fill:#F3E5F5
    style Stage2 fill:#F3E5F5
    style Stage3 fill:#F3E5F5
    style Agent2 fill:#C8E6C9
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- 4GB+ RAM available

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd Distributed

# Install dependencies
pip install -r requirements.txt

# Start CouchDB cluster
docker-compose up -d

# Initialize database
python scripts/init_database.py

# Run example
python examples/distributed_research.py
```

## Project Structure

```
Distributed/
├── src/
│   ├── core/              # Core coordination components
│   ├── agents/            # Agent implementations
│   ├── database/          # CouchDB clients and utilities
│   ├── coordination/      # Coordination patterns
│   └── monitoring/        # Observability and metrics
├── tests/                 # Test suites
├── examples/              # Example use cases
├── docs/                  # Documentation
├── docker-compose.yml     # Local development setup
└── requirements.txt       # Python dependencies
```

## Key Features Implemented

✅ **3-Node CouchDB Cluster** with multi-master replication
✅ **Agent Framework** with lifecycle management and automatic registration
✅ **Priority Task Queue** with dependency resolution (DAG support)
✅ **Conflict Resolution** using Vector Clocks, Last-Write-Wins, and Merge strategies
✅ **Coordination Patterns**: Map-Reduce, Pipeline, Auction-based allocation
✅ **Failure Recovery** with automatic detection and task reassignment
✅ **Connection Pooling** and retry logic for production use
✅ **Monitoring Setup** with Prometheus and Grafana
✅ **Comprehensive Tests** with async support
✅ **Complete Documentation** with examples

## Project Statistics

- **Total Files**: 32+ source files
- **Lines of Code**: ~3,000 lines of Python
- **Documentation**: 4 comprehensive guides
- **Docker Services**: 6 (3x CouchDB, Redis, Prometheus, Grafana)
- **Test Coverage**: Core components covered

## Documentation

- [Getting Started Guide](GETTING_STARTED.md) - Step-by-step setup checklist
- [Quick Start Guide](docs/QUICK_START.md) - Comprehensive usage guide
- [Architecture Overview](docs/ARCHITECTURE.md) - System architecture and design
- [Project Summary](PROJECT_SUMMARY.md) - Complete implementation details

## Common Commands

```bash
make help          # Show all available commands
make start         # Start the platform
make example       # Run distributed research example
make test          # Run tests
make status        # Check service status
make stop          # Stop all services
```

## Access Points

Once started, access the following interfaces:

- **CouchDB Admin**: http://localhost:5984/_utils (admin/password)
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Prometheus Metrics**: http://localhost:9090

## Next Steps

1. Read [GETTING_STARTED.md](GETTING_STARTED.md) for a guided walkthrough
2. Run the example: `python3 examples/distributed_research.py`
3. Create your first custom agent
4. Explore the coordination patterns
5. Set up production deployment

## License

MIT License - see [LICENSE](LICENSE) file for details
