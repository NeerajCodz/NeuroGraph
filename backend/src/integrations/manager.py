"""Integration connections manager."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from src.core.logging import get_logger
from src.db.postgres import get_postgres_driver
from src.models.integrations import (
    IntegrationConnection,
    IntegrationConnectionCreate,
    IntegrationConnectionUpdate,
)

logger = get_logger(__name__)


class IntegrationManager:
    """Manage integration connections."""
    
    def __init__(self):
        self.db = get_postgres_driver()
    
    async def create_connection(
        self,
        user_id: UUID,
        connection: IntegrationConnectionCreate,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None,
    ) -> IntegrationConnection:
        """Create a new integration connection.
        
        Args:
            user_id: User ID
            connection: Connection data
            access_token: OAuth access token (will be encrypted)
            refresh_token: OAuth refresh token (will be encrypted)
            token_expires_at: Token expiration time
            
        Returns:
            Created connection
        """
        async with self.db.connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO integrations.connections (
                    user_id, tenant_id, integration_type, scope, name,
                    access_token, refresh_token, token_expires_at,
                    external_id, external_name, config, enabled
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING id, user_id, tenant_id, integration_type, scope, name,
                          external_id, external_name, config, enabled, status,
                          last_sync_at, last_error, created_at, updated_at
                """,
                user_id,
                connection.tenant_id,
                connection.integration_type,
                connection.scope,
                connection.name,
                access_token,  # TODO: Encrypt before storing
                refresh_token,  # TODO: Encrypt before storing
                token_expires_at,
                connection.external_id,
                connection.external_name,
                connection.config,
                connection.enabled,
            )
            
            logger.info(
                "integration_connection_created",
                connection_id=str(row["id"]),
                integration_type=connection.integration_type,
                scope=connection.scope,
            )
            
            return IntegrationConnection(**dict(row))
    
    async def get_connection(
        self,
        connection_id: UUID,
        user_id: UUID,
    ) -> Optional[IntegrationConnection]:
        """Get connection by ID.
        
        Args:
            connection_id: Connection ID
            user_id: User ID (for authorization)
            
        Returns:
            Connection or None
        """
        async with self.db.connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, tenant_id, integration_type, scope, name,
                       external_id, external_name, config, enabled, status,
                       last_sync_at, last_error, created_at, updated_at
                FROM integrations.connections
                WHERE id = $1 AND (
                    user_id = $2 
                    OR tenant_id IN (
                        SELECT tenant_id FROM auth.tenant_members WHERE user_id = $2
                    )
                )
                """,
                connection_id,
                user_id,
            )
            
            if not row:
                return None
            
            return IntegrationConnection(**dict(row))
    
    async def list_connections(
        self,
        user_id: UUID,
        tenant_id: Optional[UUID] = None,
        integration_type: Optional[str] = None,
        scope: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[IntegrationConnection]:
        """List user's integration connections.
        
        Args:
            user_id: User ID
            tenant_id: Optional tenant ID filter
            integration_type: Optional integration type filter
            scope: Optional scope filter (personal/workspace)
            enabled_only: Only return enabled connections
            
        Returns:
            List of connections
        """
        conditions = ["(user_id = $1 OR tenant_id IN (SELECT tenant_id FROM auth.tenant_members WHERE user_id = $1))"]
        params = [user_id]
        param_idx = 2
        
        if tenant_id:
            conditions.append(f"tenant_id = ${param_idx}")
            params.append(tenant_id)
            param_idx += 1
        
        if integration_type:
            conditions.append(f"integration_type = ${param_idx}")
            params.append(integration_type)
            param_idx += 1
        
        if scope:
            conditions.append(f"scope = ${param_idx}")
            params.append(scope)
            param_idx += 1
        
        if enabled_only:
            conditions.append("enabled = TRUE")
        
        where_clause = " AND ".join(conditions)
        
        async with self.db.connection() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, user_id, tenant_id, integration_type, scope, name,
                       external_id, external_name, config, enabled, status,
                       last_sync_at, last_error, created_at, updated_at
                FROM integrations.connections
                WHERE {where_clause}
                ORDER BY created_at DESC
                """,
                *params,
            )
            
            return [IntegrationConnection(**dict(row)) for row in rows]
    
    async def update_connection(
        self,
        connection_id: UUID,
        user_id: UUID,
        update: IntegrationConnectionUpdate,
    ) -> Optional[IntegrationConnection]:
        """Update integration connection.
        
        Args:
            connection_id: Connection ID
            user_id: User ID (for authorization)
            update: Update data
            
        Returns:
            Updated connection or None
        """
        # Build update query dynamically
        updates = []
        params = [connection_id, user_id]
        param_idx = 3
        
        if update.name is not None:
            updates.append(f"name = ${param_idx}")
            params.append(update.name)
            param_idx += 1
        
        if update.config is not None:
            updates.append(f"config = ${param_idx}")
            params.append(update.config)
            param_idx += 1
        
        if update.enabled is not None:
            updates.append(f"enabled = ${param_idx}")
            params.append(update.enabled)
            param_idx += 1
        
        if not updates:
            # No updates
            return await self.get_connection(connection_id, user_id)
        
        set_clause = ", ".join(updates)
        
        async with self.db.connection() as conn:
            row = await conn.fetchrow(
                f"""
                UPDATE integrations.connections
                SET {set_clause}
                WHERE id = $1 AND (
                    user_id = $2 
                    OR tenant_id IN (
                        SELECT tenant_id FROM auth.tenant_members WHERE user_id = $2
                    )
                )
                RETURNING id, user_id, tenant_id, integration_type, scope, name,
                          external_id, external_name, config, enabled, status,
                          last_sync_at, last_error, created_at, updated_at
                """,
                *params,
            )
            
            if not row:
                return None
            
            logger.info(
                "integration_connection_updated",
                connection_id=str(connection_id),
            )
            
            return IntegrationConnection(**dict(row))
    
    async def delete_connection(
        self,
        connection_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete integration connection.
        
        Args:
            connection_id: Connection ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted, False if not found
        """
        async with self.db.connection() as conn:
            result = await conn.execute(
                """
                DELETE FROM integrations.connections
                WHERE id = $1 AND (
                    user_id = $2 
                    OR tenant_id IN (
                        SELECT tenant_id FROM auth.tenant_members WHERE user_id = $2
                    )
                )
                """,
                connection_id,
                user_id,
            )
            
            deleted = result.split()[-1] == "1"
            
            if deleted:
                logger.info(
                    "integration_connection_deleted",
                    connection_id=str(connection_id),
                )
            
            return deleted
    
    async def update_sync_status(
        self,
        connection_id: UUID,
        success: bool = True,
        error: Optional[str] = None,
    ):
        """Update connection sync status.
        
        Args:
            connection_id: Connection ID
            success: Whether sync was successful
            error: Error message if failed
        """
        async with self.db.connection() as conn:
            await conn.execute(
                """
                UPDATE integrations.connections
                SET last_sync_at = NOW(),
                    status = $2,
                    last_error = $3
                WHERE id = $1
                """,
                connection_id,
                "active" if success else "error",
                error,
            )
    
    async def get_tokens(
        self,
        connection_id: UUID,
    ) -> Optional[dict]:
        """Get OAuth tokens for a connection.
        
        Args:
            connection_id: Connection ID
            
        Returns:
            Dict with access_token, refresh_token, token_expires_at or None
        """
        async with self.db.connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT access_token, refresh_token, token_expires_at
                FROM integrations.connections
                WHERE id = $1
                """,
                connection_id,
            )
            
            if not row:
                return None
            
            # TODO: Decrypt tokens before returning
            return {
                "access_token": row["access_token"],
                "refresh_token": row["refresh_token"],
                "token_expires_at": row["token_expires_at"],
            }
