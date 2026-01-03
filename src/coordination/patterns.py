"""
Multi-agent coordination patterns.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum

from src.core.models import Task, Agent
from src.core.task_queue import TaskQueue
from src.agents.registry import AgentRegistry

logger = logging.getLogger(__name__)


class CoordinationPattern(ABC):
    """Base class for coordination patterns."""
    
    def __init__(self, task_queue: TaskQueue, agent_registry: AgentRegistry):
        self.task_queue = task_queue
        self.agent_registry = agent_registry
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute the coordination pattern."""
        pass


class MapReduceCoordinator(CoordinationPattern):
    """
    Coordinate map-reduce style parallel processing across agents.
    """
    
    async def execute(
        self,
        data: List[Any],
        map_action: str,
        reduce_action: str,
        map_params: Dict[str, Any] = None,
        reduce_params: Dict[str, Any] = None,
        num_mappers: int = None,
        timeout: int = 300
    ) -> Any:
        """
        Execute map-reduce workflow.
        
        Args:
            data: Input data to process
            map_action: Map function identifier
            reduce_action: Reduce function identifier
            map_params: Additional parameters for map tasks
            reduce_params: Additional parameters for reduce task
            num_mappers: Number of map tasks (default: auto-split)
            timeout: Timeout in seconds
            
        Returns:
            Final reduced result
        """
        logger.info(f"Starting map-reduce with {len(data)} items")
        
        # Split phase
        num_mappers = num_mappers or max(1, len(data) // 10)
        chunks = self._split_data(data, num_mappers)
        
        logger.info(f"Split data into {len(chunks)} chunks")
        
        # Map phase
        map_task_ids = []
        for i, chunk in enumerate(chunks):
            task_def = {
                "action": map_action,
                "data": chunk,
                "chunk_index": i,
                **(map_params or {})
            }
            
            task = await self.task_queue.create_task(
                task_definition=task_def,
                priority=7
            )
            map_task_ids.append(task.task_id)
        
        logger.info(f"Created {len(map_task_ids)} map tasks")
        
        # Wait for all map tasks to complete
        map_results = await self._wait_for_tasks(map_task_ids, timeout)
        
        logger.info(f"Completed {len(map_results)} map tasks")
        
        # Reduce phase
        reduce_task_def = {
            "action": reduce_action,
            "map_results": map_results,
            **(reduce_params or {})
        }
        
        reduce_task = await self.task_queue.create_task(
            task_definition=reduce_task_def,
            priority=8
        )
        
        logger.info(f"Created reduce task {reduce_task.task_id}")
        
        # Wait for reduce task
        result = await self._wait_for_task(reduce_task.task_id, timeout)
        
        logger.info("Map-reduce completed successfully")
        return result
    
    def _split_data(self, data: List[Any], num_chunks: int) -> List[List[Any]]:
        """Split data into chunks."""
        chunk_size = max(1, len(data) // num_chunks)
        chunks = []
        
        for i in range(0, len(data), chunk_size):
            chunks.append(data[i:i + chunk_size])
        
        return chunks
    
    async def _wait_for_task(self, task_id: str, timeout: int) -> Any:
        """Wait for a single task to complete."""
        start_time = datetime.utcnow()
        
        while True:
            task = await self.task_queue.get_task(task_id)
            
            if not task:
                raise Exception(f"Task {task_id} not found")
            
            if task.status.value == "completed":
                return task.result
            
            if task.status.value == "failed":
                raise Exception(f"Task {task_id} failed: {task.error}")
            
            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > timeout:
                raise TimeoutError(f"Task {task_id} timed out after {timeout}s")
            
            await asyncio.sleep(1)
    
    async def _wait_for_tasks(self, task_ids: List[str], timeout: int) -> List[Any]:
        """Wait for multiple tasks to complete."""
        results = await asyncio.gather(*[
            self._wait_for_task(task_id, timeout)
            for task_id in task_ids
        ])
        return results


class PipelineCoordinator(CoordinationPattern):
    """
    Coordinate sequential task processing pipeline.
    """
    
    async def execute(
        self,
        initial_input: Any,
        stages: List[Dict[str, Any]],
        timeout: int = 300
    ) -> Any:
        """
        Execute pipeline.
        
        Args:
            initial_input: Initial input data
            stages: List of pipeline stages, each with 'action' and 'parameters'
            timeout: Timeout in seconds
            
        Returns:
            Final output
        """
        logger.info(f"Starting pipeline with {len(stages)} stages")
        
        current_input = initial_input
        previous_task_id = None
        
        for i, stage in enumerate(stages):
            logger.info(f"Executing pipeline stage {i+1}/{len(stages)}: {stage.get('action')}")
            
            task_def = {
                "action": stage["action"],
                "input": current_input,
                **stage.get("parameters", {})
            }
            
            # Create task with dependency on previous stage
            dependencies = [previous_task_id] if previous_task_id else []
            
            task = await self.task_queue.create_task(
                task_definition=task_def,
                priority=6,
                dependencies=dependencies
            )
            
            # Wait for task completion
            result = await self._wait_for_task(task.task_id, timeout)
            
            current_input = result
            previous_task_id = task.task_id
        
        logger.info("Pipeline completed successfully")
        return current_input
    
    async def _wait_for_task(self, task_id: str, timeout: int) -> Any:
        """Wait for task completion."""
        start_time = datetime.utcnow()
        
        while True:
            task = await self.task_queue.get_task(task_id)
            
            if not task:
                raise Exception(f"Task {task_id} not found")
            
            if task.status.value == "completed":
                return task.result
            
            if task.status.value == "failed":
                raise Exception(f"Task {task_id} failed: {task.error}")
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > timeout:
                raise TimeoutError(f"Task {task_id} timed out")
            
            await asyncio.sleep(1)


class Bid:
    """Agent bid for task."""
    
    def __init__(
        self,
        agent_id: str,
        amount: float,
        estimated_completion_time: int,
        confidence: float = 1.0
    ):
        self.agent_id = agent_id
        self.amount = amount
        self.estimated_completion_time = estimated_completion_time
        self.confidence = confidence


class AuctionCoordinator(CoordinationPattern):
    """
    Coordinate task allocation through agent bidding.
    """
    
    async def execute(
        self,
        task: Task,
        auction_timeout: int = 10,
        capability_filter: Optional[str] = None
    ) -> Optional[Agent]:
        """
        Run auction for task assignment.
        
        Args:
            task: Task to assign
            auction_timeout: Auction timeout in seconds
            capability_filter: Required capability
            
        Returns:
            Winning agent or None
        """
        logger.info(f"Starting auction for task {task.task_id}")
        
        # Get eligible agents
        agents = await self.agent_registry.get_agents_by_load(
            capability=capability_filter
        )
        
        if not agents:
            logger.warning("No eligible agents for auction")
            return None
        
        logger.info(f"Found {len(agents)} eligible agents")
        
        # Collect bids
        bids = []
        for agent, load in agents:
            bid = await self._request_bid(agent, task, load)
            if bid and bid.amount > 0:
                bids.append(bid)
        
        if not bids:
            logger.warning("No valid bids received")
            return None
        
        logger.info(f"Received {len(bids)} bids")
        
        # Select winner (highest bid, lowest completion time)
        winning_bid = max(
            bids,
            key=lambda b: (b.amount, -b.estimated_completion_time, b.confidence)
        )
        
        # Assign task to winner
        assigned_task = await self.task_queue.assign_task(
            task.task_id,
            winning_bid.agent_id
        )
        
        if assigned_task:
            winner = await self.agent_registry.get_agent(winning_bid.agent_id)
            logger.info(f"Auction won by agent {winning_bid.agent_id}")
            return winner
        
        return None
    
    async def _request_bid(
        self,
        agent: Agent,
        task: Task,
        current_load: int
    ) -> Optional[Bid]:
        """
        Request bid from agent.
        
        Calculates bid based on agent capacity and task priority.
        """
        # Calculate bid amount based on:
        # 1. Available capacity
        # 2. Task priority
        # 3. Capability match
        
        max_tasks = agent.metadata.max_concurrent_tasks
        available_capacity = max_tasks - current_load
        
        if available_capacity <= 0:
            return None
        
        # Base bid on available capacity
        capacity_score = available_capacity / max_tasks
        
        # Boost bid for high priority tasks
        priority_multiplier = task.priority / 10.0
        
        # Calculate final bid
        bid_amount = capacity_score * priority_multiplier * 100
        
        # Estimate completion time based on current load
        estimated_time = 60 + (current_load * 30)  # Base 60s + 30s per task
        
        # Confidence based on capability match
        required_caps = task.task_definition.get("required_capabilities", [])
        if required_caps:
            matched_caps = len(set(required_caps) & set(agent.capabilities))
            confidence = matched_caps / len(required_caps)
        else:
            confidence = 1.0
        
        return Bid(
            agent_id=agent.agent_id,
            amount=bid_amount,
            estimated_completion_time=estimated_time,
            confidence=confidence
        )


class TaskAllocator:
    """
    Intelligent task allocation based on agent capabilities and load.
    """
    
    def __init__(self, task_queue: TaskQueue, agent_registry: AgentRegistry):
        self.task_queue = task_queue
        self.agent_registry = agent_registry
    
    async def allocate_tasks(self, max_tasks: int = 100) -> Dict[str, List[str]]:
        """
        Allocate pending tasks to available agents.
        
        Args:
            max_tasks: Maximum tasks to allocate
            
        Returns:
            Dict mapping agent_id to list of assigned task_ids
        """
        # Get pending tasks
        pending_tasks = await self.task_queue.get_pending_tasks(limit=max_tasks)
        
        if not pending_tasks:
            return {}
        
        logger.info(f"Allocating {len(pending_tasks)} pending tasks")
        
        allocations = {}
        
        for task in pending_tasks:
            # Find best agent for task
            agent = await self._find_best_agent(task)
            
            if agent:
                # Assign task
                assigned = await self.task_queue.assign_task(task.task_id, agent.agent_id)
                
                if assigned:
                    if agent.agent_id not in allocations:
                        allocations[agent.agent_id] = []
                    allocations[agent.agent_id].append(task.task_id)
        
        logger.info(f"Allocated {sum(len(tasks) for tasks in allocations.values())} tasks")
        return allocations
    
    async def _find_best_agent(self, task: Task) -> Optional[Agent]:
        """Find best agent for task based on scoring."""
        # Get agents sorted by load
        agents_with_load = await self.agent_registry.get_agents_by_load()
        
        if not agents_with_load:
            return None
        
        best_agent = None
        best_score = -1
        
        for agent, load in agents_with_load:
            score = self._calculate_agent_score(agent, task, load)
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent
    
    def _calculate_agent_score(
        self,
        agent: Agent,
        task: Task,
        current_load: int
    ) -> float:
        """Calculate suitability score for agent-task pairing."""
        score = 0.0
        
        # Capability match (0-40 points)
        required_caps = task.task_definition.get("required_capabilities", [])
        if required_caps:
            matched = len(set(required_caps) & set(agent.capabilities))
            capability_score = (matched / len(required_caps)) * 40
            score += capability_score
        else:
            score += 40  # No specific requirements
        
        # Load factor (0-30 points)
        max_load = agent.metadata.max_concurrent_tasks
        if current_load < max_load:
            load_factor = 1 - (current_load / max_load)
            score += load_factor * 30
        
        # Priority match (0-20 points)
        if task.priority >= 8:
            score += 20
        elif task.priority >= 5:
            score += 10
        
        # Region preference (0-10 points)
        preferred_region = task.task_definition.get("preferred_region")
        if preferred_region and agent.region == preferred_region:
            score += 10
        
        return score
