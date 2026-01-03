"""
Tests for task queue functionality.
"""
import pytest
from datetime import datetime

from src.core.models import Task, TaskStatus
from src.core.task_queue import TaskQueue
from src.database.client import CouchDBClient


@pytest.mark.asyncio
class TestTaskQueue:
    """Test task queue operations."""
    
    async def test_create_task(self):
        """Test task creation."""
        async with CouchDBClient() as client:
            # Create test database
            await client.create_database("test_db")
            
            try:
                task_queue = TaskQueue(client)
                
                # Create task
                task = await task_queue.create_task(
                    task_definition={"action": "test"},
                    priority=8
                )
                
                assert task is not None
                assert task.status == TaskStatus.PENDING
                assert task.priority == 8
                assert task.task_definition["action"] == "test"
                
            finally:
                # Cleanup
                await client.delete_database("test_db")
    
    async def test_assign_task(self):
        """Test task assignment."""
        async with CouchDBClient() as client:
            await client.create_database("test_db")
            
            try:
                task_queue = TaskQueue(client)
                
                # Create task
                task = await task_queue.create_task(
                    task_definition={"action": "test"}
                )
                
                # Assign task
                assigned = await task_queue.assign_task(
                    task.task_id,
                    "test-agent-001"
                )
                
                assert assigned is not None
                assert assigned.status == TaskStatus.ASSIGNED
                assert assigned.assigned_to == "test-agent-001"
                assert assigned.assigned_at is not None
                
            finally:
                await client.delete_database("test_db")
    
    async def test_task_with_dependencies(self):
        """Test task dependency handling."""
        async with CouchDBClient() as client:
            await client.create_database("test_db")
            
            try:
                task_queue = TaskQueue(client)
                
                # Create dependency task
                dep_task = await task_queue.create_task(
                    task_definition={"action": "dependency"}
                )
                
                # Create task with dependency
                task = await task_queue.create_task(
                    task_definition={"action": "main"},
                    dependencies=[dep_task.task_id]
                )
                
                # Try to assign task (should fail due to pending dependency)
                assigned = await task_queue.assign_task(
                    task.task_id,
                    "test-agent-001"
                )
                
                assert assigned is None  # Should not assign
                
                # Complete dependency
                await task_queue.complete_task(
                    dep_task.task_id,
                    result="done"
                )
                
                # Now assignment should succeed
                assigned = await task_queue.assign_task(
                    task.task_id,
                    "test-agent-001"
                )
                
                assert assigned is not None
                assert assigned.status == TaskStatus.ASSIGNED
                
            finally:
                await client.delete_database("test_db")
    
    async def test_complete_task(self):
        """Test task completion."""
        async with CouchDBClient() as client:
            await client.create_database("test_db")
            
            try:
                task_queue = TaskQueue(client)
                
                # Create and assign task
                task = await task_queue.create_task(
                    task_definition={"action": "test"}
                )
                await task_queue.assign_task(task.task_id, "test-agent-001")
                
                # Complete task
                completed = await task_queue.complete_task(
                    task.task_id,
                    result={"status": "success"}
                )
                
                assert completed is not None
                assert completed.status == TaskStatus.COMPLETED
                assert completed.result["status"] == "success"
                
            finally:
                await client.delete_database("test_db")
    
    async def test_get_task_stats(self):
        """Test task statistics."""
        async with CouchDBClient() as client:
            await client.create_database("test_db")
            
            try:
                # Initialize design documents
                from src.database.design_docs import initialize_design_documents
                await initialize_design_documents(client)
                
                task_queue = TaskQueue(client)
                
                # Create tasks
                for i in range(5):
                    await task_queue.create_task(
                        task_definition={"action": f"test-{i}"}
                    )
                
                # Get stats
                stats = await task_queue.get_task_stats()
                
                assert "pending" in stats or "PENDING" in str(stats)
                
            finally:
                await client.delete_database("test_db")
