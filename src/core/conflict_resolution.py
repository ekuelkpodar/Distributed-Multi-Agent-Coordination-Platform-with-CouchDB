"""
Conflict resolution strategies for distributed documents.
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.core.models import VectorClock, Knowledge

logger = logging.getLogger(__name__)


class ConflictResolver:
    """Base class for conflict resolution strategies."""
    
    def resolve(self, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolve conflicts and return winning document.
        
        Args:
            conflicts: List of conflicting document versions
            
        Returns:
            Resolved document
        """
        raise NotImplementedError


class VectorClockResolver(ConflictResolver):
    """
    Resolve conflicts using vector clock comparison.
    Selects document with most recent causality chain.
    """
    
    def resolve(self, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolve conflicts using vector clock comparison.
        
        Args:
            conflicts: List of conflicting document versions
            
        Returns:
            Document with dominant vector clock
        """
        if not conflicts:
            raise ValueError("No conflicts to resolve")
        
        if len(conflicts) == 1:
            return conflicts[0]
        
        # Compare vector clocks
        def get_vector_clock(doc: Dict[str, Any]) -> VectorClock:
            vc_data = doc.get("vector_clock", {})
            if isinstance(vc_data, dict) and "clock" in vc_data:
                return VectorClock(**vc_data)
            return VectorClock(clock=vc_data if isinstance(vc_data, dict) else {})
        
        winner = conflicts[0]
        winner_vc = get_vector_clock(winner)
        
        for doc in conflicts[1:]:
            doc_vc = get_vector_clock(doc)
            
            if doc_vc.happens_before(winner_vc):
                # winner is more recent
                continue
            elif winner_vc.happens_before(doc_vc):
                # doc is more recent
                winner = doc
                winner_vc = doc_vc
            else:
                # Concurrent - fall back to timestamp
                winner_time = datetime.fromisoformat(winner.get("timestamp", winner.get("updated_at", "1970-01-01")))
                doc_time = datetime.fromisoformat(doc.get("timestamp", doc.get("updated_at", "1970-01-01")))
                
                if doc_time > winner_time:
                    winner = doc
                    winner_vc = doc_vc
        
        logger.info(f"Resolved conflict using vector clock: {winner.get('_id')}")
        return winner


class LastWriteWinsResolver(ConflictResolver):
    """
    Simple last-write-wins conflict resolution.
    Selects document with most recent timestamp.
    """
    
    def resolve(self, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolve conflicts using timestamp.
        
        Args:
            conflicts: List of conflicting document versions
            
        Returns:
            Most recently updated document
        """
        if not conflicts:
            raise ValueError("No conflicts to resolve")
        
        def get_timestamp(doc: Dict[str, Any]) -> datetime:
            timestamp_str = doc.get("updated_at") or doc.get("timestamp") or "1970-01-01"
            try:
                return datetime.fromisoformat(timestamp_str)
            except:
                return datetime.min
        
        winner = max(conflicts, key=get_timestamp)
        logger.info(f"Resolved conflict using last-write-wins: {winner.get('_id')}")
        return winner


class MergeResolver(ConflictResolver):
    """
    Merge conflicts by combining non-conflicting changes.
    Useful for knowledge documents and collaborative edits.
    """
    
    def resolve(self, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge conflicting documents.
        
        Args:
            conflicts: List of conflicting document versions
            
        Returns:
            Merged document
        """
        if not conflicts:
            raise ValueError("No conflicts to resolve")
        
        if len(conflicts) == 1:
            return conflicts[0]
        
        # Start with most recent as base
        base = LastWriteWinsResolver().resolve(conflicts)
        merged = base.copy()
        
        # Merge contributors from all versions
        if "contributors" in base:
            all_contributors = []
            seen = set()
            
            for doc in conflicts:
                for contributor in doc.get("contributors", []):
                    # Create unique key from agent_id and timestamp
                    key = (contributor["agent_id"], contributor["contribution_timestamp"])
                    if key not in seen:
                        all_contributors.append(contributor)
                        seen.add(key)
            
            merged["contributors"] = sorted(
                all_contributors,
                key=lambda c: c["contribution_timestamp"]
            )
        
        # Merge list fields (union)
        list_fields = ["key_findings", "references", "tags"]
        if "content" in merged and isinstance(merged["content"], dict):
            for field in list_fields:
                if field in merged["content"]:
                    merged_items = set()
                    
                    for doc in conflicts:
                        if "content" in doc and field in doc["content"]:
                            items = doc["content"][field]
                            if isinstance(items, list):
                                merged_items.update(items)
                    
                    merged["content"][field] = list(merged_items)
        
        # Increment version
        merged["version"] = max(doc.get("version", 1) for doc in conflicts) + 1
        merged["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Resolved conflict using merge: {merged.get('_id')}")
        return merged


class ConflictManager:
    """
    Manages conflict detection and resolution for CouchDB documents.
    """
    
    def __init__(self, client):
        self.client = client
        self.resolvers = {
            "vector_clock": VectorClockResolver(),
            "last_write_wins": LastWriteWinsResolver(),
            "merge": MergeResolver()
        }
    
    async def detect_and_resolve_conflicts(
        self,
        doc_id: str,
        strategy: str = "vector_clock"
    ) -> Optional[Dict[str, Any]]:
        """
        Detect and resolve conflicts for a document.
        
        Args:
            doc_id: Document ID
            strategy: Resolution strategy to use
            
        Returns:
            Resolved document or None
        """
        # Get document with conflicts
        doc = await self.client.get_document(doc_id, include_conflicts=True)
        
        if not doc:
            return None
        
        # Check if document has conflicts
        if "_conflicts" not in doc or not doc["_conflicts"]:
            return doc
        
        logger.warning(f"Document {doc_id} has {len(doc['_conflicts'])} conflicts")
        
        # Fetch all conflicting revisions
        conflicts = [doc]  # Current revision
        
        for conflict_rev in doc["_conflicts"]:
            try:
                conflict_doc = await self.client.get_document(
                    doc_id,
                    include_conflicts=False
                )
                if conflict_doc:
                    conflicts.append(conflict_doc)
            except Exception as e:
                logger.error(f"Error fetching conflict revision: {e}")
        
        # Resolve conflicts
        resolver = self.resolvers.get(strategy)
        if not resolver:
            logger.error(f"Unknown resolution strategy: {strategy}")
            return doc
        
        resolved = resolver.resolve(conflicts)
        
        # Save resolved document
        resolved["_id"] = doc_id
        resolved["_rev"] = doc["_rev"]
        
        try:
            await self.client.save_document(resolved)
            
            # Delete conflicting revisions
            for conflict in conflicts[1:]:  # Skip the winner
                try:
                    await self.client.delete_document(
                        doc_id,
                        conflict["_rev"]
                    )
                except Exception as e:
                    logger.error(f"Error deleting conflict revision: {e}")
            
            logger.info(f"Successfully resolved conflicts for {doc_id}")
            return resolved
            
        except Exception as e:
            logger.error(f"Error saving resolved document: {e}")
            return doc
    
    async def merge_knowledge_documents(
        self,
        conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Specialized merge for knowledge documents.
        
        Args:
            conflicts: Conflicting knowledge documents
            
        Returns:
            Merged knowledge document
        """
        resolver = MergeResolver()
        return resolver.resolve(conflicts)
