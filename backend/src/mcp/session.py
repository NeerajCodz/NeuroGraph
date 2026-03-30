"""MCP Session management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from src.core.config import get_settings
from src.core.logging import get_logger
from src.db.neo4j import get_neo4j_driver
from src.db.postgres import get_postgres_driver
from src.memory.manager import MemoryManager

logger = get_logger(__name__)


@dataclass
class SessionState:
    """MCP session state."""
    session_id: str
    user_id: UUID
    tenant_id: UUID | None = None
    mode: str = "general"  # "general" or "organization"
    include_global: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


class MCPSession:
    """Manages MCP session state and provides access to memory system.
    
    Each MCP connection gets its own session with:
    - User context
    - Mode settings (general/organization)
    - Memory manager access
    """

    def __init__(self, user_id: UUID | None = None) -> None:
        self._settings = get_settings()
        self._state = SessionState(
            session_id=f"mcp_{uuid4().hex[:12]}",
            user_id=user_id or UUID(int=0),
        )
        self._memory_manager: MemoryManager | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize session resources."""
        if self._initialized:
            return
        
        # Ensure database connections are established
        neo4j = get_neo4j_driver()
        postgres = get_postgres_driver()
        
        await neo4j.connect()
        await postgres.connect()
        
        # Initialize memory manager
        self._memory_manager = MemoryManager()
        
        self._initialized = True
        logger.info("mcp_session_initialized", session_id=self._state.session_id)

    @property
    def session_id(self) -> str:
        return self._state.session_id

    @property
    def user_id(self) -> UUID:
        return self._state.user_id

    @property
    def tenant_id(self) -> UUID | None:
        return self._state.tenant_id

    @property
    def mode(self) -> str:
        return self._state.mode

    @property
    def include_global(self) -> bool:
        return self._state.include_global

    @property
    def memory_manager(self) -> MemoryManager:
        if not self._memory_manager:
            raise RuntimeError("Session not initialized")
        return self._memory_manager

    def set_user(self, user_id: UUID) -> None:
        """Set the user ID for this session."""
        self._state.user_id = user_id
        self._state.last_activity = datetime.utcnow()

    def set_mode(
        self,
        mode: str,
        tenant_id: UUID | None = None,
        include_global: bool = True,
    ) -> None:
        """Switch session mode.
        
        Args:
            mode: "general" or "organization"
            tenant_id: Required for organization mode
            include_global: Whether to include global memory
        """
        self._state.mode = mode
        self._state.tenant_id = tenant_id
        self._state.include_global = include_global
        self._state.last_activity = datetime.utcnow()
        
        logger.info(
            "mcp_mode_changed",
            session_id=self._state.session_id,
            mode=mode,
            tenant_id=str(tenant_id) if tenant_id else None,
        )

    def get_layers(self) -> list[str]:
        """Get accessible layers based on current mode."""
        layers = ["personal"]
        
        if self._state.mode == "organization" and self._state.tenant_id:
            layers.append("tenant")
        
        if self._state.include_global:
            layers.append("global")
        
        return layers

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self._state.last_activity = datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if session has expired."""
        timeout = self._settings.mcp_session_timeout
        elapsed = (datetime.utcnow() - self._state.last_activity).total_seconds()
        return elapsed > timeout

    async def close(self) -> None:
        """Clean up session resources."""
        self._memory_manager = None
        self._initialized = False
        logger.info("mcp_session_closed", session_id=self._state.session_id)
