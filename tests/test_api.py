"""
Tests for node API endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_node(client: AsyncClient):
    """Test creating a new node."""
    response = await client.post(
        "/nodes",
        json={"name": "Test Node", "description": "A test node"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Node"
    assert data["description"] == "A test node"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_node(client: AsyncClient, sample_nodes):
    """Test retrieving a specific node."""
    node = sample_nodes[0]
    response = await client.get(f"/nodes/{node.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == node.id
    assert data["name"] == node.name


@pytest.mark.asyncio
async def test_get_nonexistent_node(client: AsyncClient):
    """Test retrieving a node that doesn't exist."""
    response = await client.get("/nodes/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_nodes(client: AsyncClient, sample_nodes):
    """Test listing nodes with pagination."""
    response = await client.get("/nodes?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) == len(sample_nodes)


@pytest.mark.asyncio
async def test_get_connected_nodes(client: AsyncClient, sample_graph):
    """Test getting connected nodes from a source node."""
    # Node 1 connects to Node 2 (depth 1) and Node 3 (depth 2)
    # Node 1 also connects to Node 4 (depth 1) and Node 5 (depth 2)
    node1 = sample_graph[0]
    
    response = await client.get(f"/nodes/{node1.id}/connected")
    assert response.status_code == 200
    
    data = response.json()
    assert data["source_node_id"] == node1.id
    assert "connected_nodes" in data
    assert data["total_connected"] >= 4  # At least 4 connected nodes


@pytest.mark.asyncio
async def test_get_connected_nodes_nonexistent(client: AsyncClient):
    """Test getting connected nodes for nonexistent node."""
    response = await client.get("/nodes/99999/connected")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_edge(client: AsyncClient, sample_nodes):
    """Test creating an edge between nodes."""
    response = await client.post(
        "/edges",
        json={
            "source_node_id": sample_nodes[0].id,
            "target_node_id": sample_nodes[1].id,
            "label": "test-edge"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["source_node_id"] == sample_nodes[0].id
    assert data["target_node_id"] == sample_nodes[1].id
    assert data["label"] == "test-edge"


@pytest.mark.asyncio
async def test_create_edge_invalid_nodes(client: AsyncClient):
    """Test creating an edge with invalid node IDs."""
    response = await client.post(
        "/edges",
        json={
            "source_node_id": 99999,
            "target_node_id": 99998,
        }
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_node(client: AsyncClient, sample_nodes):
    """Test deleting a node."""
    node = sample_nodes[0]
    response = await client.delete(f"/nodes/{node.id}")
    assert response.status_code == 204
    
    # Verify node is deleted
    get_response = await client.get(f"/nodes/{node.id}")
    assert get_response.status_code == 404
