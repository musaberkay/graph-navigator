# Quick Start Guide

## 1. Start the Services

```bash
docker-compose up --build
```

Wait for:
- ✅ Database to be ready
- ✅ Migrations to run
- ✅ Database to be seeded
- ✅ API server to start

## 2. Verify the API is Running

Open your browser to: http://localhost:8000/docs

You should see the interactive API documentation.

## 3. Test the Connectivity Query

### Option A: Using the Browser (Swagger UI)

1. Go to http://localhost:8000/docs
2. Find `GET /nodes/{node_id}/connected`
3. Click "Try it out"
4. Enter `1` as the node_id
5. Click "Execute"

### Option B: Using cURL

```bash
curl http://localhost:8000/nodes/1/connected
```

### Expected Response

You should see a JSON response with:
- `source_node_id`: 1
- `connected_nodes`: Array of all nodes reachable from node 1
- `total_connected`: Number of connected nodes (should be 23+)

Example:
```json
{
  "source_node_id": 1,
  "connected_nodes": [
    {"id": 2, "name": "Branch A", "depth": 1},
    {"id": 3, "name": "Branch B", "depth": 1},
    {"id": 4, "name": "Branch C", "depth": 1},
    {"id": 5, "name": "A-1", "depth": 2},
    ...
  ],
  "total_connected": 23
}
```

## 4. Explore the Graph

Try different starting nodes:
- Node 2: `curl http://localhost:8000/nodes/2/connected`
- Node 5: `curl http://localhost:8000/nodes/5/connected`
- Node 11: `curl http://localhost:8000/nodes/11/connected`

## 5. View All Nodes

```bash
curl http://localhost:8000/nodes
```

## 6. Create Your Own Nodes and Edges

Create a node:
```bash
curl -X POST http://localhost:8000/nodes \
  -H "Content-Type: application/json" \
  -d '{"name": "My Node", "description": "Custom node"}'
```

Create an edge:
```bash
curl -X POST http://localhost:8000/edges \
  -H "Content-Type: application/json" \
  -d '{"source_node_id": 1, "target_node_id": 25, "label": "custom"}'
```

## Troubleshooting

### Port Already in Use
Edit `docker-compose.yml` and change the port mapping:
```yaml
ports:
  - "8001:8000"  # Changed from 8000:8000
```

### Fresh Start
```bash
docker-compose down -v
docker-compose up --build
```

### View Logs
```bash
docker-compose logs -f api
```

## Next Steps

- Read the full [README.md](README.md) for architectural details
- Check the API documentation at http://localhost:8000/docs
- Run the test suite: `docker-compose run --rm api pytest`
