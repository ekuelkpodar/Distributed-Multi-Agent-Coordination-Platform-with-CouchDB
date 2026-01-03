# System Diagrams

This document contains visual diagrams of the Distributed Multi-Agent Coordination Platform architecture and workflows.

## Table of Contents
- [System Architecture](#system-architecture)
- [Agent Lifecycle](#agent-lifecycle)
- [Task Flow](#task-flow)
- [Map-Reduce Coordination](#map-reduce-coordination)
- [Conflict Resolution](#conflict-resolution)
- [Data Model](#data-model)

---

## System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        API[REST API]
        CLI[CLI Tools]
    end

    subgraph "Agent Coordination Layer"
        A1[Agent 1<br/>Research]
        A2[Agent 2<br/>Analysis]
        A3[Agent 3<br/>Synthesis]
        AR[Agent Registry]
        TQ[Task Queue]
        SM[State Manager]
    end

    subgraph "Global Distribution Layer"
        subgraph "Region: US-East"
            C1[(CouchDB<br/>Node 1)]
            R1[Redis Cache]
        end
        
        subgraph "Region: EU-West"
            C2[(CouchDB<br/>Node 2)]
            R2[Redis Cache]
        end
        
        subgraph "Region: AP-South"
            C3[(CouchDB<br/>Node 3)]
            R3[Redis Cache]
        end
    end

    subgraph "Monitoring Stack"
        P[Prometheus]
        G[Grafana]
        OT[OpenTelemetry]
    end

    subgraph "LLM Providers"
        OAI[OpenAI]
        ANT[Anthropic]
        GEM[Gemini]
    end

    API --> AR
    CLI --> TQ
    
    A1 --> AR
    A2 --> AR
    A3 --> AR
    
    A1 --> TQ
    A2 --> TQ
    A3 --> TQ
    
    AR --> C1
    TQ --> C1
    SM --> C1
    
    A1 --> R1
    A2 --> R2
    A3 --> R3
    
    C1 <-.Replication.-> C2
    C2 <-.Replication.-> C3
    C3 <-.Replication.-> C1
    
    A1 -.Metrics.-> P
    A2 -.Metrics.-> P
    A3 -.Metrics.-> P
    C1 -.Metrics.-> P
    
    P --> G
    OT --> P
    
    A1 -.LLM Calls.-> OAI
    A2 -.LLM Calls.-> ANT
    A3 -.LLM Calls.-> GEM

    style A1 fill:#e1f5ff
    style A2 fill:#e1f5ff
    style A3 fill:#e1f5ff
    style C1 fill:#fff4e6
    style C2 fill:#fff4e6
    style C3 fill:#fff4e6
    style P fill:#f3e5f5
    style G fill:#f3e5f5
```

---

## Agent Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Initializing: create()
    
    Initializing --> Registering: start()
    Registering --> Active: registration complete
    
    Active --> Processing: task assigned
    Processing --> Active: task complete
    
    Active --> HeartbeatCheck: every 30s
    HeartbeatCheck --> Active: heartbeat sent
    HeartbeatCheck --> Failed: timeout (90s)
    
    Active --> Maintenance: maintenance mode
    Maintenance --> Active: resume
    
    Active --> Stopping: stop()
    Processing --> Stopping: stop()
    Stopping --> Inactive: cleanup complete
    
    Failed --> Inactive: unrecoverable
    Failed --> Active: recovery successful
    
    Inactive --> [*]
    
    note right of Active
        Agent is healthy and
        available for tasks
    end note
    
    note right of Failed
        Tasks reassigned to
        healthy agents
    end note
```

---

## Task Flow

```mermaid
sequenceDiagram
    participant U as User/System
    participant TQ as Task Queue
    participant AR as Agent Registry
    participant A1 as Agent 1
    participant A2 as Agent 2
    participant DB as CouchDB

    U->>TQ: create_task(definition, priority)
    TQ->>DB: save task (status: pending)
    DB-->>TQ: task created
    TQ-->>U: Task ID
    
    loop Task Allocation
        AR->>DB: query active agents
        DB-->>AR: agent list
        AR->>TQ: get pending tasks
        TQ->>DB: query pending by priority
        DB-->>TQ: task list
        
        AR->>AR: calculate agent scores
        AR->>TQ: assign_task(task_id, agent_id)
        TQ->>DB: update task (optimistic lock)
        
        alt Assignment Success
            DB-->>TQ: task updated
            TQ-->>A1: notify task assignment
        else Conflict (already assigned)
            DB-->>TQ: conflict error
            TQ->>AR: retry with next agent
        end
    end
    
    A1->>TQ: get_task()
    TQ-->>A1: task details
    
    A1->>DB: update status (in_progress)
    A1->>A1: execute task logic
    
    alt Task Success
        A1->>TQ: complete_task(result)
        TQ->>DB: update status (completed)
        DB-->>TQ: confirmed
    else Task Failure
        A1->>TQ: handle_failure(error)
        TQ->>DB: increment retry_count
        
        alt Retry Available
            TQ->>DB: reset to pending
            DB-->>AR: task available
        else Max Retries Reached
            TQ->>DB: mark as failed
        end
    end
    
    Note over A1,DB: Tasks with dependencies<br/>wait for prerequisites
```

---

## Map-Reduce Coordination

```mermaid
graph TD
    Start([Input Data: 10 items]) --> Split[Split into Chunks]
    
    Split --> C1[Chunk 1<br/>3 items]
    Split --> C2[Chunk 2<br/>3 items]
    Split --> C3[Chunk 3<br/>2 items]
    Split --> C4[Chunk 4<br/>2 items]
    
    C1 --> T1[Create Map Task 1]
    C2 --> T2[Create Map Task 2]
    C3 --> T3[Create Map Task 3]
    C4 --> T4[Create Map Task 4]
    
    T1 --> TQ[Task Queue<br/>Priority: 7]
    T2 --> TQ
    T3 --> TQ
    T4 --> TQ
    
    TQ --> A1[Agent 1<br/>US-East]
    TQ --> A2[Agent 2<br/>EU-West]
    TQ --> A3[Agent 3<br/>AP-South]
    TQ --> A4[Agent 4<br/>US-East]
    
    A1 --> M1[Map Result 1]
    A2 --> M2[Map Result 2]
    A3 --> M3[Map Result 3]
    A4 --> M4[Map Result 4]
    
    M1 --> Wait{Wait for All<br/>Map Tasks}
    M2 --> Wait
    M3 --> Wait
    M4 --> Wait
    
    Wait --> RT[Create Reduce Task]
    RT --> TQ2[Task Queue<br/>Priority: 8]
    TQ2 --> A5[Agent 5]
    
    A5 --> Reduce[Reduce Operation<br/>Aggregate Results]
    Reduce --> Final([Final Result])
    
    style Start fill:#e8f5e9
    style Final fill:#e8f5e9
    style TQ fill:#fff3e0
    style TQ2 fill:#fff3e0
    style A1 fill:#e1f5ff
    style A2 fill:#e1f5ff
    style A3 fill:#e1f5ff
    style A4 fill:#e1f5ff
    style A5 fill:#e1f5ff
```

---

## Conflict Resolution

```mermaid
flowchart TD
    Start([Document Update]) --> Rep{Replication<br/>Conflict?}
    
    Rep -->|No| Success([Save Successful])
    Rep -->|Yes| Detect[Detect Conflict]
    
    Detect --> Fetch[Fetch All Versions]
    Fetch --> DocType{Document<br/>Type?}
    
    DocType -->|Agent State| VC[Vector Clock<br/>Resolution]
    DocType -->|Task| LWW[Last-Write-Wins<br/>Resolution]
    DocType -->|Knowledge| Merge[Merge<br/>Resolution]
    
    subgraph "Vector Clock Resolution"
        VC --> Compare[Compare Vector Clocks]
        Compare --> Happens{Happens<br/>Before?}
        Happens -->|Yes| SelectRecent[Select Recent]
        Happens -->|No, Concurrent| UseClock[Use Timestamp<br/>as Tiebreaker]
        UseClock --> SelectRecent
    end
    
    subgraph "Last-Write-Wins"
        LWW --> CompareTime[Compare Timestamps]
        CompareTime --> SelectLatest[Select Latest]
    end
    
    subgraph "Merge Strategy"
        Merge --> MergeContent[Merge Non-Conflicting<br/>Fields]
        MergeContent --> Union[Union of Lists]
        Union --> Dedupe[Deduplicate Contributors]
        Dedupe --> Increment[Increment Version]
    end
    
    SelectRecent --> Save[Save Winner]
    SelectLatest --> Save
    Increment --> Save
    
    Save --> Delete[Delete Losing<br/>Revisions]
    Delete --> Success
    
    style Start fill:#e8f5e9
    style Success fill:#e8f5e9
    style VC fill:#fff3e0
    style LWW fill:#e1f5ff
    style Merge fill:#f3e5f5
```

---

## Data Model

```mermaid
erDiagram
    AGENT ||--o{ TASK : "assigned_to"
    AGENT ||--o{ AGENT_STATE : "has"
    AGENT ||--o{ KNOWLEDGE : "contributes_to"
    TASK ||--o{ TASK : "depends_on"
    TASK ||--o{ TASK_HISTORY : "has"
    KNOWLEDGE ||--o{ CONTRIBUTOR : "has"

    AGENT {
        string _id PK "agent:uuid"
        string _rev "CouchDB revision"
        enum type "agent"
        string agent_id UK
        string agent_type
        array capabilities
        enum status "active|inactive|failed"
        string region
        datetime heartbeat_timestamp
        object metadata
        array current_tasks
        datetime created_at
        datetime updated_at
    }

    TASK {
        string _id PK "task:uuid"
        string _rev
        enum type "task"
        string task_id UK
        enum status "pending|assigned|in_progress|completed|failed"
        int priority "1-10"
        string assigned_to FK
        datetime assigned_at
        object task_definition
        array dependencies FK
        any result
        string error
        int retry_count
        int max_retries
        datetime created_at
        datetime updated_at
    }

    TASK_HISTORY {
        datetime timestamp
        enum status
        string agent
        string message
    }

    AGENT_STATE {
        string _id PK "state:agent_id:session_id"
        string _rev
        enum type "agent_state"
        string agent_id FK
        string session_id
        object state_snapshot
        object vector_clock
        datetime timestamp
        datetime created_at
        datetime updated_at
    }

    KNOWLEDGE {
        string _id PK "knowledge:topic"
        string _rev
        enum type "knowledge"
        string topic UK
        object content
        array contributors
        int version
        datetime created_at
        datetime updated_at
    }

    CONTRIBUTOR {
        string agent_id
        datetime contribution_timestamp
        string contribution_type "create|enhance|review"
    }
```

---

## Component Interaction

```mermaid
graph LR
    subgraph "Agent Operations"
        A[Agent] -->|register| AR[Agent Registry]
        A -->|heartbeat| AR
        A -->|get_task| TQ[Task Queue]
        A -->|update_status| TQ
        A -->|save_state| SM[State Manager]
    end

    subgraph "Coordination Patterns"
        MR[Map-Reduce] -->|create_tasks| TQ
        PL[Pipeline] -->|create_tasks| TQ
        AU[Auction] -->|request_bids| AR
        AU -->|assign_task| TQ
    end

    subgraph "Conflict Management"
        CR[Conflict Resolver] -->|detect| DB[(CouchDB)]
        CR -->|resolve| VC[Vector Clock]
        CR -->|resolve| LWW[Last-Write-Wins]
        CR -->|resolve| MG[Merge]
    end

    subgraph "Data Layer"
        AR -->|read/write| DB
        TQ -->|read/write| DB
        SM -->|read/write| DB
        
        DB -->|replicate| DB2[(CouchDB<br/>Replica)]
        DB2 -->|replicate| DB3[(CouchDB<br/>Replica)]
        DB3 -->|replicate| DB
    end

    subgraph "Monitoring"
        A -.metrics.-> P[Prometheus]
        TQ -.metrics.-> P
        DB -.metrics.-> P
        P -->|visualize| G[Grafana]
    end

    style A fill:#e1f5ff
    style DB fill:#fff4e6
    style DB2 fill:#fff4e6
    style DB3 fill:#fff4e6
    style P fill:#f3e5f5
    style G fill:#f3e5f5
```

---

## Replication Flow

```mermaid
sequenceDiagram
    participant C1 as CouchDB US
    participant C2 as CouchDB EU
    participant C3 as CouchDB AP
    participant A as Agent

    Note over C1,C3: Continuous Bidirectional Replication

    A->>C1: Write Document (rev: 1-abc)
    C1->>C1: Save locally
    
    par Replicate to EU
        C1->>C2: Replicate document
        C2->>C2: Save (rev: 1-abc)
    and Replicate to AP
        C1->>C3: Replicate document
        C3->>C3: Save (rev: 1-abc)
    end

    Note over C1,C3: Concurrent Updates Create Conflict

    A->>C2: Update Document (rev: 2-def)
    A->>C3: Update Document (rev: 2-xyz)
    
    C2->>C1: Replicate (rev: 2-def)
    C3->>C1: Replicate (rev: 2-xyz)
    
    C1->>C1: Detect Conflict!
    C1->>C1: Store both versions
    
    Note over C1: Conflict Resolution
    
    C1->>C1: Apply resolution strategy
    C1->>C1: Select winner (rev: 3-final)
    C1->>C1: Delete losers
    
    par Propagate Resolution
        C1->>C2: Replicate winner
        C2->>C2: Accept resolution
    and 
        C1->>C3: Replicate winner
        C3->>C3: Accept resolution
    end
    
    Note over C1,C3: Consistency Restored
```

---

## Task Dependency Resolution

```mermaid
graph TD
    Start([Task Created]) --> HasDep{Has<br/>Dependencies?}
    
    HasDep -->|No| Ready[Mark as Ready]
    HasDep -->|Yes| CheckDeps[Check Dependencies]
    
    CheckDeps --> DepLoop{All Deps<br/>Complete?}
    
    DepLoop -->|Yes| Ready
    DepLoop -->|No| Wait[Status: Waiting]
    
    Wait --> Monitor[Monitor Dep Changes]
    Monitor --> DepComplete{Dependency<br/>Completed?}
    
    DepComplete -->|Yes| CheckDeps
    DepComplete -->|No| Monitor
    
    Ready --> Queue[Add to Priority Queue]
    Queue --> Allocate{Agent<br/>Available?}
    
    Allocate -->|Yes| Assign[Assign to Agent]
    Allocate -->|No| WaitAgent[Wait for Agent]
    
    WaitAgent --> Allocate
    
    Assign --> Execute[Agent Executes]
    Execute --> Result{Success?}
    
    Result -->|Yes| Complete[Mark Complete]
    Result -->|No| Retry{Retry<br/>Available?}
    
    Retry -->|Yes| Queue
    Retry -->|No| Failed[Mark Failed]
    
    Complete --> Notify[Notify Dependent Tasks]
    Notify --> End([Done])
    Failed --> End
    
    style Start fill:#e8f5e9
    style Complete fill:#e8f5e9
    style Failed fill:#ffebee
    style End fill:#e8f5e9
```

---

## Monitoring Architecture

```mermaid
graph TB
    subgraph "Application Layer"
        A1[Agent 1]
        A2[Agent 2]
        A3[Agent 3]
        TQ[Task Queue]
        AR[Agent Registry]
    end

    subgraph "Metrics Collection"
        PC[Prometheus Client]
        A1 --> PC
        A2 --> PC
        A3 --> PC
        TQ --> PC
        AR --> PC
    end

    subgraph "Database Metrics"
        C1[CouchDB Node 1]
        C2[CouchDB Node 2]
        C3[CouchDB Node 3]
        C1 --> PM[Prometheus Exporter]
        C2 --> PM
        C3 --> PM
    end

    subgraph "Metrics Storage"
        PC --> PROM[Prometheus Server]
        PM --> PROM
        PROM --> TSDB[(Time Series DB)]
    end

    subgraph "Visualization"
        TSDB --> GRAF[Grafana]
        GRAF --> D1[Agent Dashboard]
        GRAF --> D2[Task Dashboard]
        GRAF --> D3[Database Dashboard]
        GRAF --> D4[System Dashboard]
    end

    subgraph "Alerting"
        PROM --> AM[Alert Manager]
        AM --> Email[Email Notifications]
        AM --> Slack[Slack Notifications]
        AM --> PD[PagerDuty]
    end

    subgraph "Tracing"
        A1 -.traces.-> OT[OpenTelemetry]
        A2 -.traces.-> OT
        A3 -.traces.-> OT
        OT --> Jaeger[Jaeger UI]
    end

    style PROM fill:#f3e5f5
    style GRAF fill:#f3e5f5
    style TSDB fill:#fff4e6
    style OT fill:#e1f5ff
```

---

## Network Partition Handling

```mermaid
sequenceDiagram
    participant A1 as Agent (US)
    participant C1 as CouchDB US
    participant C2 as CouchDB EU
    participant A2 as Agent (EU)

    Note over C1,C2: Normal Operation

    A1->>C1: Write Task 1
    A2->>C2: Write Task 2
    
    C1->>C2: Replicate Task 1
    C2->>C1: Replicate Task 2
    
    Note over C1,C2: Network Partition!
    
    rect rgb(255, 200, 200)
        Note over C1,C2: Partition Detected
        
        A1->>C1: Write Task 3
        C1->>C1: Save locally
        
        A2->>C2: Write Task 4
        C2->>C2: Save locally
        
        A1->>C1: Assign & Execute
        C1-->>A1: Task 3 Result
        
        A2->>C2: Assign & Execute
        C2-->>A2: Task 4 Result
    end
    
    Note over C1,C2: Partition Healed!
    
    C1->>C2: Replicate changes
    C2->>C1: Replicate changes
    
    rect rgb(200, 255, 200)
        Note over C1,C2: Conflict Detection
        
        C1->>C1: Detect conflicts
        C2->>C2: Detect conflicts
        
        C1->>C1: Apply resolution
        C2->>C2: Apply resolution
        
        C1->>C2: Sync resolution
        C2->>C1: Sync resolution
    end
    
    Note over C1,C2: Eventual Consistency Achieved
```

---

## Performance Optimization

```mermaid
graph TD
    Request[Incoming Request] --> Cache{Check<br/>Redis Cache}
    
    Cache -->|Hit| Return[Return Cached]
    Cache -->|Miss| Pool{Connection<br/>Pool Available?}
    
    Pool -->|Yes| GetConn[Get Connection]
    Pool -->|No| Wait[Wait for Connection]
    Wait --> GetConn
    
    GetConn --> Batch{Batchable<br/>Operation?}
    
    Batch -->|Yes| Collect[Collect Requests]
    Collect --> Full{Batch Full or<br/>Timeout?}
    Full -->|Yes| BulkOp[Bulk Operation]
    Full -->|No| Collect
    
    Batch -->|No| SingleOp[Single Operation]
    BulkOp --> Execute
    SingleOp --> Execute[Execute on CouchDB]
    
    Execute --> Success{Success?}
    
    Success -->|Yes| UpdateCache[Update Cache]
    Success -->|No| Retry{Retry<br/>Available?}
    
    Retry -->|Yes| Backoff[Exponential Backoff]
    Backoff --> Execute
    Retry -->|No| Error[Return Error]
    
    UpdateCache --> ReturnConn[Return Connection to Pool]
    ReturnConn --> Return
    
    Error --> ReturnConn
    
    style Return fill:#e8f5e9
    style Error fill:#ffebee
    style Pool fill:#fff3e0
    style Cache fill:#e1f5ff
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx/HAProxy]
    end

    subgraph "US-East Region"
        subgraph "Agent Cluster 1"
            A1[Agent Pod 1]
            A2[Agent Pod 2]
            A3[Agent Pod 3]
        end
        
        C1[(CouchDB<br/>StatefulSet)]
        R1[(Redis<br/>Cluster)]
        
        A1 --> C1
        A2 --> C1
        A3 --> C1
        A1 --> R1
        A2 --> R1
        A3 --> R1
    end

    subgraph "EU-West Region"
        subgraph "Agent Cluster 2"
            A4[Agent Pod 4]
            A5[Agent Pod 5]
        end
        
        C2[(CouchDB<br/>StatefulSet)]
        R2[(Redis<br/>Cluster)]
        
        A4 --> C2
        A5 --> C2
        A4 --> R2
        A5 --> R2
    end

    subgraph "AP-South Region"
        subgraph "Agent Cluster 3"
            A6[Agent Pod 6]
            A7[Agent Pod 7]
        end
        
        C3[(CouchDB<br/>StatefulSet)]
        R3[(Redis<br/>Cluster)]
        
        A6 --> C3
        A7 --> C3
        A6 --> R3
        A7 --> R3
    end

    subgraph "Monitoring (Central)"
        P[Prometheus<br/>Federation]
        G[Grafana]
        AM[Alert Manager]
    end

    LB --> A1
    LB --> A2
    LB --> A4
    LB --> A6

    C1 <-.Replication.-> C2
    C2 <-.Replication.-> C3
    C3 <-.Replication.-> C1

    A1 -.metrics.-> P
    A4 -.metrics.-> P
    A6 -.metrics.-> P
    C1 -.metrics.-> P
    C2 -.metrics.-> P
    C3 -.metrics.-> P

    P --> G
    P --> AM

    style LB fill:#e8eaf6
    style P fill:#f3e5f5
    style G fill:#f3e5f5
    style AM fill:#f3e5f5
```

