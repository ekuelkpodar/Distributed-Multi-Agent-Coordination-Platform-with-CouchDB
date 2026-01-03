#!/usr/bin/env python3
"""
Generate realistic mock data for testing the distributed agent platform using OpenRouter.
"""
import asyncio
import sys
import os
import json
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.client import CouchDBClient
from src.core.models import (
    Agent, Task, Knowledge, AgentState, Decision,
    AgentStatus, TaskStatus, DocumentType, AgentMetadata,
    VectorClock, KnowledgeContributor
)
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_openrouter(prompt: str, model: str = "meta-llama/llama-3.1-8b-instruct:free") -> str:
    """Call OpenRouter API to generate content."""
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5984",
            "X-Title": "Distributed Agent Platform Mock Data Generator"
        }

        data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }

        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        result = response.json()
        return result['choices'][0]['message']['content'].strip()

    except Exception as e:
        logger.error(f"OpenRouter API error: {e}")
        return f"Generated content for: {prompt[:50]}..."


async def generate_mock_agents(client: CouchDBClient, count: int = 10) -> List[Agent]:
    """Generate mock agent documents."""
    logger.info(f"\nGenerating {count} mock agents...")

    agent_types = ["research", "analysis", "coordination", "data_processing", "monitoring"]
    regions = ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-south-1", "ap-northeast-1"]
    models = ["claude-sonnet-4", "gpt-4", "llama-3.1-70b", "claude-opus-4", "gpt-4-turbo"]

    agents = []
    for i in range(count):
        agent_type = random.choice(agent_types)

        # Generate capabilities using OpenRouter
        prompt = f"List 3-5 specific technical capabilities for a {agent_type} AI agent in a distributed system. Return only a comma-separated list."
        capabilities_str = call_openrouter(prompt)
        capabilities = [cap.strip() for cap in capabilities_str.split(',')[:5]]

        agent = Agent(
            agent_id=f"agent_{agent_type}_{i:03d}",
            agent_type=agent_type,
            capabilities=capabilities,
            status=random.choice([AgentStatus.ACTIVE, AgentStatus.ACTIVE, AgentStatus.ACTIVE, AgentStatus.INACTIVE]),
            region=random.choice(regions),
            heartbeat_timestamp=datetime.utcnow() - timedelta(seconds=random.randint(0, 300)),
            metadata=AgentMetadata(
                version=f"1.{random.randint(0, 5)}.{random.randint(0, 10)}",
                model=random.choice(models),
                max_concurrent_tasks=random.randint(3, 10),
                custom={
                    "deployment": random.choice(["docker", "kubernetes", "lambda"]),
                    "memory_limit": f"{random.randint(512, 4096)}MB",
                    "cpu_limit": f"{random.randint(1, 8)} cores"
                }
            ),
            current_tasks=[]
        )

        # Save to database
        doc = agent.model_dump(by_alias=True)
        await client.save_document(doc)
        agents.append(agent)

        logger.info(f"  ✓ Created agent: {agent.agent_id} ({agent.agent_type}) in {agent.region}")

    return agents


async def generate_mock_tasks(client: CouchDBClient, agents: List[Agent], count: int = 30) -> List[Task]:
    """Generate mock task documents."""
    logger.info(f"\nGenerating {count} mock tasks...")

    task_types = [
        "data_analysis", "web_scraping", "report_generation",
        "model_training", "data_transformation", "quality_check",
        "sentiment_analysis", "entity_extraction", "summarization"
    ]

    tasks = []
    for i in range(count):
        task_type = random.choice(task_types)

        # Generate task description using OpenRouter
        prompt = f"Write a one-sentence technical description for a {task_type} task in a distributed AI system."
        description = call_openrouter(prompt)

        status = random.choice([
            TaskStatus.PENDING, TaskStatus.PENDING, TaskStatus.PENDING,
            TaskStatus.ASSIGNED, TaskStatus.ASSIGNED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.COMPLETED, TaskStatus.COMPLETED,
            TaskStatus.FAILED
        ])

        assigned_to = None
        assigned_at = None
        result = None
        error = None

        if status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED, TaskStatus.FAILED]:
            assigned_to = random.choice(agents).agent_id
            assigned_at = datetime.utcnow() - timedelta(minutes=random.randint(5, 120))

        if status == TaskStatus.COMPLETED:
            result = {
                "status": "success",
                "output": f"Completed {task_type} task",
                "metrics": {
                    "execution_time_ms": random.randint(1000, 60000),
                    "items_processed": random.randint(100, 10000),
                    "accuracy": round(random.uniform(0.85, 0.99), 3)
                }
            }
        elif status == TaskStatus.FAILED:
            error = random.choice([
                "Connection timeout",
                "Resource limit exceeded",
                "Invalid input format",
                "Dependency not available"
            ])

        # Random dependencies (10% chance)
        dependencies = []
        if random.random() < 0.1 and i > 0:
            dependencies = [f"task_{random.randint(0, i-1):03d}"]

        task = Task(
            task_id=f"task_{i:03d}",
            status=status,
            priority=random.randint(1, 10),
            assigned_to=assigned_to,
            assigned_at=assigned_at,
            task_definition={
                "type": task_type,
                "description": description,
                "input_data": {
                    "source": f"data_source_{random.randint(1, 5)}",
                    "format": random.choice(["json", "csv", "parquet", "text"]),
                    "size_mb": random.randint(1, 1000)
                },
                "parameters": {
                    "timeout": random.randint(30, 300),
                    "batch_size": random.randint(100, 1000)
                }
            },
            dependencies=dependencies,
            result=result,
            error=error,
            retry_count=random.randint(0, 2) if status == TaskStatus.FAILED else 0,
            max_retries=3
        )

        # Save to database
        doc = task.model_dump(by_alias=True)
        await client.save_document(doc)
        tasks.append(task)

        logger.info(f"  ✓ Created task: {task.task_id} ({task_type}) - Status: {status.value}")

    return tasks


async def generate_mock_knowledge(client: CouchDBClient, agents: List[Agent], count: int = 15) -> List[Knowledge]:
    """Generate mock knowledge documents."""
    logger.info(f"\nGenerating {count} mock knowledge documents...")

    topics = [
        "distributed_systems", "machine_learning", "data_engineering",
        "api_design", "performance_optimization", "security_best_practices",
        "testing_strategies", "deployment_patterns", "monitoring_observability"
    ]

    knowledge_docs = []
    for i in range(count):
        topic = random.choice(topics)

        # Generate knowledge content using OpenRouter
        prompt = f"Write 2-3 key insights about {topic.replace('_', ' ')} for AI agents. Return as bullet points."
        insights = call_openrouter(prompt)

        # Generate best practices
        prompt_practices = f"List 2-3 best practices for {topic.replace('_', ' ')} in distributed systems."
        practices = call_openrouter(prompt_practices)

        # Random contributors
        num_contributors = random.randint(1, 3)
        contributors = []
        for _ in range(num_contributors):
            contributors.append(
                KnowledgeContributor(
                    agent_id=random.choice(agents).agent_id,
                    contribution_timestamp=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
                    contribution_type=random.choice(["create", "enhance", "review"])
                )
            )

        knowledge = Knowledge(
            topic=topic,
            content={
                "summary": f"Knowledge base entry for {topic.replace('_', ' ')}",
                "insights": insights,
                "best_practices": practices,
                "references": [
                    f"https://docs.example.com/{topic}/{i}",
                    f"https://research.example.com/{topic}"
                ],
                "tags": [topic, random.choice(["architecture", "implementation", "operations"])]
            },
            contributors=contributors,
            version=random.randint(1, 5)
        )

        # Save to database
        doc = knowledge.model_dump(by_alias=True)
        await client.save_document(doc)
        knowledge_docs.append(knowledge)

        logger.info(f"  ✓ Created knowledge: {topic} (v{knowledge.version}) with {len(contributors)} contributors")

    return knowledge_docs


async def generate_mock_agent_states(client: CouchDBClient, agents: List[Agent], count: int = 20) -> List[AgentState]:
    """Generate mock agent state snapshots."""
    logger.info(f"\nGenerating {count} mock agent states...")

    states = []
    for i in range(count):
        agent = random.choice(agents)

        # Create vector clock
        vc = VectorClock(
            clock={
                agent.agent_id: random.randint(1, 100),
                f"agent_{random.randint(0, 9):03d}": random.randint(1, 50)
            }
        )

        state = AgentState(
            agent_id=agent.agent_id,
            session_id=f"session_{i:03d}",
            state_snapshot={
                "memory_usage_mb": random.randint(128, 2048),
                "cpu_usage_percent": round(random.uniform(10, 90), 2),
                "active_connections": random.randint(0, 50),
                "processed_tasks": random.randint(0, 1000),
                "current_workload": random.choice(["low", "medium", "high"]),
                "last_error": None if random.random() < 0.8 else "Connection timeout"
            },
            vector_clock=vc,
            timestamp=datetime.utcnow() - timedelta(minutes=random.randint(0, 60))
        )

        # Save to database
        doc = state.model_dump(by_alias=True)
        await client.save_document(doc)
        states.append(state)

        logger.info(f"  ✓ Created state snapshot for {agent.agent_id} (session_{i:03d})")

    return states


async def generate_mock_decisions(client: CouchDBClient, agents: List[Agent], count: int = 5) -> List[Decision]:
    """Generate mock consensus decision documents."""
    logger.info(f"\nGenerating {count} mock consensus decisions...")

    decision_types = [
        "resource_allocation", "leader_election", "task_prioritization",
        "scaling_decision", "failure_recovery"
    ]

    decisions = []
    for i in range(count):
        decision_type = random.choice(decision_types)

        # Generate decision using OpenRouter
        prompt = f"Write a brief technical decision statement for {decision_type.replace('_', ' ')} in a distributed system."
        decision_text = call_openrouter(prompt)

        # Random participating agents (3-7 agents)
        num_participants = random.randint(3, min(7, len(agents)))
        participants = random.sample([a.agent_id for a in agents], num_participants)

        # Generate votes (70% consensus)
        votes = {agent_id: random.random() < 0.7 for agent_id in participants}

        decision = Decision(
            proposal_id=f"proposal_{i:03d}",
            decision={
                "type": decision_type,
                "description": decision_text,
                "outcome": "approved" if sum(votes.values()) > len(votes) * 0.5 else "rejected",
                "parameters": {
                    "quorum_size": len(participants),
                    "approval_threshold": 0.5
                }
            },
            participating_agents=participants,
            consensus_achieved_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
            votes=votes
        )

        # Save to database
        doc = decision.model_dump(by_alias=True)
        await client.save_document(doc)
        decisions.append(decision)

        outcome = decision.decision['outcome']
        logger.info(f"  ✓ Created decision: {decision_type} - {outcome} ({sum(votes.values())}/{len(votes)} votes)")

    return decisions


async def generate_all_mock_data(
    num_agents: int = 10,
    num_tasks: int = 30,
    num_knowledge: int = 15,
    num_states: int = 20,
    num_decisions: int = 5
):
    """Generate all mock data."""
    logger.info("=" * 70)
    logger.info("Mock Data Generator for Distributed Agent Platform")
    logger.info("=" * 70)

    async with CouchDBClient() as client:
        # Generate agents first (needed for other documents)
        agents = await generate_mock_agents(client, num_agents)

        # Generate tasks
        tasks = await generate_mock_tasks(client, agents, num_tasks)

        # Generate knowledge
        knowledge = await generate_mock_knowledge(client, agents, num_knowledge)

        # Generate agent states
        states = await generate_mock_agent_states(client, agents, num_states)

        # Generate decisions
        decisions = await generate_mock_decisions(client, agents, num_decisions)

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("Mock Data Generation Summary")
        logger.info("=" * 70)
        logger.info(f"  Agents created:        {len(agents)}")
        logger.info(f"  Tasks created:         {len(tasks)}")
        logger.info(f"  Knowledge docs:        {len(knowledge)}")
        logger.info(f"  Agent states:          {len(states)}")
        logger.info(f"  Consensus decisions:   {len(decisions)}")
        logger.info(f"  Total documents:       {len(agents) + len(tasks) + len(knowledge) + len(states) + len(decisions)}")
        logger.info("=" * 70)
        logger.info(f"\n✓ All mock data has been saved to CouchDB!")
        logger.info(f"  View at: http://localhost:5984/_utils/#database/agent_coordination")

        return {
            "agents": agents,
            "tasks": tasks,
            "knowledge": knowledge,
            "states": states,
            "decisions": decisions
        }


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate mock data for testing")
    parser.add_argument("--agents", type=int, default=10, help="Number of agents to create")
    parser.add_argument("--tasks", type=int, default=30, help="Number of tasks to create")
    parser.add_argument("--knowledge", type=int, default=15, help="Number of knowledge docs to create")
    parser.add_argument("--states", type=int, default=20, help="Number of agent states to create")
    parser.add_argument("--decisions", type=int, default=5, help="Number of decisions to create")

    args = parser.parse_args()

    try:
        await generate_all_mock_data(
            num_agents=args.agents,
            num_tasks=args.tasks,
            num_knowledge=args.knowledge,
            num_states=args.states,
            num_decisions=args.decisions
        )
        logger.info("\n✓ Mock data generation completed successfully!")
    except Exception as e:
        logger.error(f"\n✗ Error generating mock data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
