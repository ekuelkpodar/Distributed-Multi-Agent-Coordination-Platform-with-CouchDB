#!/usr/bin/env python3
"""
Initialize CouchDB database with design documents and indexes.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.client import CouchDBClient
from src.database.design_docs import initialize_design_documents, DESIGN_DOCS
from src.core.config import settings


async def initialize_database():
    """Initialize CouchDB database."""
    print("Initializing CouchDB database...")
    print(f"URL: {settings.couchdb_url}")
    print(f"Database: {settings.couchdb_database}")
    
    async with CouchDBClient() as client:
        # Create main database
        print(f"\nCreating database: {settings.couchdb_database}")
        await client.create_database(settings.couchdb_database)
        
        # Initialize design documents
        print("\nInitializing design documents...")
        await initialize_design_documents(client)
        
        # Create indexes for Mango queries
        print("\nCreating indexes...")
        
        # Agent indexes
        await client.create_index(
            index_fields=["type", "status", "region"],
            index_name="agent-status-region-index"
        )
        
        await client.create_index(
            index_fields=["type", "agent_type"],
            index_name="agent-type-index"
        )
        
        # Task indexes
        await client.create_index(
            index_fields=["type", "status", "priority"],
            index_name="task-status-priority-index"
        )
        
        await client.create_index(
            index_fields=["type", "assigned_to"],
            index_name="task-assigned-index"
        )
        
        # Knowledge indexes
        await client.create_index(
            index_fields=["type", "topic"],
            index_name="knowledge-topic-index"
        )
        
        print("\nDatabase initialization completed successfully!")
        print("\nCreated design documents:")
        for doc_name in DESIGN_DOCS.keys():
            print(f"  - {doc_name}")


async def setup_replication():
    """Set up replication between CouchDB nodes."""
    print("\n\nSetting up replication...")
    
    nodes = [
        {"url": "http://localhost:5984", "name": "node1"},
        {"url": "http://localhost:5985", "name": "node2"},
        {"url": "http://localhost:5986", "name": "node3"}
    ]
    
    # Set up bidirectional replication between all nodes
    for i, source in enumerate(nodes):
        for target in nodes[i+1:]:
            print(f"\nSetting up replication: {source['name']} <-> {target['name']}")
            
            # Create replication from source to target
            await create_replication(
                source["url"],
                target["url"],
                settings.couchdb_database
            )
            
            # Create replication from target to source
            await create_replication(
                target["url"],
                source["url"],
                settings.couchdb_database
            )
    
    print("\nReplication setup completed!")


async def create_replication(source_url: str, target_url: str, database: str):
    """Create a continuous replication."""
    async with CouchDBClient(url=source_url) as client:
        replication_doc = {
            "source": f"{source_url}/{database}",
            "target": f"{target_url}/{database}",
            "continuous": True,
            "create_target": True
        }
        
        try:
            response = await client.session.post(
                f"{source_url}/_replicate",
                json=replication_doc
            )
            
            if response.status in (200, 202):
                result = await response.json()
                print(f"  ✓ Replication created: {result.get('ok', False)}")
            else:
                error = await response.text()
                print(f"  ✗ Replication failed: {error}")
        except Exception as e:
            print(f"  ✗ Error: {e}")


async def verify_setup():
    """Verify database setup."""
    print("\n\nVerifying setup...")
    
    async with CouchDBClient() as client:
        # Check database exists
        url = f"{client.url}/{settings.couchdb_database}"
        async with client.session.get(url) as response:
            if response.status == 200:
                db_info = await response.json()
                print(f"✓ Database exists: {db_info.get('db_name')}")
                print(f"  Documents: {db_info.get('doc_count')}")
                print(f"  Update sequence: {db_info.get('update_seq')}")
            else:
                print("✗ Database not found")
                return False
        
        # Check design documents
        for doc_name in DESIGN_DOCS.keys():
            doc = await client.get_document(f"_design/{doc_name}")
            if doc:
                print(f"✓ Design document exists: {doc_name}")
            else:
                print(f"✗ Design document missing: {doc_name}")
    
    print("\nSetup verification completed!")
    return True


async def main():
    """Main initialization function."""
    try:
        # Initialize database
        await initialize_database()
        
        # Set up replication (optional)
        if input("\nSet up replication between nodes? (y/n): ").lower() == 'y':
            await setup_replication()
        
        # Verify setup
        await verify_setup()
        
        print("\n✓ All done! Your CouchDB cluster is ready for distributed agents.")
        
    except Exception as e:
        print(f"\n✗ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
