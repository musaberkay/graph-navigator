# Architecture & Design Decisions

## Overview

This document explains the architectural choices made for the Graph Navigator service, including rationale, trade-offs, and alternatives considered.

## Architecture Pattern: Layered Architecture

### Chosen: Three-Layer Architecture

```
API Layer → Service Layer → Data Layer
```

**Rationale:**

- **Separation of Concerns**: Each layer has a clear responsibility
- **Testability**: Layers can be tested independently
- **Maintainability**: Changes in one layer don't ripple through the system
- **Scalability**: Easy to add new features without modifying existing code

**Layers:**

1. **API Layer** (`app/api/`): HTTP concerns, request/response handling
2. **Service Layer** (`app/services/`): Business logic, orchestration
3. **Data Layer** (`app/models/`): Database operations, ORM

**Alternative Considered:**

- **Domain-Driven Design (DDD)**: Too heavy for this MVP
- **Monolithic Service**: Would work but harder to maintain

---

## Database Design

### Graph Representation: Adjacency List

**Schema:**

```sql
nodes (id, name, description, created_at, updated_at)
edges (id, source_node_id, target_node_id, label, created_at)
```

**Rationale:**

- **Flexible**: Easy to add/remove nodes and edges
- **Efficient**: Optimized for graph traversal queries
- **Standard**: Well-understood pattern for directed graphs
- **Scalable**: Works well with millions of nodes

**Alternatives Considered:**

1. **Adjacency Matrix**:
   - ❌ Memory inefficient for sparse graphs
   - ❌ Hard to add nodes dynamically
2. **Edge List Only**:
   - ❌ No place for node metadata
   - ❌ Harder to query node properties

3. **Nested Set Model**:
   - ❌ Only works for trees, not graphs
   - ❌ Complex updates

### Indexes

**Created Indexes:**

```sql
-- On nodes table
CREATE INDEX ix_nodes_id ON nodes(id);
CREATE INDEX ix_nodes_name ON nodes(name);

-- On edges table
CREATE INDEX idx_source_node ON edges(source_node_id);
CREATE INDEX idx_target_node ON edges(target_node_id);
CREATE INDEX idx_source_target ON edges(source_node_id, target_node_id);
```

**Rationale:**

- `source_node_id` index: Critical for graph traversal (starting point)
- `target_node_id` index: Supports reverse lookups if needed
- Composite index: Faster for finding specific edges
- `name` index: Common search pattern for nodes

---

## The Recursive Query Strategy

### Chosen: WITH RECURSIVE Common Table Expression (CTE)

**Implementation:**

```sql
WITH RECURSIVE node_tree AS (
                -- Base case: direct children of the source node
                SELECT
                    e.target_node_id as node_id,
                    1 as depth,
                    CAST(CONCAT(',', :source_node_id, ',', e.target_node_id, ',') AS CHAR(4000)) as path
                FROM edges e
                WHERE e.source_node_id = :source_node_id

                UNION ALL

                -- Recursive case: children of previously found nodes
                -- Only visit nodes not already in the current path (cycle detection)
                SELECT
                    e.target_node_id as node_id,
                    nt.depth + 1 as depth,
                    CONCAT(nt.path, e.target_node_id, ',') as path
                FROM edges e
                INNER JOIN node_tree nt ON e.source_node_id = nt.node_id
                WHERE nt.path NOT LIKE CONCAT('%,', e.target_node_id, ',%')
                  AND CHAR_LENGTH(nt.path) < 3900  -- Stop before exceeding path column limit
                  AND nt.depth < 100  -- Safety limit for very deep graphs
            )
            -- Get nodes with their minimum depth
            SELECT
                n.id,
                n.name,
                MIN(nt.depth) as depth
            FROM nodes n
            INNER JOIN node_tree nt ON n.id = nt.node_id
            GROUP BY n.id, n.name
            ORDER BY depth, n.id;
```

**Cycle Detection Strategy:**

The query uses path tracking to detect and avoid cycles:

- Each row carries a `path` column containing all visited node IDs (e.g., `,1,3,5,`)
- Before visiting a node, the query checks if it's already in the path using `NOT LIKE`
- The path is cast to `CHAR(4000)` to accommodate deep traversals
- This prevents infinite loops immediately when a cycle is encountered

**Path Length Limitation:**

The path tracking approach has an inherent limitation: the path string can only hold ~4000 characters.

| Node ID Size | Approx. Max Path Depth |
| ------------ | ---------------------- |
| 1-9          | ~1300 nodes            |
| 10-99        | ~800 nodes             |
| 100-999      | ~570 nodes             |
| 1000-9999    | ~440 nodes             |

**Trade-off:**

- The query stops traversal at `CHAR_LENGTH(path) < 3900` to prevent overflow errors
- For paths exceeding this limit, traversal stops gracefully (no error, but incomplete results)
- This is acceptable for most real-world graphs where paths rarely exceed 100 nodes
- If deeper traversal is required, alternatives include:
  - Increase `CHAR(4000)` limit (MySQL row size max ~65KB)
  - Use application-level BFS with batched queries
  - Store visited nodes in a temporary table instead of a string

**Advantages:**

- ✅ **Single Query**: No N+1 query problems
- ✅ **Database-Level**: Leverages MySQL's query optimizer
- ✅ **Efficient**: Much faster than application-level recursion
- ✅ **Memory Efficient**: Streaming results
- ✅ **True Cycle Detection**: Path tracking stops cycles immediately (not just depth limiting)

**Performance Characteristics:**

- Time Complexity: O(V + E) where V = vertices, E = edges
- Space Complexity: O(V) for result set
- Scales well to graphs with 100K+ nodes

**Alternatives Considered:**

1. **Application-Level BFS/DFS**:

   ```python
   # Pseudocode
   visited = set()
   queue = [start_node]
   while queue:
       node = queue.pop(0)
       for child in node.children:
           if child not in visited:
               queue.append(child)
   ```

   - ❌ Multiple database queries (N+1 problem)
   - ❌ Slow for deep/wide graphs
   - ❌ More memory usage
   - ✅ Easier to understand

2. **Closure Table**:

   ```sql
   CREATE TABLE node_closure (
       ancestor_id INT,
       descendant_id INT,
       depth INT
   );
   ```

   - ✅ O(1) query time
   - ❌ O(V²) space complexity
   - ❌ Complex updates
   - ❌ Not suitable for frequently changing graphs

3. **Path Enumeration**:

   ```sql
   CREATE TABLE nodes (
       id INT,
       path VARCHAR(255)  -- e.g., "/1/2/5/"
   );
   ```

   - ✅ Fast queries with LIKE
   - ❌ Limited depth
   - ❌ Complex to maintain
   - ❌ Doesn't work for DAGs (multiple paths)

**Why Recursive CTE Wins:**
For this use case (read-heavy, dynamic graph, multiple paths), recursive CTE provides the best balance of:

- Query performance
- Storage efficiency
- Maintenance simplicity
- Flexibility

---

## Technology Choices

### FastAPI

**Chosen for:**

- ✅ Modern Python (3.11+) with type hints
- ✅ Automatic API documentation (OpenAPI/Swagger)
- ✅ Native async/await support
- ✅ Excellent performance
- ✅ Pydantic validation built-in

**Alternatives:**

- Flask: Older, synchronous, less features
- Django: Too heavy for a focused API
- Express.js: Would require JavaScript

### SQLAlchemy 2.0 (Async)

**Chosen for:**

- ✅ Mature ORM with async support
- ✅ Type safety with mypy
- ✅ Migration support (Alembic)
- ✅ Connection pooling
- ✅ Raw SQL support for complex queries

**Alternatives:**

- Django ORM: Tied to Django framework
- Tortoise ORM: Less mature
- Raw SQL: No ORM benefits

### MySQL 8.0

**Chosen for:**

- ✅ Native recursive CTE support (since 8.0)
- ✅ Excellent performance for hierarchical queries
- ✅ ACID compliance
- ✅ Well-known and widely deployed

**Alternatives:**

- PostgreSQL: Equally good, similar CTE support
- MongoDB: Not suitable for graph traversal
- Neo4j: Overkill for this MVP, learning curve

### Pydantic v2

**Chosen for:**

- ✅ Request/response validation
- ✅ Type safety
- ✅ Automatic JSON serialization
- ✅ Environment variable management

---

## Design Patterns

### 1. Dependency Injection

```python
async def get_connected_nodes(
    node_id: int,
    db: AsyncSession = Depends(get_db)  # Injected
):
    ...
```

**Benefits:**

- Easy testing (can inject mock DB)
- Loose coupling
- FastAPI native pattern

### 2. Repository Pattern (via Service Layer)

```python
class GraphService:
    @staticmethod
    async def get_connected_nodes(db, node_id):
        # All data access logic here
        ...
```

**Benefits:**

- Data access logic centralized
- Easy to change database implementation
- Testable without database

### 3. DTO Pattern (Pydantic Schemas)

```python
class NodeResponse(BaseModel):
    id: int
    name: str
    ...
```

**Benefits:**

- Input validation
- Output serialization
- API contract definition

---

## Error Handling Strategy

### HTTP Status Codes

- `200 OK`: Success with data
- `201 Created`: Resource created
- `204 No Content`: Success, no data
- `404 Not Found`: Resource doesn't exist
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Unexpected errors

### Error Response Format

```python
raise HTTPException(
    status_code=404,
    detail="Node with id X not found"
)
```

**Rationale:**

- Consistent error format
- Client can handle errors appropriately
- Logged for debugging

---

## Scalability Considerations

### Current Implementation

- Connection pooling: 5 connections, 10 overflow
- Async I/O: Non-blocking operations
- Indexed queries: O(log n) lookups
- Single query traversal: No N+1 problems

### Future Optimizations (Not in MVP)

1. **Caching Layer**:

   ```
   Redis → Cache frequently accessed paths
   TTL: 5 minutes
   Invalidate on graph changes
   ```

2. **Read Replicas**:

   ```
   Write → Master DB
   Read → Replica DBs (round-robin)
   ```

3. **Materialized Paths**:

   ```
   Precompute common paths
   Update on graph changes
   Trade space for speed
   ```

4. **Horizontal Partitioning**:
   ```
   Partition by node ID range
   Shard across multiple databases
   ```

---

## Testing Strategy

### What's Tested

- API endpoints (integration tests)
- Request/response validation
- Error cases
- Database connectivity

### What's Not Tested (MVP)

- ❌ Performance/load testing
- ❌ Unit tests for services
- ❌ End-to-end tests
- ❌ Security testing

**Rationale:** Time-boxed MVP focuses on core functionality.

---

## Security Considerations

### Not Implemented (MVP)

- ❌ Authentication/Authorization
- ❌ Rate limiting
- ❌ SQL injection protection (handled by ORM)
- ❌ CORS restrictions (wide open)

### Would Add for Production

- ✅ JWT authentication
- ✅ Role-based access control
- ✅ API key management
- ✅ Request rate limiting
- ✅ Input sanitization
- ✅ HTTPS enforcement
- ✅ Security headers

---

## Configuration Management

### Environment-Based

```python
class Settings(BaseSettings):
    DATABASE_URL: str
    DEBUG: bool = False
    ...
```

**Benefits:**

- Different configs for dev/test/prod
- No secrets in code
- Easy to change without rebuild

---

## Docker Strategy

### Multi-Container Setup

```yaml
services:
  db: # MySQL
  api: # FastAPI
```

**Benefits:**

- Isolated environments
- Easy local development
- Production-like setup
- One-command startup

### Container Communication

- Docker network bridge
- Service name DNS resolution
- Health checks for dependencies

---

## Trade-offs Summary

| Decision      | Benefit           | Trade-off               |
| ------------- | ----------------- | ----------------------- |
| Recursive CTE | Fast single query | Complex SQL             |
| Async FastAPI | High concurrency  | More complex code       |
| SQLAlchemy    | ORM benefits      | Overhead vs raw SQL     |
| MySQL 8.0     | Native recursion  | Version requirement     |
| No auth       | Faster MVP        | Not production-ready    |
| No caching    | Simpler code      | Slower repeated queries |
| Docker        | Easy setup        | Resource overhead       |

---

## Conclusion

This architecture prioritizes:

1. **Correctness**: Single-query solution that works
2. **Maintainability**: Clean code, clear structure
3. **Performance**: Efficient database queries
4. **Pragmatism**: MVP features, not over-engineered

The design is production-ready with known gaps (auth, caching, monitoring) that can be added incrementally based on requirements.
