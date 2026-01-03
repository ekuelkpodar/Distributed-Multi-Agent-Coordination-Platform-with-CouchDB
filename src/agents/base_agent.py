"""
Base agent implementation with coordination capabilities.
"""
import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.models import Agent, AgentMetadata, AgentStatus, Task, TaskStatus
from src.core.config import settings
from src.database.client import CouchDBClient

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents in the distributed system.
    
    Provides core functionality for:
    - Agent registration and discovery
    - Heartbeat management
    - Task execution
    - State management
    """
    
    def __init__(
        self,
        agent_type: str,
        capabilities: List[str],
        region: str = "us-east-1",
        max_concurrent_tasks: int = None,
        model: str = "claude-sonnet-4"
    ):
        self.agent_id = f"{agent_type}-{uuid.uuid4().hex[:8]}"
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.region = region
        self.model = model
        self.max_concurrent_tasks = max_concurrent_tasks or settings.max_concurrent_tasks
        
        self.client: Optional[CouchDBClient] = None
        self.status = AgentStatus.INACTIVE
        self.current_tasks: List[str] = []
        
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start the agent and register with coordination system."""
        self.client = CouchDBClient()
        await self.client.connect()
        
        # Register agent
        await self._register()
        
        # Start heartbeat
        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        self.status = AgentStatus.ACTIVE
        logger.info(f"Agent {self.agent_id} started in region {self.region}")
    
    async def stop(self):
        """Stop the agent and deregister."""
        self._running = False
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Update status to inactive
        await self._update_status(AgentStatus.INACTIVE)
        
        if self.client:
            await self.client.close()
        
        logger.info(f"Agent {self.agent_id} stopped")
    
    async def _register(self):
        """Register agent in CouchDB."""
        agent_doc = Agent(
            id=f"agent:{self.agent_id}",
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            capabilities=self.capabilities,
            status=AgentStatus.ACTIVE,
            region=self.region,
            heartbeat_timestamp=datetime.utcnow(),
            metadata=AgentMetadata(
                version="1.0.0",
                model=self.model,
                max_concurrent_tasks=self.max_concurrent_tasks
            ),
            current_tasks=[]
        )
        
        await self.client.save_document(agent_doc.model_dump(by_alias=True))
        logger.info(f"Registered agent {self.agent_id}")
    
    async def _heartbeat_loop(self):
        """Periodic heartbeat to indicate agent is alive."""
        while self._running:
            try:
                await self._update_heartbeat()
                await asyncio.sleep(settings.agent_heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    async def _update_heartbeat(self):
        """Update agent heartbeat timestamp."""
        try:
            agent_doc = await self.client.get_document(f"agent:{self.agent_id}")
            if agent_doc:
                agent_doc["heartbeat_timestamp"] = datetime.utcnow().isoformat()
                agent_doc["current_tasks"] = self.current_tasks
                await self.client.save_document(agent_doc)
        except Exception as e:
            logger.error(f"Failed to update heartbeat: {e}")
    
    async def _update_status(self, status: AgentStatus):
        """Update agent status."""
        self.status = status
        try:
            agent_doc = await self.client.get_document(f"agent:{self.agent_id}")
            if agent_doc:
                agent_doc["status"] = status.value
                agent_doc["updated_at"] = datetime.utcnow().isoformat()
                await self.client.save_document(agent_doc)
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
    
    async def execute_task(self, task: Task) -> Any:
        """
        Execute a task.
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
        """
        if len(self.current_tasks) >= self.max_concurrent_tasks:
            raise Exception(f"Agent at capacity ({self.max_concurrent_tasks} tasks)")
        
        self.current_tasks.append(task.task_id)
        
        try:
            # Update task status to in_progress
            await self._update_task_status(
                task.task_id,
                TaskStatus.IN_PROGRESS,
                "Task execution started"
            )
            
            # Execute task logic
            result = await self._execute_task_logic(task)
            
            # Mark task as completed
            await self._update_task_status(
                task.task_id,
                TaskStatus.COMPLETED,
                "Task completed successfully",
                result=result
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            
            # Mark task as failed
            await self._update_task_status(
                task.task_id,
                TaskStatus.FAILED,
                f"Task failed: {str(e)}",
                error=str(e)
            )
            
            raise
        finally:
            self.current_tasks.remove(task.task_id)
    
    @abstractmethod
    async def _execute_task_logic(self, task: Task) -> Any:
        """
        Execute task-specific logic.
        Must be implemented by subclasses.
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
        """
        pass
    
    async def _update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        message: str,
        result: Any = None,
        error: str = None
    ):
        """Update task status in database."""
        try:
            task_doc = await self.client.get_document(f"task:{task_id}")
            if task_doc:
                task_doc["status"] = status.value
                task_doc["updated_at"] = datetime.utcnow().isoformat()
                
                if result is not None:
                    task_doc["result"] = result
                
                if error:
                    task_doc["error"] = error
                
                # Add to history
                if "history" not in task_doc:
                    task_doc["history"] = []
                
                task_doc["history"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": status.value,
                    "agent": self.agent_id,
                    "message": message
                })
                
                await self.client.save_document(task_doc)
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
    
    async def get_available_capacity(self) -> int:
        """Get number of tasks this agent can still accept."""
        return self.max_concurrent_tasks - len(self.current_tasks)
    
    def can_handle_task(self, task: Task) -> bool:
        """Check if agent can handle this task based on capabilities."""
        required_capabilities = task.task_definition.get("required_capabilities", [])
        return all(cap in self.capabilities for cap in required_capabilities)
