"""
CouchDB client with connection pooling and async support.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, AsyncIterator
from datetime import datetime
from contextlib import asynccontextmanager

import aiohttp
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings

logger = logging.getLogger(__name__)


class CouchDBClient:
    """Async CouchDB client with connection pooling."""
    
    def __init__(
        self,
        url: str = None,
        username: str = None,
        password: str = None,
        database: str = None,
        max_connections: int = 100
    ):
        self.url = url or settings.couchdb_url
        self.username = username or settings.couchdb_user
        self.password = password or settings.couchdb_password
        self.database = database or settings.couchdb_database
        self.max_connections = max_connections
        
        self.auth = aiohttp.BasicAuth(self.username, self.password)
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def connect(self):
        """Initialize connection pool."""
        if self._session is None:
            self._connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                limit_per_host=self.max_connections
            )
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                auth=self.auth
            )
            logger.info(f"Connected to CouchDB at {self.url}")
    
    async def close(self):
        """Close connection pool."""
        if self._session:
            await self._session.close()
            self._session = None
            logger.info("Closed CouchDB connection")
    
    @property
    def session(self) -> aiohttp.ClientSession:
        """Get current session."""
        if self._session is None:
            raise RuntimeError("Client not connected. Use async with or call connect()")
        return self._session
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def create_database(self, db_name: str = None) -> bool:
        """Create database if it doesn't exist."""
        db_name = db_name or self.database
        url = f"{self.url}/{db_name}"
        
        try:
            async with self.session.put(url) as response:
                if response.status == 201:
                    logger.info(f"Created database: {db_name}")
                    return True
                elif response.status == 412:
                    logger.info(f"Database already exists: {db_name}")
                    return True
                else:
                    error = await response.text()
                    logger.error(f"Failed to create database: {error}")
                    return False
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise
    
    async def delete_database(self, db_name: str = None) -> bool:
        """Delete database."""
        db_name = db_name or self.database
        url = f"{self.url}/{db_name}"
        
        async with self.session.delete(url) as response:
            return response.status == 200
    
    async def save_document(
        self,
        document: Dict[str, Any],
        db_name: str = None
    ) -> Dict[str, Any]:
        """
        Save document to database.
        Handles both new documents and updates.
        """
        db_name = db_name or self.database
        doc_id = document.get("_id")
        
        if doc_id:
            url = f"{self.url}/{db_name}/{doc_id}"
            method = self.session.put
        else:
            url = f"{self.url}/{db_name}"
            method = self.session.post
        
        async with method(url, json=document) as response:
            if response.status in (201, 202):
                result = await response.json()
                document["_id"] = result["id"]
                document["_rev"] = result["rev"]
                return document
            else:
                error = await response.text()
                raise Exception(f"Failed to save document: {error}")
    
    async def get_document(
        self,
        doc_id: str,
        db_name: str = None,
        include_conflicts: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        db_name = db_name or self.database
        url = f"{self.url}/{db_name}/{doc_id}"
        
        params = {}
        if include_conflicts:
            params["conflicts"] = "true"
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 404:
                return None
            else:
                error = await response.text()
                raise Exception(f"Failed to get document: {error}")
    
    async def delete_document(
        self,
        doc_id: str,
        rev: str,
        db_name: str = None
    ) -> bool:
        """Delete document."""
        db_name = db_name or self.database
        url = f"{self.url}/{db_name}/{doc_id}"
        params = {"rev": rev}
        
        async with self.session.delete(url, params=params) as response:
            return response.status == 200
    
    async def bulk_save(
        self,
        documents: List[Dict[str, Any]],
        db_name: str = None
    ) -> List[Dict[str, Any]]:
        """Save multiple documents in a single request."""
        db_name = db_name or self.database
        url = f"{self.url}/{db_name}/_bulk_docs"
        
        payload = {"docs": documents}
        
        async with self.session.post(url, json=payload) as response:
            if response.status in (201, 202):
                results = await response.json()
                
                # Update documents with new revisions
                for doc, result in zip(documents, results):
                    if "rev" in result:
                        doc["_rev"] = result["rev"]
                        if "id" in result:
                            doc["_id"] = result["id"]
                
                return documents
            else:
                error = await response.text()
                raise Exception(f"Failed to bulk save: {error}")
    
    async def query_view(
        self,
        design_doc: str,
        view_name: str,
        db_name: str = None,
        **params
    ) -> Dict[str, Any]:
        """Query a view."""
        db_name = db_name or self.database
        url = f"{self.url}/{db_name}/_design/{design_doc}/_view/{view_name}"
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                raise Exception(f"Failed to query view: {error}")
    
    async def changes_feed(
        self,
        db_name: str = None,
        since: str = "now",
        feed: str = "continuous",
        include_docs: bool = True,
        filter_doc: Optional[str] = None,
        heartbeat: int = 60000
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream changes from database.
        Yields change documents as they occur.
        """
        db_name = db_name or self.database
        url = f"{self.url}/{db_name}/_changes"
        
        params = {
            "since": since,
            "feed": feed,
            "include_docs": str(include_docs).lower(),
            "heartbeat": heartbeat
        }
        
        if filter_doc:
            params["filter"] = filter_doc
        
        async with self.session.get(url, params=params) as response:
            async for line in response.content:
                if line:
                    try:
                        change = line.decode('utf-8').strip()
                        if change:
                            import json
                            yield json.loads(change)
                    except json.JSONDecodeError:
                        continue
    
    async def find(
        self,
        selector: Dict[str, Any],
        db_name: str = None,
        limit: int = 25,
        skip: int = 0,
        sort: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """Query using Mango query language."""
        db_name = db_name or self.database
        url = f"{self.url}/{db_name}/_find"
        
        query = {
            "selector": selector,
            "limit": limit,
            "skip": skip
        }
        
        if sort:
            query["sort"] = sort
        
        async with self.session.post(url, json=query) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("docs", [])
            else:
                error = await response.text()
                raise Exception(f"Failed to execute find query: {error}")
    
    async def create_index(
        self,
        index_fields: List[str],
        index_name: str = None,
        db_name: str = None
    ) -> Dict[str, Any]:
        """Create an index for Mango queries."""
        db_name = db_name or self.database
        url = f"{self.url}/{db_name}/_index"
        
        payload = {
            "index": {
                "fields": index_fields
            },
            "type": "json"
        }
        
        if index_name:
            payload["name"] = index_name
        
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                raise Exception(f"Failed to create index: {error}")


class ConnectionPool:
    """Connection pool manager for multiple CouchDB clients."""
    
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self._pool: asyncio.Queue[CouchDBClient] = asyncio.Queue(maxsize=max_size)
        self._current_size = 0
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Pre-populate connection pool."""
        for _ in range(self.max_size):
            client = CouchDBClient()
            await client.connect()
            await self._pool.put(client)
            self._current_size += 1
    
    @asynccontextmanager
    async def get_client(self) -> AsyncIterator[CouchDBClient]:
        """Get client from pool."""
        async with self._lock:
            if self._pool.empty() and self._current_size < self.max_size:
                client = CouchDBClient()
                await client.connect()
                self._current_size += 1
            else:
                client = await self._pool.get()
        
        try:
            yield client
        finally:
            await self._pool.put(client)
    
    async def close_all(self):
        """Close all connections in pool."""
        while not self._pool.empty():
            client = await self._pool.get()
            await client.close()
        self._current_size = 0


# Global connection pool
connection_pool = ConnectionPool()
