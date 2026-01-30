"""
Script to seed the database with a sample graph structure.

Creates a graph that is at least 5 levels deep with multiple outgoing edges per node.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.graph import Node, Edge
from app.core.database import Base


async def seed_database():
    """
    Seed the database with a sample graph.
    
    Structure:
    - 5+ levels deep
    - Multiple children per node
    - Total ~20-30 nodes for demonstration
    """
    print("🌱 Starting database seeding...")
    
    # Create async engine and session
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            # Check if data already exists
            from sqlalchemy import select, func
            result = await session.execute(select(func.count(Node.id)))
            count = result.scalar()
            
            if count > 0:
                print(f"⚠️  Database already contains {count} nodes. Skipping seed.")
                return
            
            print("📝 Creating nodes...")
            
            # Level 0: Root node
            node1 = Node(name="Root Node", description="The starting point of our graph")
            session.add(node1)
            await session.flush()
            
            # Level 1: Three children of root
            node2 = Node(name="Branch A", description="First main branch")
            node3 = Node(name="Branch B", description="Second main branch")
            node4 = Node(name="Branch C", description="Third main branch")
            session.add_all([node2, node3, node4])
            await session.flush()
            
            # Level 2: Children of Level 1 nodes
            node5 = Node(name="A-1", description="First child of Branch A")
            node6 = Node(name="A-2", description="Second child of Branch A")
            node7 = Node(name="B-1", description="First child of Branch B")
            node8 = Node(name="B-2", description="Second child of Branch B")
            node9 = Node(name="C-1", description="First child of Branch C")
            node10 = Node(name="C-2", description="Second child of Branch C")
            session.add_all([node5, node6, node7, node8, node9, node10])
            await session.flush()
            
            # Level 3: Children of Level 2 nodes
            node11 = Node(name="A-1-1", description="Grandchild of A")
            node12 = Node(name="A-1-2", description="Another grandchild of A")
            node13 = Node(name="A-2-1", description="Grandchild of A-2")
            node14 = Node(name="B-1-1", description="Grandchild of B")
            node15 = Node(name="B-2-1", description="Grandchild of B-2")
            node16 = Node(name="C-1-1", description="Grandchild of C")
            session.add_all([node11, node12, node13, node14, node15, node16])
            await session.flush()
            
            # Level 4: Great-grandchildren
            node17 = Node(name="A-1-1-1", description="Great-grandchild level 4")
            node18 = Node(name="A-1-1-2", description="Another at level 4")
            node19 = Node(name="B-1-1-1", description="Deep node in B branch")
            node20 = Node(name="C-1-1-1", description="Deep node in C branch")
            session.add_all([node17, node18, node19, node20])
            await session.flush()
            
            # Level 5: Even deeper nodes
            node21 = Node(name="A-1-1-1-1", description="Very deep node - level 5")
            node22 = Node(name="A-1-1-2-1", description="Another level 5 node")
            node23 = Node(name="B-1-1-1-1", description="Level 5 in B branch")
            session.add_all([node21, node22, node23])
            await session.flush()
            
            # Level 6: Extra deep for good measure
            node24 = Node(name="A-1-1-1-1-1", description="Level 6 - very deep!")
            session.add(node24)
            await session.flush()
            
            print("🔗 Creating edges...")
            
            # Level 0 -> Level 1
            edges = [
                Edge(source_node_id=node1.id, target_node_id=node2.id, label="to-A"),
                Edge(source_node_id=node1.id, target_node_id=node3.id, label="to-B"),
                Edge(source_node_id=node1.id, target_node_id=node4.id, label="to-C"),
                
                # Level 1 -> Level 2
                Edge(source_node_id=node2.id, target_node_id=node5.id, label="branch"),
                Edge(source_node_id=node2.id, target_node_id=node6.id, label="branch"),
                Edge(source_node_id=node3.id, target_node_id=node7.id, label="branch"),
                Edge(source_node_id=node3.id, target_node_id=node8.id, label="branch"),
                Edge(source_node_id=node4.id, target_node_id=node9.id, label="branch"),
                Edge(source_node_id=node4.id, target_node_id=node10.id, label="branch"),
                
                # Level 2 -> Level 3
                Edge(source_node_id=node5.id, target_node_id=node11.id, label="child"),
                Edge(source_node_id=node5.id, target_node_id=node12.id, label="child"),
                Edge(source_node_id=node6.id, target_node_id=node13.id, label="child"),
                Edge(source_node_id=node7.id, target_node_id=node14.id, label="child"),
                Edge(source_node_id=node8.id, target_node_id=node15.id, label="child"),
                Edge(source_node_id=node9.id, target_node_id=node16.id, label="child"),
                
                # Level 3 -> Level 4
                Edge(source_node_id=node11.id, target_node_id=node17.id, label="deeper"),
                Edge(source_node_id=node11.id, target_node_id=node18.id, label="deeper"),
                Edge(source_node_id=node14.id, target_node_id=node19.id, label="deeper"),
                Edge(source_node_id=node16.id, target_node_id=node20.id, label="deeper"),
                
                # Level 4 -> Level 5
                Edge(source_node_id=node17.id, target_node_id=node21.id, label="very-deep"),
                Edge(source_node_id=node18.id, target_node_id=node22.id, label="very-deep"),
                Edge(source_node_id=node19.id, target_node_id=node23.id, label="very-deep"),
                
                # Level 5 -> Level 6
                Edge(source_node_id=node21.id, target_node_id=node24.id, label="deepest"),
            ]
            
            # Add some cross-connections to make it more interesting
            edges.extend([
                Edge(source_node_id=node2.id, target_node_id=node7.id, label="cross-link"),
                Edge(source_node_id=node3.id, target_node_id=node9.id, label="cross-link"),
                Edge(source_node_id=node5.id, target_node_id=node14.id, label="skip-level"),
                Edge(source_node_id=node6.id, target_node_id=node7.id, label="same-level"),
                Edge(source_node_id=node7.id, target_node_id=node2.id, label="upper-level"),
                Edge(source_node_id=node2.id, target_node_id=node23.id, label="lower-4-level"),
                Edge(source_node_id=node23.id, target_node_id=node22.id, label="same-level"),
                Edge(source_node_id=node22.id, target_node_id=node2.id, label="upper-level"),
                Edge(source_node_id=node3.id, target_node_id=node3.id, label="same-edge"),
            ])
            
            session.add_all(edges)
            await session.commit()
            
            print("✅ Database seeded successfully!")
            print(f"   Created {len([node1, node2, node3, node4, node5, node6, node7, node8, node9, node10, node11, node12, node13, node14, node15, node16, node17, node18, node19, node20, node21, node22, node23, node24])} nodes")
            print(f"   Created {len(edges)} edges")
            print(f"   Graph depth: 6 levels")
            print("\n🎯 Try querying connected nodes from node 1:")
            print(f"   curl http://localhost:8000/nodes/1/connected")
            
        except Exception as e:
            print(f"❌ Error seeding database: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
