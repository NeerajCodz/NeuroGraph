"""Base memory layer abstract class."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class MemoryLayer(ABC):
    """Abstract base class for memory layers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Layer name identifier."""
        ...

    @abstractmethod
    async def can_read(self, user_id: UUID, tenant_id: UUID | None = None) -> bool:
        """Check if user has read access to this layer.
        
        Args:
            user_id: User requesting access
            tenant_id: Optional tenant context
            
        Returns:
            True if user can read from this layer
        """
        ...

    @abstractmethod
    async def can_write(self, user_id: UUID, tenant_id: UUID | None = None) -> bool:
        """Check if user has write access to this layer.
        
        Args:
            user_id: User requesting access
            tenant_id: Optional tenant context
            
        Returns:
            True if user can write to this layer
        """
        ...

    @abstractmethod
    async def store(
        self,
        content: str,
        user_id: UUID,
        tenant_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        """Store information in this layer.
        
        Args:
            content: Content to store
            user_id: User storing the content
            tenant_id: Optional tenant context
            metadata: Additional metadata
            confidence: Confidence score
            
        Returns:
            Stored memory data
        """
        ...

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        user_id: UUID,
        tenant_id: UUID | None = None,
        limit: int = 20,
        min_confidence: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Retrieve information from this layer.
        
        Args:
            query: Search query
            user_id: User performing search
            tenant_id: Optional tenant context
            limit: Maximum results
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of matching memories
        """
        ...

    @abstractmethod
    async def delete(
        self,
        memory_id: str,
        user_id: UUID,
        tenant_id: UUID | None = None,
    ) -> bool:
        """Delete a memory from this layer.
        
        Args:
            memory_id: Memory to delete
            user_id: User requesting deletion
            tenant_id: Optional tenant context
            
        Returns:
            True if deleted successfully
        """
        ...

    def get_filter_conditions(
        self,
        user_id: UUID,
        tenant_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Get filter conditions for database queries.
        
        Args:
            user_id: User context
            tenant_id: Tenant context
            
        Returns:
            Dictionary of filter conditions
        """
        return {"layer": self.name}
