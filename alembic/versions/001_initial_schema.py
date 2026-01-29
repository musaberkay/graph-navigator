"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-01-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create nodes table
    op.create_table(
        'nodes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_nodes_id', 'nodes', ['id'], unique=False)
    op.create_index('ix_nodes_name', 'nodes', ['name'], unique=False)
    
    # Create edges table
    op.create_table(
        'edges',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_node_id', sa.Integer(), nullable=False),
        sa.Column('target_node_id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['source_node_id'], ['nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_node_id'], ['nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_edges_id', 'edges', ['id'], unique=False)
    op.create_index('idx_source_node', 'edges', ['source_node_id'], unique=False)
    op.create_index('idx_target_node', 'edges', ['target_node_id'], unique=False)
    op.create_index('idx_source_target', 'edges', ['source_node_id', 'target_node_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_source_target', table_name='edges')
    op.drop_index('idx_target_node', table_name='edges')
    op.drop_index('idx_source_node', table_name='edges')
    op.drop_index('ix_edges_id', table_name='edges')
    op.drop_table('edges')
    
    op.drop_index('ix_nodes_name', table_name='nodes')
    op.drop_index('ix_nodes_id', table_name='nodes')
    op.drop_table('nodes')
