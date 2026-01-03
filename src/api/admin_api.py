"""
Admin API for distributed agent platform control.
Provides endpoints for replication management, data generation, and monitoring.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from src.database.client import CouchDBClient
from src.core.models import Agent, Task, AgentStatus, TaskStatus
import sys
import os

# Add scripts to path for mock data generation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../scripts'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus Metrics
requests_total = Counter('admin_api_requests_total', 'Total API requests', ['endpoint', 'method'])
replication_status = Gauge('couchdb_replication_status', 'Replication status', ['source', 'target'])
node_document_count = Gauge('couchdb_node_documents', 'Document count per node', ['node', 'type'])
data_generation_total = Counter('data_generation_total', 'Total data generation runs')
data_generation_duration = Histogram('data_generation_duration_seconds', 'Data generation duration')
active_replications = Gauge('couchdb_active_replications', 'Number of active replications')

# Global state
app_state = {
    'openrouter_key': None,
    'auto_generate_enabled': False,
    'generation_interval': 300,  # 5 minutes default
    'last_generation': None
}

# Pydantic models
class ReplicationConfig(BaseModel):
    source_node: str
    target_node: str
    enable: bool = True

class NodeInfo(BaseModel):
    url: str
    name: str
    status: str
    document_count: int
    documents_by_type: Dict[str, int]

class GenerationConfig(BaseModel):
    openrouter_key: Optional[str] = None
    agents: int = 10
    tasks: int = 30
    knowledge: int = 15
    states: int = 20
    decisions: int = 5

class AutoGenerationConfig(BaseModel):
    enabled: bool
    interval_minutes: int
    openrouter_key: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting Admin API...")
    # Start auto-generation task
    asyncio.create_task(auto_generation_task())
    yield
    logger.info("Shutting down Admin API...")

app = FastAPI(
    title="Distributed Agent Platform Admin",
    description="Admin interface for managing distributed agent coordination",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request counting
@app.middleware("http")
async def count_requests(request: Request, call_next):
    requests_total.labels(endpoint=request.url.path, method=request.method).inc()
    response = await call_next(request)
    return response


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve admin dashboard."""
    html_path = os.path.join(os.path.dirname(__file__), 'static', 'admin.html')
    if os.path.exists(html_path):
        with open(html_path, 'r') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Admin Dashboard</h1><p>Frontend not found. Building...</p>")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/nodes")
async def get_nodes() -> List[NodeInfo]:
    """Get information about all CouchDB nodes."""
    nodes = [
        {"url": "http://localhost:5984", "name": "node1"},
        {"url": "http://localhost:5985", "name": "node2"},
        {"url": "http://localhost:5986", "name": "node3"}
    ]

    result = []
    for node_config in nodes:
        try:
            client = CouchDBClient(url=node_config["url"])
            async with client:
                # Get all documents
                docs_response = await client.query_view("_all_docs", include_docs=True)

                total_count = len(docs_response.get('rows', []))

                # Count by type
                type_counts = {}
                for row in docs_response.get('rows', []):
                    doc = row.get('doc', {})
                    doc_type = doc.get('type', 'other')
                    type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

                # Update Prometheus metrics
                for doc_type, count in type_counts.items():
                    node_document_count.labels(node=node_config["name"], type=doc_type).set(count)

                result.append(NodeInfo(
                    url=node_config["url"],
                    name=node_config["name"],
                    status="healthy",
                    document_count=total_count,
                    documents_by_type=type_counts
                ))
        except Exception as e:
            logger.error(f"Error getting node info for {node_config['name']}: {e}")
            result.append(NodeInfo(
                url=node_config["url"],
                name=node_config["name"],
                status="error",
                document_count=0,
                documents_by_type={}
            ))

    return result


@app.get("/api/replications")
async def get_replications():
    """Get current replication status."""
    try:
        client = CouchDBClient(url="http://localhost:5984")
        async with client:
            # Get replication documents
            response = await client.query_view("_replicator/_all_docs", include_docs=True)

            replications = []
            active_count = 0
            for row in response.get('rows', []):
                doc = row.get('doc', {})
                if doc.get('_id', '').startswith('_design'):
                    continue

                source = doc.get('source', '')
                target = doc.get('target', '')
                continuous = doc.get('continuous', False)

                # Check replication status
                status = "active" if continuous else "completed"
                if status == "active":
                    active_count += 1
                    replication_status.labels(source=source, target=target).set(1)
                else:
                    replication_status.labels(source=source, target=target).set(0)

                replications.append({
                    "id": doc.get('_id'),
                    "source": source,
                    "target": target,
                    "continuous": continuous,
                    "status": status
                })

            active_replications.set(active_count)
            return replications
    except Exception as e:
        logger.error(f"Error getting replications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/replication/control")
async def control_replication(config: ReplicationConfig):
    """Enable or disable replication between nodes."""
    try:
        client = CouchDBClient(url="http://localhost:5984")
        async with client:
            repl_id = f"replication_{config.source_node}_to_{config.target_node}"

            if config.enable:
                # Create/update replication
                repl_doc = {
                    "_id": repl_id,
                    "source": config.source_node,
                    "target": config.target_node,
                    "continuous": True,
                    "create_target": False
                }

                # Check if exists
                try:
                    existing = await client.get_document(repl_id, db_name="_replicator")
                    repl_doc["_rev"] = existing.get("_rev")
                except:
                    pass

                await client.save_document(repl_doc, db_name="_replicator")
                replication_status.labels(source=config.source_node, target=config.target_node).set(1)

                return {"status": "enabled", "replication_id": repl_id}
            else:
                # Disable replication
                try:
                    doc = await client.get_document(repl_id, db_name="_replicator")
                    await client.delete_document(repl_id, doc["_rev"], db_name="_replicator")
                    replication_status.labels(source=config.source_node, target=config.target_node).set(0)
                    return {"status": "disabled", "replication_id": repl_id}
                except:
                    return {"status": "not_found", "replication_id": repl_id}

    except Exception as e:
        logger.error(f"Error controlling replication: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/data/generate")
async def generate_data(config: GenerationConfig, background_tasks: BackgroundTasks):
    """Generate mock data."""
    if config.openrouter_key:
        app_state['openrouter_key'] = config.openrouter_key

    background_tasks.add_task(
        run_data_generation,
        config.agents,
        config.tasks,
        config.knowledge,
        config.states,
        config.decisions,
        app_state.get('openrouter_key')
    )

    return {
        "status": "started",
        "message": "Data generation started in background",
        "config": config.dict()
    }


@app.post("/api/data/auto-generate")
async def configure_auto_generation(config: AutoGenerationConfig):
    """Configure automatic data generation."""
    app_state['auto_generate_enabled'] = config.enabled
    app_state['generation_interval'] = config.interval_minutes * 60

    if config.openrouter_key:
        app_state['openrouter_key'] = config.openrouter_key

    return {
        "status": "configured",
        "enabled": config.enabled,
        "interval_minutes": config.interval_minutes,
        "next_run": (datetime.utcnow() + timedelta(seconds=app_state['generation_interval'])).isoformat() if config.enabled else None
    }


@app.get("/api/data/auto-generate/status")
async def get_auto_generation_status():
    """Get auto-generation status."""
    return {
        "enabled": app_state['auto_generate_enabled'],
        "interval_seconds": app_state['generation_interval'],
        "interval_minutes": app_state['generation_interval'] / 60,
        "last_generation": app_state['last_generation'],
        "next_generation": (datetime.fromisoformat(app_state['last_generation']) +
                          timedelta(seconds=app_state['generation_interval'])).isoformat()
                          if app_state['last_generation'] else None
    }


@app.get("/api/stats")
async def get_stats():
    """Get platform statistics."""
    try:
        client = CouchDBClient()
        async with client:
            # Get all documents
            all_docs = await client.query_view("_all_docs", include_docs=True)

            # Count by type and status
            stats = {
                "total_documents": 0,
                "agents": {"total": 0, "active": 0, "inactive": 0},
                "tasks": {"total": 0, "pending": 0, "in_progress": 0, "completed": 0, "failed": 0},
                "knowledge": 0,
                "agent_states": 0,
                "decisions": 0
            }

            for row in all_docs.get('rows', []):
                doc = row.get('doc', {})
                doc_type = doc.get('type')

                if not doc_type or doc.get('_id', '').startswith('_design'):
                    continue

                stats["total_documents"] += 1

                if doc_type == 'agent':
                    stats["agents"]["total"] += 1
                    status = doc.get('status', '')
                    if status == 'active':
                        stats["agents"]["active"] += 1
                    else:
                        stats["agents"]["inactive"] += 1

                elif doc_type == 'task':
                    stats["tasks"]["total"] += 1
                    status = doc.get('status', '')
                    stats["tasks"][status] = stats["tasks"].get(status, 0) + 1

                elif doc_type == 'knowledge':
                    stats["knowledge"] += 1
                elif doc_type == 'agent_state':
                    stats["agent_states"] += 1
                elif doc_type == 'consensus_decision':
                    stats["decisions"] += 1

            return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def run_data_generation(agents: int, tasks: int, knowledge: int, states: int, decisions: int, api_key: Optional[str]):
    """Run data generation in background."""
    import time
    start_time = time.time()

    try:
        logger.info(f"Starting data generation: {agents} agents, {tasks} tasks, {knowledge} knowledge docs")

        # Set environment variable if key provided
        if api_key:
            os.environ['OPENROUTER_API_KEY'] = api_key

        # Import and run generation
        from generate_mock_data import generate_all_mock_data

        await generate_all_mock_data(
            num_agents=agents,
            num_tasks=tasks,
            num_knowledge=knowledge,
            num_states=states,
            num_decisions=decisions
        )

        duration = time.time() - start_time
        data_generation_total.inc()
        data_generation_duration.observe(duration)

        app_state['last_generation'] = datetime.utcnow().isoformat()

        logger.info(f"Data generation completed in {duration:.2f}s")

    except Exception as e:
        logger.error(f"Error in data generation: {e}")
        raise


async def auto_generation_task():
    """Background task for automatic data generation."""
    while True:
        try:
            if app_state['auto_generate_enabled']:
                interval = app_state['generation_interval']
                logger.info(f"Auto-generation enabled, waiting {interval}s")

                await asyncio.sleep(interval)

                if app_state['auto_generate_enabled']:  # Check again after sleep
                    logger.info("Running scheduled data generation")
                    await run_data_generation(
                        agents=5,
                        tasks=10,
                        knowledge=5,
                        states=5,
                        decisions=2,
                        api_key=app_state.get('openrouter_key')
                    )
            else:
                await asyncio.sleep(10)  # Check every 10 seconds

        except Exception as e:
            logger.error(f"Error in auto-generation task: {e}")
            await asyncio.sleep(60)  # Wait a minute on error


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the admin API server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
