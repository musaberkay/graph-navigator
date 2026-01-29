"""
API endpoints for node operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from app.core.database import get_db
from app.services.graph_service import GraphService
from app.schemas.graph import (
    NodeCreate, NodeResponse, NodeUpdate, 
    ConnectedNodesResponse, PaginatedResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/nodes/{node_id}/connected", response_model=ConnectedNodesResponse)
async def get_connected_nodes(
    node_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all nodes reachable from the specified node.
    
    This endpoint performs a recursive traversal of the graph starting from
    the given node and returns all nodes that can be reached by following edges.
    
    The traversal is performed using a single optimized SQL query with a
    recursive CTE (Common Table Expression).
    
    **Parameters:**
    - **node_id**: The ID of the starting node
    
    **Returns:**
    - **source_node_id**: The ID of the starting node
    - **connected_nodes**: List of all reachable nodes with their depth from source
    - **total_connected**: Total count of connected nodes
    
    **Status Codes:**
    - **200**: Successfully retrieved connected nodes
    - **404**: Source node not found
    - **500**: Internal server error
    """
    try:
        # Get connected nodes using recursive query
        connected_nodes = await GraphService.get_connected_nodes(db, node_id)
        
        if connected_nodes is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node with id {node_id} not found"
            )
        
        return ConnectedNodesResponse(
            source_node_id=node_id,
            connected_nodes=connected_nodes,
            total_connected=len(connected_nodes)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connected nodes for node {node_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving connected nodes"
        )


@router.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific node by ID.
    
    **Parameters:**
    - **node_id**: The ID of the node to retrieve
    
    **Returns:**
    - Node details including id, name, description, and timestamps
    
    **Status Codes:**
    - **200**: Successfully retrieved node
    - **404**: Node not found
    """
    node = await GraphService.get_node(db, node_id)
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node with id {node_id} not found"
        )
    
    return node


@router.get("/nodes", response_model=PaginatedResponse)
async def list_nodes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all nodes with pagination.
    
    **Parameters:**
    - **page**: Page number (default: 1)
    - **page_size**: Number of items per page (default: 50, max: 100)
    
    **Returns:**
    - Paginated list of nodes with metadata
    
    **Status Codes:**
    - **200**: Successfully retrieved nodes
    """
    skip = (page - 1) * page_size
    nodes, total = await GraphService.get_nodes(db, skip=skip, limit=page_size)
    
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=nodes,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/nodes", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def create_node(
    node_data: NodeCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new node in the graph.
    
    **Parameters:**
    - **name**: Node name (required)
    - **description**: Optional node description
    
    **Returns:**
    - The created node with generated ID and timestamps
    
    **Status Codes:**
    - **201**: Node successfully created
    - **422**: Invalid input data
    """
    try:
        node = await GraphService.create_node(db, node_data)
        return node
    except Exception as e:
        logger.error(f"Error creating node: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the node"
        )


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a node and all its associated edges.
    
    **Parameters:**
    - **node_id**: The ID of the node to delete
    
    **Status Codes:**
    - **204**: Node successfully deleted
    - **404**: Node not found
    """
    deleted = await GraphService.delete_node(db, node_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node with id {node_id} not found"
        )
