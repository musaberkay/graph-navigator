# Testing Guide for Evaluators

This guide helps you quickly verify all aspects of the Graph Navigator service.

## Prerequisites

- Docker installed and running
- Docker Compose installed
- Ports 8000 and 3306 available

---

## Test Scenario 1: Basic Startup (2 minutes)

### 1. Start the Services

```bash
cd graph-navigator
docker-compose up --build
```

**Expected Output:**

```
✅ MySQL starts and becomes healthy
✅ Migrations run successfully
✅ Database is seeded with 24 nodes
✅ API server starts on port 8000
```

### 2. Verify Health

```bash
curl http://localhost:8000/health
```

**Expected Response:**

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-28T..."
}
```

### 3. Check API Documentation

Open: http://localhost:8000/docs

**Expected:** Interactive Swagger UI with all endpoints

---

## Test Scenario 2: Graph Traversal (Main Feature)

### Test 1: Get All Connected Nodes from Root

```bash
curl http://localhost:8000/nodes/1/connected
```

**Expected Response:**

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

**Verification Points:**

- ✅ Returns HTTP 200
- ✅ Contains 23 connected nodes (all except node 1 itself)
- ✅ Nodes are ordered by depth
- ✅ Depth values are correct (1, 2, 3, 4, 5, 6)

### Test 2: Get Connected Nodes from Mid-Level Node

```bash
curl http://localhost:8000/nodes/5/connected
```

**Expected Response:**

```json
{
  "source_node_id": 5,
  "connected_nodes": [
    {"id": 11, "name": "A-1-1", "depth": 1},
    {"id": 12, "name": "A-1-2", "depth": 1},
    {"id": 14, "name": "B-1-1", "depth": 1},
    {"id": 17, "name": "A-1-1-1", "depth": 2},
    ...
  ],
  "total_connected": 7
}
```

**Verification Points:**

- ✅ Returns fewer nodes (only descendants of node 5)
- ✅ Correct depth calculations from new starting point
- ✅ Includes cross-linked nodes (node 14)

### Test 3: Get Connected Nodes from Leaf Node

```bash
curl http://localhost:8000/nodes/24/connected
```

**Expected Response:**

```json
{
  "source_node_id": 24,
  "connected_nodes": [],
  "total_connected": 0
}
```

**Verification Points:**

- ✅ Returns HTTP 200 (not 404)
- ✅ Empty list of connected nodes
- ✅ Leaf node has no descendants

### Test 4: Nonexistent Node

```bash
curl http://localhost:8000/nodes/999/connected
```

**Expected Response:**

```json
{
  "detail": "Node with id 999 not found"
}
```

**Verification Points:**

- ✅ Returns HTTP 404
- ✅ Clear error message

---

## Test Scenario 3: CRUD Operations

### Create a Node

```bash
curl -X POST http://localhost:8000/nodes \
  -H "Content-Type: application/json" \
  -d '{"name": "New Node", "description": "Test node"}'
```

**Expected:** HTTP 201, returns created node with ID

### Create an Edge

```bash
curl -X POST http://localhost:8000/edges \
  -H "Content-Type: application/json" \
  -d '{"source_node_id": 1, "target_node_id": 25, "label": "test"}'
```

**Expected:** HTTP 201, edge created

### Verify New Connection

```bash
curl http://localhost:8000/nodes/1/connected
```

**Expected:** Now includes node 25 in results

### List All Nodes

```bash
curl http://localhost:8000/nodes?page=1&page_size=10
```

**Expected:** Paginated list with 10 nodes

### Get Single Node

```bash
curl http://localhost:8000/nodes/1
```

**Expected:** Full node details

### Delete Node

```bash
curl -X DELETE http://localhost:8000/nodes/25
```

**Expected:** HTTP 204 No Content

---

## Test Scenario 4: Verify Single Query Implementation

### Method 1: Check Logs

```bash
docker-compose logs api | grep "WITH RECURSIVE"
```

**Expected:** You should see the recursive query in the logs (if DEBUG=true)

### Method 2: Database Query Analysis

```bash
# Connect to MySQL
docker-compose exec db mysql -u graphuser -pgraphpassword graphdb

# Run EXPLAIN on the query
EXPLAIN WITH RECURSIVE node_tree AS (
    SELECT target_node_id as node_id, 1 as depth
    FROM edges
    WHERE source_node_id = 1
    UNION ALL
    SELECT e.target_node_id, nt.depth + 1
    FROM edges e
    INNER JOIN node_tree nt ON e.source_node_id = nt.node_id
    WHERE nt.depth < 100
)
SELECT n.id, n.name, MIN(nt.depth) as depth
FROM nodes n
INNER JOIN node_tree nt ON n.id = nt.node_id
GROUP BY n.id, n.name
ORDER BY depth, n.id;
```

**Expected:** Query plan showing recursive CTE execution

---

## Test Scenario 5: Graph Structure Verification

### Verify Graph Depth

The seeded graph has 6 levels:

```bash
# Check deepest node (level 6)
curl http://localhost:8000/nodes/1/connected | jq '.connected_nodes[] | select(.depth == 6)'
```

**Expected Response:**

```json
{
  "id": 24,
  "name": "A-1-1-1-1-1",
  "depth": 6
}
```

### Verify Multiple Edges per Node

```bash
# Node 1 should have 3 direct children
curl http://localhost:8000/nodes/1/connected | jq '.connected_nodes[] | select(.depth == 1)'
```

**Expected:** 3 nodes at depth 1 (nodes 2, 3, 4)

### Verify Cross-Links

```bash
# Node 2 has a cross-link to node 7
curl http://localhost:8000/nodes/2/connected | jq '.connected_nodes[] | select(.name == "B-1")'
```

**Expected:** Node 7 appears in results

---

## Test Scenario 6: Performance Testing

### Test Large Graph Traversal

```bash
# Time the query
time curl http://localhost:8000/nodes/1/connected
```

**Expected:** Response in < 100ms for 24 nodes

### Create More Nodes

```bash
# Create 100 additional nodes
for i in {26..125}; do
  curl -X POST http://localhost:8000/nodes \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"Node $i\"}"
done

# Connect them in a chain
for i in {26..124}; do
  j=$((i+1))
  curl -X POST http://localhost:8000/edges \
    -H "Content-Type: application/json" \
    -d "{\"source_node_id\": $i, \"target_node_id\": $j}"
done

# Test traversal
time curl http://localhost:8000/nodes/26/connected
```

**Expected:** Still completes quickly (< 500ms)

---

## Test Scenario 7: Error Handling

### Invalid Input

```bash
curl -X POST http://localhost:8000/nodes \
  -H "Content-Type: application/json" \
  -d '{"name": ""}'
```

**Expected:** HTTP 422, validation error

### Invalid Edge

```bash
curl -X POST http://localhost:8000/edges \
  -H "Content-Type: application/json" \
  -d '{"source_node_id": 999, "target_node_id": 1}'
```

**Expected:** HTTP 404, "Source node 999 not found"

### Malformed JSON

```bash
curl -X POST http://localhost:8000/nodes \
  -H "Content-Type: application/json" \
  -d '{invalid json}'
```

**Expected:** HTTP 422, parse error

---

## Test Scenario 8: Run Test Suite

```bash
docker-compose run --rm api pytest -v
```

**Expected Output:**

```
tests/test_api.py::test_health_check PASSED
tests/test_api.py::test_create_node PASSED
tests/test_api.py::test_get_node PASSED
tests/test_api.py::test_get_connected_nodes PASSED
...
========================= X passed =========================
```

---

## Test Scenario 9: Documentation Verification

### Check OpenAPI Schema

```bash
curl http://localhost:8000/openapi.json | jq '.paths["/nodes/{node_id}/connected"]'
```

**Expected:** Full endpoint documentation

### Check ReDoc

Open: http://localhost:8000/redoc

**Expected:** Alternative documentation UI

---

## Test Scenario 10: Cleanup

### Stop Services

```bash
docker-compose down
```

### Full Cleanup (Remove Volumes)

```bash
docker-compose down -v
```

### Restart Fresh

```bash
docker-compose up --build
```

**Expected:** Database is reseeded, clean state

---

## Common Issues & Solutions

### Port 8000 in Use

```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"
```

### Database Not Ready

```bash
# Check MySQL logs
docker-compose logs db

# Wait for "ready for connections"
```

### Permission Issues

```bash
# Clean and rebuild
docker-compose down -v
docker-compose up --build
```

---

## Performance Benchmarks

For reference, expected performance on a modern laptop:

- **Startup time**: ~30 seconds
- **Migration time**: ~2 seconds
- **Seeding time**: ~1 second
- **Query time (24 nodes)**: <50ms
- **Query time (1000 nodes)**: <200ms

---

## Need Help?

If something doesn't work:

1. Check logs: `docker-compose logs -f`
2. Verify ports: `netstat -an | grep 8000`
3. Clean start: `docker-compose down -v && docker-compose up --build`
4. Check README.md troubleshooting section
