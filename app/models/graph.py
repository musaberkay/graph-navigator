"""
Database models for graph structure.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.core.database import Base


class Node(Base):
    """
    Represents a node in the graph.
    """
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    outgoing_edges = relationship(
        "Edge",
        foreign_keys="Edge.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan"
    )
    
    incoming_edges = relationship(
        "Edge",
        foreign_keys="Edge.target_node_id",
        back_populates="target_node",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Node(id={self.id}, name='{self.name}')>"


class Edge(Base):
    """
    Represents a directed edge between two nodes.
    """
    __tablename__ = "edges"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source_node_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    label = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    source_node = relationship("Node", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("Node", foreign_keys=[target_node_id], back_populates="incoming_edges")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_source_node', 'source_node_id'),
        Index('idx_target_node', 'target_node_id'),
        Index('idx_source_target', 'source_node_id', 'target_node_id'),
    )
    
    def __repr__(self):
        return f"<Edge(id={self.id}, source={self.source_node_id}, target={self.target_node_id})>"
