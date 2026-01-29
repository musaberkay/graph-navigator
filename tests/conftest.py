"""
Pytest configuration and fixtures.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.graph import Node, Edge


# Use in-memory SQLite for testing (or a test MySQL database)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database and session.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client with dependency override.
    """
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def sample_nodes(test_db: AsyncSession):
    """
    Create sample nodes for testing.
    """
    node1 = Node(name="Node 1", description="First node")
    node2 = Node(name="Node 2", description="Second node")
    node3 = Node(name="Node 3", description="Third node")
    
    test_db.add_all([node1, node2, node3])
    await test_db.commit()
    
    return [node1, node2, node3]


@pytest.fixture
async def sample_graph(test_db: AsyncSession):
    """
    Create a sample graph structure for testing.
    """
    # Create nodes
    nodes = [Node(name=f"Node {i}", description=f"Node {i}") for i in range(1, 6)]
    test_db.add_all(nodes)
    await test_db.flush()
    
    # Create edges: 1->2, 2->3, 1->4, 4->5
    edges = [
        Edge(source_node_id=nodes[0].id, target_node_id=nodes[1].id),
        Edge(source_node_id=nodes[1].id, target_node_id=nodes[2].id),
        Edge(source_node_id=nodes[0].id, target_node_id=nodes[3].id),
        Edge(source_node_id=nodes[3].id, target_node_id=nodes[4].id),
    ]
    test_db.add_all(edges)
    await test_db.commit()
    
    return nodes
