"""
Service layer for graph operations.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from typing import List, Optional
import logging

from app.models.graph import Node, Edge
from app.schemas.graph import NodeCreate, EdgeCreate, ConnectedNodeInfo

logger = logging.getLogger(__name__)


class GraphService:
    """
    Service for graph-related operations.
    """
    
    @staticmethod
    async def get_node(db: AsyncSession, node_id: int) -> Optional[Node]:
        """
        Get a node by ID.
        """
        result = await db.execute(select(Node).where(Node.id == node_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_nodes(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Node], int]:
        """
        Get paginated list of nodes.
        Returns (nodes, total_count).
        """
        # Get total count
        count_result = await db.execute(select(func.count(Node.id)))
        total = count_result.scalar()
        
        # Get paginated nodes
        result = await db.execute(
            select(Node)
            .offset(skip)
            .limit(limit)
            .order_by(Node.id)
        )
        nodes = result.scalars().all()
        
        return list(nodes), total
    
    @staticmethod
    async def create_node(db: AsyncSession, node_data: NodeCreate) -> Node:
        """
        Create a new node.
        """
        node = Node(
            name=node_data.name,
            description=node_data.description
        )
        db.add(node)
        await db.commit()
        await db.refresh(node)
        return node
    
    @staticmethod
    async def create_edge(db: AsyncSession, edge_data: EdgeCreate) -> Edge:
        """
        Create a new edge between nodes.
        """
        # Verify both nodes exist
        source = await GraphService.get_node(db, edge_data.source_node_id)
        target = await GraphService.get_node(db, edge_data.target_node_id)
        
        if not source:
            raise ValueError(f"Source node {edge_data.source_node_id} not found")
        if not target:
            raise ValueError(f"Target node {edge_data.target_node_id} not found")
        
        edge = Edge(
            source_node_id=edge_data.source_node_id,
            target_node_id=edge_data.target_node_id,
            label=edge_data.label
        )
        db.add(edge)
        await db.commit()
        await db.refresh(edge)
        return edge
    
    @staticmethod
    async def get_connected_nodes(
        db: AsyncSession,
        node_id: int
    ) -> List[ConnectedNodeInfo]:
        """
        Get all nodes connected to the given node using a single recursive query.
        
        Uses MySQL's WITH RECURSIVE CTE to traverse the graph efficiently.
        Returns nodes with their depth from the source node.
        """
        # First verify the source node exists
        source_node = await GraphService.get_node(db, node_id)
        if not source_node:
            return None
        
        # Recursive CTE query to find all connected nodes
        # Uses path tracking to detect and avoid cycles
        query = text("""
            WITH RECURSIVE node_tree AS (
                -- Base case: direct children of the source node
                SELECT
                    e.target_node_id as node_id,
                    1 as depth,
                    CAST(CONCAT(',', :source_node_id, ',', e.target_node_id, ',') AS CHAR(4000)) as path
                FROM edges e
                WHERE e.source_node_id = :source_node_id

                UNION ALL

                -- Recursive case: children of previously found nodes
                -- Only visit nodes not already in the current path (cycle detection)
                SELECT
                    e.target_node_id as node_id,
                    nt.depth + 1 as depth,
                    CONCAT(nt.path, e.target_node_id, ',') as path
                FROM edges e
                INNER JOIN node_tree nt ON e.source_node_id = nt.node_id
                WHERE nt.path NOT LIKE CONCAT('%,', e.target_node_id, ',%')
                  AND CHAR_LENGTH(nt.path) < 3900  -- Stop before exceeding path column limit
                  AND nt.depth < 100  -- Safety limit for very deep graphs
            )
            -- Get nodes with their minimum depth
            SELECT
                n.id,
                n.name,
                MIN(nt.depth) as depth
            FROM nodes n
            INNER JOIN node_tree nt ON n.id = nt.node_id
            GROUP BY n.id, n.name
            ORDER BY depth, n.id
        """)
        
        result = await db.execute(query, {"source_node_id": node_id})
        rows = result.fetchall()
        
        # Convert to ConnectedNodeInfo objects
        connected_nodes = [
            ConnectedNodeInfo(
                id=row[0],
                name=row[1],
                depth=row[2]
            )
            for row in rows
        ]
        
        logger.info(f"Found {len(connected_nodes)} nodes connected to node {node_id}")
        return connected_nodes
    
    @staticmethod
    async def delete_node(db: AsyncSession, node_id: int) -> bool:
        """
        Delete a node and all its associated edges.
        """
        node = await GraphService.get_node(db, node_id)
        if not node:
            return False
        
        await db.delete(node)
        await db.commit()
        return True


# Import func for count
from sqlalchemy import func
