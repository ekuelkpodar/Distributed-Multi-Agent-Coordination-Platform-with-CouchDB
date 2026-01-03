"""
Distributed task queue with priority and dependency management.
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.models import Task, TaskStatus, TaskHistory
from src.core.config import settings
from src.database.client import CouchDBClient

logger = logging.getLogger(__name__)


class TaskQueue:
    """
    Distributed task queue with priority and dependency management.
    """
    
    def __init__(self, client: CouchDBClient):
        self.client = client
    
    async def create_task(
        self,
        task_definition: Dict[str, Any],
        priority: int = 5,
        dependencies: List[str] = None
    ) -> Task:
        """
        Create new task in the queue.
        
        Args:
            task_definition: Task configuration and parameters
            priority: Task priority (1-10, higher is more urgent)
            dependencies: List of task IDs that must complete first
            
        Returns:
            Created task
        """
        task_id = uuid.uuid4().hex
        
        task = Task(
            id=f"task:{task_id}",
            task_id=task_id,
            status=TaskStatus.PENDING,
            priority=min(max(priority, 1), 10),  # Clamp to 1-10
            task_definition=task_definition,
            dependencies=dependencies or [],
            history=[
                TaskHistory(
                    timestamp=datetime.utcnow(),
                    status=TaskStatus.PENDING,
                    agent="system",
                    message="Task created"
                )
            ]
        )
        
        task_doc = task.model_dump(by_alias=True)
        await self.client.save_document(task_doc)
        
        logger.info(f"Created task {task_id} with priority {priority}")
        return task
    
    async def assign_task(
        self,
        task_id: str,
        agent_id: str
    ) -> Optional[Task]:
        """
        Assign task to specific agent with optimistic locking.
        
        Args:
            task_id: Task ID
            agent_id: Agent ID
            
        Returns:
            Updated task or None if assignment failed
        """
        try:
            task_doc = await self.client.get_document(f"task:{task_id}")
            
            if not task_doc:
                logger.error(f"Task {task_id} not found")
                return None
            
            # Check if task is available for assignment
            if task_doc["status"] != TaskStatus.PENDING.value:
                logger.warning(f"Task {task_id} is not pending (status: {task_doc['status']})")
                return None
            
            # Check dependencies
            if await self._has_pending_dependencies(task_doc.get("dependencies", [])):
                logger.warning(f"Task {task_id} has pending dependencies")
                return None
            
            # Update task
            task_doc["status"] = TaskStatus.ASSIGNED.value
            task_doc["assigned_to"] = agent_id
            task_doc["assigned_at"] = datetime.utcnow().isoformat()
            task_doc["updated_at"] = datetime.utcnow().isoformat()
            
            if "history" not in task_doc:
                task_doc["history"] = []
            
            task_doc["history"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "status": TaskStatus.ASSIGNED.value,
                "agent": agent_id,
                "message": f"Task assigned to agent {agent_id}"
            })
            
            # Save with optimistic locking (will fail if _rev changed)
            await self.client.save_document(task_doc)
            
            logger.info(f"Assigned task {task_id} to agent {agent_id}")
            return Task(**task_doc)
            
        except Exception as e:
            logger.error(f"Failed to assign task {task_id}: {e}")
            return None
    
    async def _has_pending_dependencies(self, dependencies: List[str]) -> bool:
        """Check if any dependencies are not completed."""
        if not dependencies:
            return False
        
        for dep_id in dependencies:
            dep_doc = await self.client.get_document(f"task:{dep_id}")
            if not dep_doc or dep_doc["status"] != TaskStatus.COMPLETED.value:
                return True
        
        return False
    
    async def get_next_task(
        self,
        agent_id: str,
        capabilities: List[str]
    ) -> Optional[Task]:
        """
        Get next available task matching agent capabilities.
        
        Args:
            agent_id: Requesting agent ID
            capabilities: Agent capabilities
            
        Returns:
            Next available task or None
        """
        # Query ready-to-execute tasks sorted by priority
        result = await self.client.query_view(
            "tasks",
            "ready_to_execute",
            descending=True,  # High priority first
            limit=50
        )
        
        for row in result.get("rows", []):
            task_data = row["value"]
            task_id = task_data["task_id"]
            
            # Get full task document
            task_doc = await self.client.get_document(f"task:{task_id}")
            if not task_doc:
                continue
            
            # Check if agent can handle this task
            required_caps = task_doc["task_definition"].get("required_capabilities", [])
            if required_caps and not all(cap in capabilities for cap in required_caps):
                continue
            
            # Try to assign task
            task = await self.assign_task(task_id, agent_id)
            if task:
                return task
        
        return None
    
    async def complete_task(
        self,
        task_id: str,
        result: Any
    ) -> Optional[Task]:
        """
        Mark task as complete and unlock dependent tasks.
        
        Args:
            task_id: Task ID
            result: Task result
            
        Returns:
            Updated task
        """
        task_doc = await self.client.get_document(f"task:{task_id}")
        
        if not task_doc:
            logger.error(f"Task {task_id} not found")
            return None
        
        task_doc["status"] = TaskStatus.COMPLETED.value
        task_doc["result"] = result
        task_doc["updated_at"] = datetime.utcnow().isoformat()
        
        if "history" not in task_doc:
            task_doc["history"] = []
        
        task_doc["history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "status": TaskStatus.COMPLETED.value,
            "agent": task_doc.get("assigned_to", "unknown"),
            "message": "Task completed successfully"
        })
        
        await self.client.save_document(task_doc)
        
        logger.info(f"Completed task {task_id}")
        return Task(**task_doc)
    
    async def handle_task_failure(
        self,
        task_id: str,
        error: Exception,
        retry: bool = True
    ) -> Optional[Task]:
        """
        Handle task failures with exponential backoff retry.
        
        Args:
            task_id: Task ID
            error: Error that caused failure
            retry: Whether to retry the task
            
        Returns:
            Updated task
        """
        task_doc = await self.client.get_document(f"task:{task_id}")
        
        if not task_doc:
            logger.error(f"Task {task_id} not found")
            return None
        
        retry_count = task_doc.get("retry_count", 0)
        max_retries = task_doc.get("max_retries", settings.task_retry_max_attempts)
        
        task_doc["error"] = str(error)
        task_doc["retry_count"] = retry_count + 1
        task_doc["updated_at"] = datetime.utcnow().isoformat()
        
        if "history" not in task_doc:
            task_doc["history"] = []
        
        # Decide whether to retry
        if retry and retry_count < max_retries:
            # Reset to pending for retry
            task_doc["status"] = TaskStatus.PENDING.value
            task_doc["assigned_to"] = None
            task_doc["assigned_at"] = None
            
            task_doc["history"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "status": TaskStatus.PENDING.value,
                "agent": "system",
                "message": f"Task failed, retry {retry_count + 1}/{max_retries}: {str(error)}"
            })
            
            logger.warning(f"Task {task_id} failed, retrying ({retry_count + 1}/{max_retries})")
        else:
            # Mark as permanently failed
            task_doc["status"] = TaskStatus.FAILED.value
            
            task_doc["history"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "status": TaskStatus.FAILED.value,
                "agent": task_doc.get("assigned_to", "unknown"),
                "message": f"Task permanently failed: {str(error)}"
            })
            
            logger.error(f"Task {task_id} permanently failed after {retry_count} retries")
        
        await self.client.save_document(task_doc)
        return Task(**task_doc)
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        task_doc = await self.client.get_document(f"task:{task_id}")
        if task_doc:
            return Task(**task_doc)
        return None
    
    async def get_pending_tasks(self, limit: int = 100) -> List[Task]:
        """Get all pending tasks."""
        result = await self.client.query_view(
            "tasks",
            "pending_by_priority",
            descending=True,
            limit=limit
        )
        
        tasks = []
        for row in result.get("rows", []):
            task_id = row["value"]["task_id"]
            task = await self.get_task(task_id)
            if task:
                tasks.append(task)
        
        return tasks
    
    async def get_task_stats(self) -> Dict[str, int]:
        """Get task queue statistics."""
        result = await self.client.query_view(
            "tasks",
            "by_status",
            group=True
        )
        
        stats = {}
        for row in result.get("rows", []):
            status = row["key"][0]
            count = row["value"]
            stats[status] = count
        
        return stats
