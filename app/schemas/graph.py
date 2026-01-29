"""
Pydantic schemas for API validation and serialization.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# Node Schemas
class NodeBase(BaseModel):
    """Base schema for Node."""
    name: str = Field(..., min_length=1, max_length=255, description="Node name")
    description: Optional[str] = Field(None, description="Optional node description")


class NodeCreate(NodeBase):
    """Schema for creating a new node."""
    pass


class NodeUpdate(BaseModel):
    """Schema for updating a node."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class NodeResponse(NodeBase):
    """Schema for node responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ConnectedNodeInfo(BaseModel):
    """Schema for connected node information with depth."""
    id: int
    name: str
    depth: int
    
    model_config = ConfigDict(from_attributes=True)


class ConnectedNodesResponse(BaseModel):
    """Schema for the connected nodes endpoint response."""
    source_node_id: int
    connected_nodes: List[ConnectedNodeInfo]
    total_connected: int


# Edge Schemas
class EdgeBase(BaseModel):
    """Base schema for Edge."""
    source_node_id: int = Field(..., description="Source node ID")
    target_node_id: int = Field(..., description="Target node ID")
    label: Optional[str] = Field(None, max_length=255, description="Optional edge label")


class EdgeCreate(EdgeBase):
    """Schema for creating a new edge."""
    pass


class EdgeResponse(EdgeBase):
    """Schema for edge responses."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Pagination
class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List[NodeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Health Check
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str
    timestamp: datetime
