"""
API endpoints for edge operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.database import get_db
from app.services.graph_service import GraphService
from app.schemas.graph import EdgeCreate, EdgeResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/edges", response_model=EdgeResponse, status_code=status.HTTP_201_CREATED)
async def create_edge(
    edge_data: EdgeCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new directed edge between two nodes.
    
    This creates a connection from the source node to the target node.
    Both nodes must already exist.
    
    **Parameters:**
    - **source_node_id**: ID of the source node (required)
    - **target_node_id**: ID of the target node (required)
    - **label**: Optional label for the edge
    
    **Returns:**
    - The created edge with generated ID and timestamp
    
    **Status Codes:**
    - **201**: Edge successfully created
    - **404**: Source or target node not found
    - **422**: Invalid input data
    """
    try:
        edge = await GraphService.create_edge(db, edge_data)
        return edge
    except ValueError as e:
        # Node not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating edge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the edge"
        )
