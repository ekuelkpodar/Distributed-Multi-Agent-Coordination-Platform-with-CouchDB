#!/usr/bin/env python3
"""
Example: Distributed research using map-reduce pattern.
"""
import asyncio
import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.client import CouchDBClient
from src.core.task_queue import TaskQueue
from src.agents.registry import AgentRegistry
from src.agents.research_agent import ResearchAgent
from src.coordination.patterns import MapReduceCoordinator, TaskAllocator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_distributed_research():
    """
    Demonstrate distributed research using map-reduce pattern.
    """
    logger.info("=" * 70)
    logger.info("Distributed Research Example - Map-Reduce Pattern")
    logger.info("=" * 70)
    
    # Initialize CouchDB client
    async with CouchDBClient() as client:
        # Create task queue and agent registry
        task_queue = TaskQueue(client)
        agent_registry = AgentRegistry(client)
        
        # Start research agents
        logger.info("\n1. Starting research agents...")
        agents = []
        for i in range(3):
            agent = ResearchAgent(
                region=["us-east-1", "eu-west-1", "ap-south-1"][i]
            )
            await agent.start()
            agents.append(agent)
            logger.info(f"   ✓ Started agent: {agent.agent_id} in {agent.region}")
        
        # Wait for agents to register
        await asyncio.sleep(2)
        
        # Verify agent registration
        active_agents = await agent_registry.discover_agents()
        logger.info(f"\n2. Discovered {len(active_agents)} active agents")
        for agent in active_agents:
            logger.info(f"   - {agent.agent_id}: {agent.capabilities}")
        
        # Create map-reduce coordinator
        map_reduce = MapReduceCoordinator(task_queue, agent_registry)
        
        # Prepare research data
        research_topics = [
            "Distributed AI Systems",
            "CouchDB Replication",
            "Vector Clocks",
            "Conflict Resolution",
            "Agent Coordination",
            "Eventual Consistency",
            "Map-Reduce Patterns",
            "Multi-Agent Systems",
            "Database Partitioning",
            "Consensus Algorithms"
        ]
        
        logger.info(f"\n3. Starting map-reduce research on {len(research_topics)} topics...")
        
        # Execute map-reduce
        try:
            # Start task allocator in background
            allocator = TaskAllocator(task_queue, agent_registry)
            allocation_task = asyncio.create_task(continuous_allocation(allocator))
            
            # Run map-reduce
            result = await map_reduce.execute(
                data=research_topics,
                map_action="map",
                reduce_action="reduce",
                num_mappers=3,
                timeout=60
            )
            
            logger.info("\n4. Map-Reduce Results:")
            logger.info(f"   Total items processed: {result.get('total_items')}")
            logger.info(f"   Chunks processed: {result.get('chunks_processed')}")
            logger.info(f"   Final result: {result.get('final_result')}")
            
            # Cancel allocation task
            allocation_task.cancel()
            
        except Exception as e:
            logger.error(f"\n✗ Map-reduce failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Get task statistics
        stats = await task_queue.get_task_stats()
        logger.info("\n5. Task Queue Statistics:")
        for status, count in stats.items():
            logger.info(f"   {status}: {count}")
        
        # Stop agents
        logger.info("\n6. Stopping agents...")
        for agent in agents:
            await agent.stop()
            logger.info(f"   ✓ Stopped agent: {agent.agent_id}")
        
        logger.info("\n" + "=" * 70)
        logger.info("Example completed successfully!")
        logger.info("=" * 70)


async def continuous_allocation(allocator: TaskAllocator):
    """Continuously allocate tasks to agents."""
    while True:
        try:
            allocations = await allocator.allocate_tasks(max_tasks=50)
            if allocations:
                logger.info(f"   Allocated tasks to {len(allocations)} agents")
            await asyncio.sleep(2)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in task allocation: {e}")


async def main():
    """Main entry point."""
    try:
        await run_distributed_research()
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
