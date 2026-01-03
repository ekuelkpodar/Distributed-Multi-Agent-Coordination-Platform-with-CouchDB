"""
Agent registry for discovery and management.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from src.core.models import Agent, AgentStatus
from src.core.config import settings
from src.database.client import CouchDBClient

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Manages agent lifecycle and discovery through CouchDB.
    """
    
    def __init__(self, client: CouchDBClient):
        self.client = client
    
    async def discover_agents(
        self,
        capability: Optional[str] = None,
        region: Optional[str] = None,
        status: AgentStatus = AgentStatus.ACTIVE
    ) -> List[Agent]:
        """
        Find agents matching criteria using CouchDB views.
        
        Args:
            capability: Required capability
            region: Preferred region
            status: Agent status filter
            
        Returns:
            List of matching agents
        """
        if capability:
            # Query by capability
            result = await self.client.query_view(
                "agents",
                "by_capability",
                startkey=[capability, region] if region else [capability],
                endkey=[capability, region or {}] if region else [capability, {}]
            )
        elif region:
            # Query by region
            result = await self.client.query_view(
                "agents",
                "by_region",
                key=region
            )
        else:
            # Query by status
            result = await self.client.query_view(
                "agents",
                "by_status",
                startkey=[status.value],
                endkey=[status.value, {}]
            )
        
        agents = []
        for row in result.get("rows", []):
            agent_data = row.get("value", {})
            if "agent_id" in agent_data:
                # Fetch full agent document
                full_doc = await self.client.get_document(f"agent:{agent_data['agent_id']}")
                if full_doc:
                    agents.append(Agent(**full_doc))
        
        return agents
    
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        doc = await self.client.get_document(f"agent:{agent_id}")
        if doc:
            return Agent(**doc)
        return None
    
    async def detect_failed_agents(self) -> List[str]:
        """
        Identify agents that have missed heartbeats.
        
        Returns:
            List of failed agent IDs
        """
        result = await self.client.query_view(
            "agents",
            "stale_heartbeats"
        )
        
        failed_agents = []
        for row in result.get("rows", []):
            agent_data = row["value"]
            failed_agents.append(agent_data["agent_id"])
        
        return failed_agents
    
    async def handle_agent_failure(self, agent_id: str):
        """
        Handle agent failure by updating status and reassigning tasks.
        
        Args:
            agent_id: Failed agent ID
        """
        # Update agent status
        agent_doc = await self.client.get_document(f"agent:{agent_id}")
        if agent_doc:
            agent_doc["status"] = AgentStatus.FAILED.value
            agent_doc["updated_at"] = datetime.utcnow().isoformat()
            await self.client.save_document(agent_doc)
            
            logger.warning(f"Agent {agent_id} marked as failed")
            
            # Get tasks assigned to this agent
            from src.core.models import TaskStatus
            tasks_result = await self.client.query_view(
                "tasks",
                "by_agent",
                startkey=[agent_id, TaskStatus.ASSIGNED.value],
                endkey=[agent_id, TaskStatus.IN_PROGRESS.value]
            )
            
            # Reassign tasks
            for row in tasks_result.get("rows", []):
                task_id = row["value"]["task_id"]
                await self._reassign_task(task_id)
    
    async def _reassign_task(self, task_id: str):
        """Reassign task from failed agent."""
        task_doc = await self.client.get_document(f"task:{task_id}")
        if task_doc:
            from src.core.models import TaskStatus
            task_doc["status"] = TaskStatus.PENDING.value
            task_doc["assigned_to"] = None
            task_doc["assigned_at"] = None
            task_doc["updated_at"] = datetime.utcnow().isoformat()
            
            if "history" not in task_doc:
                task_doc["history"] = []
            
            task_doc["history"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "status": TaskStatus.PENDING.value,
                "agent": "system",
                "message": "Task reassigned due to agent failure"
            })
            
            await self.client.save_document(task_doc)
            logger.info(f"Reassigned task {task_id}")
    
    async def get_agent_load(self, agent_id: str) -> int:
        """
        Get current task load for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Number of current tasks
        """
        from src.core.models import TaskStatus
        result = await self.client.query_view(
            "tasks",
            "by_agent",
            startkey=[agent_id, TaskStatus.ASSIGNED.value],
            endkey=[agent_id, TaskStatus.IN_PROGRESS.value],
            reduce=True,
            group_level=1
        )
        
        if result.get("rows"):
            return result["rows"][0].get("value", 0)
        return 0
    
    async def get_agents_by_load(
        self,
        capability: Optional[str] = None,
        region: Optional[str] = None
    ) -> List[tuple[Agent, int]]:
        """
        Get agents sorted by current load (ascending).
        
        Args:
            capability: Optional capability filter
            region: Optional region filter
            
        Returns:
            List of (agent, load) tuples sorted by load
        """
        agents = await self.discover_agents(
            capability=capability,
            region=region,
            status=AgentStatus.ACTIVE
        )
        
        agent_loads = []
        for agent in agents:
            load = await self.get_agent_load(agent.agent_id)
            agent_loads.append((agent, load))
        
        # Sort by load (ascending)
        agent_loads.sort(key=lambda x: x[1])
        
        return agent_loads
