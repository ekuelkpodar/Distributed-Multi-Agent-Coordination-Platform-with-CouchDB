"""
Core data models for the distributed agent platform.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Document types in CouchDB."""
    AGENT = "agent"
    TASK = "task"
    AGENT_STATE = "agent_state"
    KNOWLEDGE = "knowledge"
    DECISION = "consensus_decision"


class AgentStatus(str, Enum):
    """Agent status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


class TaskStatus(str, Enum):
    """Task status enum."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BaseDocument(BaseModel):
    """Base model for all CouchDB documents."""
    model_config = {"populate_by_name": True}

    id: Optional[str] = Field(None, alias="_id")
    rev: Optional[str] = Field(None, alias="_rev")
    type: DocumentType
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def model_dump(self, **kwargs):
        """Override to serialize datetime objects and exclude None values."""
        # Exclude None by default
        if 'exclude_none' not in kwargs:
            kwargs['exclude_none'] = True

        data = super().model_dump(**kwargs)

        # Convert datetime objects to ISO strings recursively
        def convert_datetimes(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_datetimes(v) for k, v in obj.items() if v is not None}
            elif isinstance(obj, list):
                return [convert_datetimes(item) for item in obj]
            return obj

        return convert_datetimes(data)


class AgentMetadata(BaseModel):
    """Agent metadata."""
    version: str = "1.0.0"
    model: str = "claude-sonnet-4"
    max_concurrent_tasks: int = 5
    custom: Dict[str, Any] = Field(default_factory=dict)


class Agent(BaseDocument):
    """Agent registration document."""
    type: DocumentType = DocumentType.AGENT
    agent_id: str
    agent_type: str
    capabilities: List[str] = Field(default_factory=list)
    status: AgentStatus = AgentStatus.ACTIVE
    region: str = "us-east-1"
    heartbeat_timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: AgentMetadata = Field(default_factory=AgentMetadata)
    current_tasks: List[str] = Field(default_factory=list)


class TaskHistory(BaseModel):
    """Task history entry."""
    timestamp: datetime
    status: TaskStatus
    agent: str
    message: Optional[str] = None


class Task(BaseDocument):
    """Task queue document."""
    type: DocumentType = DocumentType.TASK
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    priority: int = Field(default=5, ge=1, le=10)
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    task_definition: Dict[str, Any]
    dependencies: List[str] = Field(default_factory=list)
    result: Optional[Any] = None
    error: Optional[str] = None
    history: List[TaskHistory] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3


class VectorClock(BaseModel):
    """Vector clock for causality tracking."""
    clock: Dict[str, int] = Field(default_factory=dict)
    
    def increment(self, agent_id: str) -> 'VectorClock':
        """Increment clock for agent."""
        self.clock[agent_id] = self.clock.get(agent_id, 0) + 1
        return self
    
    def merge(self, other: 'VectorClock') -> 'VectorClock':
        """Merge with another vector clock."""
        for agent_id, timestamp in other.clock.items():
            self.clock[agent_id] = max(
                self.clock.get(agent_id, 0),
                timestamp
            )
        return self
    
    def happens_before(self, other: 'VectorClock') -> bool:
        """Check if this event happens before other."""
        all_keys = set(self.clock.keys()) | set(other.clock.keys())
        return (
            all(self.clock.get(k, 0) <= other.clock.get(k, 0) for k in all_keys) and
            self.clock != other.clock
        )
    
    def concurrent_with(self, other: 'VectorClock') -> bool:
        """Check if events are concurrent."""
        return not (self.happens_before(other) or other.happens_before(self))


class AgentState(BaseDocument):
    """Agent state snapshot document."""
    type: DocumentType = DocumentType.AGENT_STATE
    agent_id: str
    session_id: str
    state_snapshot: Dict[str, Any]
    vector_clock: VectorClock = Field(default_factory=VectorClock)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class KnowledgeContributor(BaseModel):
    """Knowledge document contributor."""
    agent_id: str
    contribution_timestamp: datetime
    contribution_type: str  # create, enhance, review


class Knowledge(BaseDocument):
    """Shared knowledge document."""
    type: DocumentType = DocumentType.KNOWLEDGE
    topic: str
    content: Dict[str, Any]
    contributors: List[KnowledgeContributor] = Field(default_factory=list)
    version: int = 1


class Decision(BaseDocument):
    """Consensus decision document."""
    type: DocumentType = DocumentType.DECISION
    proposal_id: str
    decision: Dict[str, Any]
    participating_agents: List[str]
    consensus_achieved_at: datetime
    votes: Dict[str, bool] = Field(default_factory=dict)
