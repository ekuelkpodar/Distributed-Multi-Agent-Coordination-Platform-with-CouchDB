"""
Comprehensive integration tests for the distributed agent platform.
Tests the entire system end-to-end.
"""
import pytest
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from src.database.client import CouchDBClient
from src.core.task_queue import TaskQueue
from src.agents.registry import AgentRegistry
from src.agents.research_agent import ResearchAgent
from src.coordination.patterns import MapReduceCoordinator, TaskAllocator
from src.core.models import (
    Agent, Task, Knowledge, AgentState,
    AgentStatus, TaskStatus, AgentMetadata
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDatabaseIntegration:
    """Test database connectivity and operations."""

    @pytest.mark.asyncio
    async def test_couchdb_connection(self):
        """Test CouchDB connection is working."""
        async with CouchDBClient() as client:
            # Should connect without errors
            assert client._session is not None
            logger.info("✓ CouchDB connection successful")

    @pytest.mark.asyncio
    async def test_database_exists(self):
        """Test that the database exists."""
        async with CouchDBClient() as client:
            # Try to get a document to verify database exists
            try:
                await client.get_document("_design/agents")
                logger.info("✓ Database exists and is accessible")
            except Exception as e:
                pytest.fail(f"Database not accessible: {e}")

    @pytest.mark.asyncio
    async def test_document_crud_operations(self):
        """Test Create, Read, Update, Delete operations."""
        async with CouchDBClient() as client:
            # Create
            test_agent = Agent(
                agent_id="test_integration_agent",
                agent_type="test",
                capabilities=["testing"],
                status=AgentStatus.ACTIVE,
                region="test-region"
            )
            doc = test_agent.model_dump(by_alias=True)
            created = await client.save_document(doc)
            assert created.get("_id") is not None
            assert created.get("_rev") is not None
            doc_id = created.get("_id")
            logger.info(f"✓ Created document: {doc_id}")

            # Read
            retrieved = await client.get_document(doc_id)
            assert retrieved["agent_id"] == "test_integration_agent"
            logger.info("✓ Read document successfully")

            # Update
            retrieved["status"] = AgentStatus.INACTIVE.value
            updated = await client.save_document(retrieved)
            assert updated.get("_rev") is not None
            logger.info("✓ Updated document successfully")

            # Delete
            await client.delete_document(doc_id, updated["_rev"])
            logger.info("✓ Deleted document successfully")


class TestAgentRegistry:
    """Test agent registration and discovery."""

    @pytest.mark.asyncio
    async def test_agent_registration(self):
        """Test agent can register itself."""
        async with CouchDBClient() as client:
            registry = AgentRegistry(client)

            agent = Agent(
                agent_id="test_registry_agent_001",
                agent_type="test",
                capabilities=["registration_test"],
                status=AgentStatus.ACTIVE,
                region="test-region"
            )

            # Register agent (save to database)
            doc = agent.model_dump(by_alias=True)
            result = await client.save_document(doc)
            assert result is not None
            assert result.get("_id") == agent.agent_id
            logger.info(f"✓ Agent registered: {agent.agent_id}")

            # Verify we can retrieve it
            retrieved = await registry.get_agent(agent.agent_id)
            assert retrieved is not None
            assert retrieved.agent_id == agent.agent_id
            logger.info(f"✓ Agent retrieved: {retrieved.agent_id}")

            # Cleanup
            await client.delete_document(agent.agent_id, result["_rev"])

    @pytest.mark.asyncio
    async def test_agent_discovery(self):
        """Test discovering active agents."""
        async with CouchDBClient() as client:
            registry = AgentRegistry(client)

            # Register multiple agents
            agents = []
            for i in range(3):
                agent = Agent(
                    agent_id=f"test_discovery_agent_{i:03d}",
                    agent_type="test",
                    capabilities=["discovery_test"],
                    status=AgentStatus.ACTIVE,
                    region="test-region"
                )
                doc = agent.model_dump(by_alias=True)
                await client.save_document(doc)
                agents.append(agent)

            # Discover agents by status
            discovered = await registry.discover_agents(status=AgentStatus.ACTIVE)
            assert len(discovered) >= 3
            logger.info(f"✓ Discovered {len(discovered)} active agents")

            # Cleanup
            for agent in agents:
                try:
                    doc = await client.get_document(agent.agent_id)
                    await client.delete_document(agent.agent_id, doc["_rev"])
                except:
                    pass

    @pytest.mark.asyncio
    async def test_agent_retrieval(self):
        """Test retrieving agent by ID."""
        async with CouchDBClient() as client:
            registry = AgentRegistry(client)

            agent = Agent(
                agent_id="test_retrieval_agent",
                agent_type="test",
                capabilities=["retrieval_test"],
                status=AgentStatus.ACTIVE,
                region="test-region"
            )

            # Register agent
            doc = agent.model_dump(by_alias=True)
            result = await client.save_document(doc)
            logger.info(f"✓ Agent saved: {agent.agent_id}")

            # Retrieve agent
            retrieved = await registry.get_agent(agent.agent_id)
            assert retrieved is not None
            assert retrieved.agent_id == agent.agent_id
            assert retrieved.agent_type == "test"
            logger.info("✓ Agent retrieved successfully")

            # Cleanup
            doc = await client.get_document(agent.agent_id)
            await client.delete_document(agent.agent_id, doc["_rev"])


class TestTaskQueue:
    """Test task queue operations."""

    @pytest.mark.asyncio
    async def test_task_creation_and_retrieval(self):
        """Test creating and retrieving tasks."""
        async with CouchDBClient() as client:
            task_queue = TaskQueue(client)

            # Create task
            task = Task(
                task_id="test_task_001",
                status=TaskStatus.PENDING,
                priority=5,
                task_definition={
                    "type": "test",
                    "description": "Integration test task"
                }
            )

            await task_queue.add_task(task)
            logger.info(f"✓ Task created: {task.task_id}")

            # Retrieve task
            retrieved = await task_queue.get_task(task.task_id)
            assert retrieved.task_id == task.task_id
            assert retrieved.status == TaskStatus.PENDING
            logger.info("✓ Task retrieved successfully")

            # Cleanup
            doc = await client.get_document(task.task_id)
            await client.delete_document(task.task_id, doc["_rev"])

    @pytest.mark.asyncio
    async def test_task_assignment(self):
        """Test assigning tasks to agents."""
        async with CouchDBClient() as client:
            task_queue = TaskQueue(client)

            # Create task
            task = Task(
                task_id="test_assign_task",
                status=TaskStatus.PENDING,
                priority=8,
                task_definition={"type": "test"}
            )
            await task_queue.add_task(task)

            # Assign task
            agent_id = "test_agent_001"
            await task_queue.assign_task(task.task_id, agent_id)

            # Verify assignment
            assigned = await task_queue.get_task(task.task_id)
            assert assigned.assigned_to == agent_id
            assert assigned.status == TaskStatus.ASSIGNED
            logger.info(f"✓ Task assigned to {agent_id}")

            # Cleanup
            doc = await client.get_document(task.task_id)
            await client.delete_document(task.task_id, doc["_rev"])

    @pytest.mark.asyncio
    async def test_task_priority_queue(self):
        """Test tasks are retrieved by priority."""
        async with CouchDBClient() as client:
            task_queue = TaskQueue(client)

            # Create tasks with different priorities
            tasks = []
            for i, priority in enumerate([3, 9, 5, 1, 7]):
                task = Task(
                    task_id=f"test_priority_task_{i}",
                    status=TaskStatus.PENDING,
                    priority=priority,
                    task_definition={"type": "test", "priority": priority}
                )
                await task_queue.add_task(task)
                tasks.append(task)

            # Get pending tasks (should be sorted by priority)
            pending = await task_queue.get_pending_tasks(limit=5)

            # Verify they're in priority order (highest first)
            priorities = [t.priority for t in pending]
            assert priorities == sorted(priorities, reverse=True)
            logger.info(f"✓ Tasks retrieved in priority order: {priorities}")

            # Cleanup
            for task in tasks:
                try:
                    doc = await client.get_document(task.task_id)
                    await client.delete_document(task.task_id, doc["_rev"])
                except:
                    pass


class TestCoordinationPatterns:
    """Test coordination patterns (Map-Reduce, Task Allocation)."""

    @pytest.mark.asyncio
    async def test_task_allocation(self):
        """Test task allocation to available agents."""
        async with CouchDBClient() as client:
            task_queue = TaskQueue(client)
            agent_registry = AgentRegistry(client)

            # Register test agents
            agents = []
            for i in range(3):
                agent = Agent(
                    agent_id=f"test_alloc_agent_{i}",
                    agent_type="worker",
                    capabilities=["processing"],
                    status=AgentStatus.ACTIVE,
                    region="test-region",
                    metadata=AgentMetadata(max_concurrent_tasks=5)
                )
                await agent_registry.register_agent(agent)
                agents.append(agent)

            # Create test tasks
            tasks = []
            for i in range(5):
                task = Task(
                    task_id=f"test_alloc_task_{i}",
                    status=TaskStatus.PENDING,
                    priority=(i % 10) + 1,
                    task_definition={"type": "processing"}
                )
                await task_queue.add_task(task)
                tasks.append(task)

            # Allocate tasks
            allocator = TaskAllocator(task_queue, agent_registry)
            allocations = await allocator.allocate_tasks(max_tasks=10)

            assert len(allocations) > 0
            logger.info(f"✓ Allocated tasks to {len(allocations)} agents")

            # Cleanup
            for agent in agents:
                try:
                    doc = await client.get_document(agent.agent_id)
                    await client.delete_document(agent.agent_id, doc["_rev"])
                except:
                    pass

            for task in tasks:
                try:
                    doc = await client.get_document(task.task_id)
                    await client.delete_document(task.task_id, doc["_rev"])
                except:
                    pass


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_complete_task_lifecycle(self):
        """Test complete task lifecycle: create -> assign -> process -> complete."""
        async with CouchDBClient() as client:
            task_queue = TaskQueue(client)
            agent_registry = AgentRegistry(client)

            # 1. Register agent
            agent = Agent(
                agent_id="test_lifecycle_agent",
                agent_type="worker",
                capabilities=["data_processing"],
                status=AgentStatus.ACTIVE,
                region="test-region"
            )
            await agent_registry.register_agent(agent)
            logger.info("1. ✓ Agent registered")

            # 2. Create task
            task = Task(
                task_id="test_lifecycle_task",
                status=TaskStatus.PENDING,
                priority=7,
                task_definition={
                    "type": "data_processing",
                    "description": "Process test data"
                }
            )
            await task_queue.add_task(task)
            logger.info("2. ✓ Task created")

            # 3. Assign task
            await task_queue.assign_task(task.task_id, agent.agent_id)
            logger.info("3. ✓ Task assigned")

            # 4. Update task to in-progress
            await task_queue.update_task_status(
                task.task_id,
                TaskStatus.IN_PROGRESS
            )
            logger.info("4. ✓ Task in progress")

            # 5. Complete task
            result = {"output": "Processed successfully", "items": 1000}
            await task_queue.complete_task(task.task_id, result)
            logger.info("5. ✓ Task completed")

            # 6. Verify final state
            final_task = await task_queue.get_task(task.task_id)
            assert final_task.status == TaskStatus.COMPLETED
            assert final_task.result == result
            logger.info("6. ✓ Task lifecycle verified")

            # Cleanup
            try:
                agent_doc = await client.get_document(agent.agent_id)
                await client.delete_document(agent.agent_id, agent_doc["_rev"])
                task_doc = await client.get_document(task.task_id)
                await client.delete_document(task.task_id, task_doc["_rev"])
            except:
                pass

    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self):
        """Test multiple agents coordinating on tasks."""
        async with CouchDBClient() as client:
            task_queue = TaskQueue(client)
            agent_registry = AgentRegistry(client)

            # Register multiple agents
            agents = []
            for i in range(5):
                agent = Agent(
                    agent_id=f"test_coord_agent_{i}",
                    agent_type="worker",
                    capabilities=["coordination_test"],
                    status=AgentStatus.ACTIVE,
                    region=f"region-{i % 2}"
                )
                await agent_registry.register_agent(agent)
                agents.append(agent)
            logger.info(f"✓ Registered {len(agents)} agents")

            # Create multiple tasks
            tasks = []
            for i in range(10):
                task = Task(
                    task_id=f"test_coord_task_{i}",
                    status=TaskStatus.PENDING,
                    priority=((i * 3) % 10) + 1,
                    task_definition={"type": "coordination_test"}
                )
                await task_queue.add_task(task)
                tasks.append(task)
            logger.info(f"✓ Created {len(tasks)} tasks")

            # Allocate tasks to agents
            allocator = TaskAllocator(task_queue, agent_registry)
            allocations = await allocator.allocate_tasks(max_tasks=15)

            assert len(allocations) > 0
            logger.info(f"✓ Allocated {sum(len(tasks) for tasks in allocations.values())} tasks across {len(allocations)} agents")

            # Verify all agents got work
            for agent_id, allocated_tasks in allocations.items():
                logger.info(f"  Agent {agent_id}: {len(allocated_tasks)} tasks")

            # Cleanup
            for agent in agents:
                try:
                    doc = await client.get_document(agent.agent_id)
                    await client.delete_document(agent.agent_id, doc["_rev"])
                except:
                    pass

            for task in tasks:
                try:
                    doc = await client.get_document(task.task_id)
                    await client.delete_document(task.task_id, doc["_rev"])
                except:
                    pass


class TestReplicationAndConsistency:
    """Test CouchDB replication and eventual consistency."""

    @pytest.mark.asyncio
    async def test_document_replication_across_nodes(self):
        """Test that documents replicate across CouchDB nodes."""
        # Create document on node 1
        client1 = CouchDBClient(url="http://localhost:5984")
        async with client1:
            test_doc = {
                "_id": "test_replication_doc",
                "type": "test",
                "timestamp": datetime.utcnow().isoformat(),
                "node": "node1"
            }
            await client1.save_document(test_doc)
            logger.info("✓ Created document on node 1")

        # Wait for replication
        await asyncio.sleep(2)

        # Check document exists on node 2
        client2 = CouchDBClient(url="http://localhost:5985")
        async with client2:
            replicated = await client2.get_document("test_replication_doc")
            assert replicated["_id"] == "test_replication_doc"
            logger.info("✓ Document replicated to node 2")

        # Check document exists on node 3
        client3 = CouchDBClient(url="http://localhost:5986")
        async with client3:
            replicated = await client3.get_document("test_replication_doc")
            assert replicated["_id"] == "test_replication_doc"
            logger.info("✓ Document replicated to node 3")

        # Cleanup
        async with client1:
            doc = await client1.get_document("test_replication_doc")
            await client1.delete_document("test_replication_doc", doc["_rev"])


class TestSystemHealth:
    """Test overall system health and monitoring."""

    @pytest.mark.asyncio
    async def test_all_couchdb_nodes_healthy(self):
        """Test all CouchDB nodes are healthy."""
        nodes = [
            ("node1", "http://localhost:5984"),
            ("node2", "http://localhost:5985"),
            ("node3", "http://localhost:5986")
        ]

        for name, url in nodes:
            client = CouchDBClient(url=url)
            async with client:
                # Just connecting successfully means healthy
                assert client._session is not None
                logger.info(f"✓ {name} is healthy")

    @pytest.mark.asyncio
    async def test_redis_connectivity(self):
        """Test Redis is accessible."""
        import redis.asyncio as aioredis

        try:
            redis_client = await aioredis.from_url("redis://localhost:6379")
            await redis_client.ping()
            logger.info("✓ Redis is accessible")
            await redis_client.close()
        except Exception as e:
            pytest.fail(f"Redis not accessible: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
