"""
CouchDB design documents and views.
"""
from typing import Dict, Any


DESIGN_DOCS = {
    "agents": {
        "_id": "_design/agents",
        "language": "javascript",
        "views": {
            "by_region": {
                "map": """
function(doc) {
    if (doc.type === "agent" && doc.status === "active") {
        emit(doc.region, {
            agent_id: doc.agent_id,
            agent_type: doc.agent_type,
            capabilities: doc.capabilities,
            heartbeat: doc.heartbeat_timestamp,
            current_tasks: doc.current_tasks ? doc.current_tasks.length : 0
        });
    }
}
                """,
                "reduce": "_count"
            },
            "by_status": {
                "map": """
function(doc) {
    if (doc.type === "agent") {
        emit([doc.status, doc.region], {
            agent_id: doc.agent_id,
            heartbeat: doc.heartbeat_timestamp
        });
    }
}
                """
            },
            "by_capability": {
                "map": """
function(doc) {
    if (doc.type === "agent" && doc.status === "active" && doc.capabilities) {
        doc.capabilities.forEach(function(capability) {
            emit([capability, doc.region], {
                agent_id: doc.agent_id,
                agent_type: doc.agent_type,
                current_load: doc.current_tasks ? doc.current_tasks.length : 0,
                max_tasks: doc.metadata ? doc.metadata.max_concurrent_tasks : 5
            });
        });
    }
}
                """
            },
            "stale_heartbeats": {
                "map": """
function(doc) {
    if (doc.type === "agent" && doc.status === "active") {
        var now = new Date().getTime();
        var heartbeat = new Date(doc.heartbeat_timestamp).getTime();
        var age_seconds = (now - heartbeat) / 1000;
        
        if (age_seconds > 90) {  // Failure threshold
            emit(age_seconds, {
                agent_id: doc.agent_id,
                last_heartbeat: doc.heartbeat_timestamp
            });
        }
    }
}
                """
            }
        }
    },
    
    "tasks": {
        "_id": "_design/tasks",
        "language": "javascript",
        "views": {
            "pending_by_priority": {
                "map": """
function(doc) {
    if (doc.type === "task" && doc.status === "pending") {
        emit([doc.priority, doc.created_at], {
            task_id: doc.task_id,
            task_definition: doc.task_definition,
            dependencies: doc.dependencies
        });
    }
}
                """
            },
            "by_status": {
                "map": """
function(doc) {
    if (doc.type === "task") {
        emit([doc.status, doc.created_at], {
            task_id: doc.task_id,
            assigned_to: doc.assigned_to,
            priority: doc.priority
        });
    }
}
                """,
                "reduce": "_count"
            },
            "by_agent": {
                "map": """
function(doc) {
    if (doc.type === "task" && doc.assigned_to) {
        emit([doc.assigned_to, doc.status], {
            task_id: doc.task_id,
            assigned_at: doc.assigned_at,
            priority: doc.priority
        });
    }
}
                """,
                "reduce": "_count"
            },
            "dependencies": {
                "map": """
function(doc) {
    if (doc.type === "task" && doc.dependencies && doc.dependencies.length > 0) {
        doc.dependencies.forEach(function(dep) {
            emit([dep, doc.task_id], {
                task_id: doc.task_id,
                status: doc.status
            });
        });
    }
}
                """
            },
            "failed_tasks": {
                "map": """
function(doc) {
    if (doc.type === "task" && doc.status === "failed") {
        emit(doc.updated_at, {
            task_id: doc.task_id,
            error: doc.error,
            retry_count: doc.retry_count,
            max_retries: doc.max_retries
        });
    }
}
                """
            },
            "ready_to_execute": {
                "map": """
function(doc) {
    if (doc.type === "task" && doc.status === "pending" && 
        (!doc.dependencies || doc.dependencies.length === 0)) {
        emit([doc.priority, doc.created_at], {
            task_id: doc.task_id,
            task_definition: doc.task_definition
        });
    }
}
                """
            }
        }
    },
    
    "knowledge": {
        "_id": "_design/knowledge",
        "language": "javascript",
        "views": {
            "by_topic": {
                "map": """
function(doc) {
    if (doc.type === "knowledge") {
        emit(doc.topic, {
            topic: doc.topic,
            version: doc.version,
            contributors_count: doc.contributors ? doc.contributors.length : 0,
            updated_at: doc.updated_at
        });
    }
}
                """
            },
            "by_contributor": {
                "map": """
function(doc) {
    if (doc.type === "knowledge" && doc.contributors) {
        doc.contributors.forEach(function(contributor) {
            emit(contributor.agent_id, {
                topic: doc.topic,
                contribution_type: contributor.contribution_type,
                timestamp: contributor.contribution_timestamp
            });
        });
    }
}
                """
            },
            "recent_updates": {
                "map": """
function(doc) {
    if (doc.type === "knowledge") {
        emit(doc.updated_at, {
            topic: doc.topic,
            version: doc.version
        });
    }
}
                """
            }
        }
    },
    
    "agent_states": {
        "_id": "_design/agent_states",
        "language": "javascript",
        "views": {
            "by_agent": {
                "map": """
function(doc) {
    if (doc.type === "agent_state") {
        emit([doc.agent_id, doc.timestamp], {
            session_id: doc.session_id,
            vector_clock: doc.vector_clock
        });
    }
}
                """
            },
            "latest_by_agent": {
                "map": """
function(doc) {
    if (doc.type === "agent_state") {
        emit(doc.agent_id, {
            session_id: doc.session_id,
            timestamp: doc.timestamp,
            state_snapshot: doc.state_snapshot
        });
    }
}
                """,
                "reduce": """
function(keys, values) {
    return values.reduce(function(latest, current) {
        return new Date(current.timestamp) > new Date(latest.timestamp) ? 
            current : latest;
    });
}
                """
            }
        }
    }
}


async def initialize_design_documents(client):
    """Initialize all design documents in the database."""
    from src.database.client import CouchDBClient
    
    for doc_name, design_doc in DESIGN_DOCS.items():
        try:
            # Check if design doc exists
            existing = await client.get_document(design_doc["_id"])
            
            if existing:
                # Update with new revision
                design_doc["_rev"] = existing["_rev"]
            
            # Save design document
            await client.save_document(design_doc)
            print(f"Initialized design document: {design_doc['_id']}")
            
        except Exception as e:
            print(f"Error initializing design document {doc_name}: {e}")
            raise
