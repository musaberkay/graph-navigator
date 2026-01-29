# Graph Navigator Service

A production-ready FastAPI service for managing and traversing directed graph structures stored in MySQL.

## 🏗️ Architecture Overview

This project follows a layered architecture with clear separation of concerns:

```
graph-navigator/
├── app/
│   ├── api/              # API layer - endpoints and routing
│   ├── core/             # Core configuration and dependencies
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic models for validation
│   ├── services/         # Business logic layer
│   └── main.py           # Application entry point
├── scripts/              # Utility scripts (seeding, migrations)
├── tests/                # Test suite
├── alembic/              # Database migrations
├── docker-compose.yml    # Docker orchestration
├── Dockerfile            # Application container
└── README.md
```

### Key Design Decisions

1. **Layered Architecture**:
   - API layer handles HTTP concerns
   - Service layer contains business logic
   - Models represent the database schema
   - Schemas handle validation and serialization

2. **Database Strategy**:
   - Using MySQL 8.0 for native support of recursive CTEs
   - Single optimized query using `WITH RECURSIVE` for graph traversal
   - Proper indexing on foreign keys for performance

3. **Graph Representation**:
   - Adjacency list model (node and edges tables)
   - Supports directed graphs with labeled edges
   - Scalable for large graphs

## 🚀 Quick Start

### Prerequisites

- Docker
- Docker Compose

### Running the Application

1. **Clone the repository** (or extract the zip)

2. **Start the services**:

```bash
docker-compose up --build
```

This will:

- Build the FastAPI application
- Start MySQL 8.0
- Run database migrations
- Seed the database with sample data (5+ levels deep)
- Start the API server on `http://localhost:8000`

3. **Access the API**:

- API Documentation: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc`
- Health Check: `http://localhost:8000/health`

### Testing the Connectivity Query

Once the services are running, you can verify the graph traversal:

1. **Via Swagger UI** (`http://localhost:8000/docs`):
   - Navigate to `GET /nodes/{node_id}/connected`
   - Try `node_id=1` (should return all connected nodes)

2. **Via cURL**:

```bash
curl http://localhost:8000/nodes/1/connected
```

3. **Expected Response**:

```json
{
  "source_node_id": 1,
  "connected_nodes": [
    {"id": 2, "name": "Node 2", "depth": 1},
    {"id": 3, "name": "Node 3", "depth": 1},
    {"id": 5, "name": "Node 5", "depth": 2},
    ...
  ],
  "total_connected": 15
}
```

### Sample Graph Structure

The seeded data creates a graph like this:

```
Level 0: Node 1 (Root)
         ├── Node 2
         │   ├── Node 5
         │   │   └── Node 11
         │   └── Node 6
         ├── Node 3
         │   ├── Node 7
         │   └── Node 8
         └── Node 4
             ├── Node 9
             └── Node 10
...
```

## 📊 API Endpoints

### Graph Operations

#### Get Connected Nodes

```
GET /nodes/{node_id}/connected
```

Returns all nodes reachable from the specified node via a single recursive SQL query.

**Parameters:**

- `node_id` (path, required): The starting node ID

**Response:**

```json
{
  "source_node_id": 1,
  "connected_nodes": [
    {
      "id": 2,
      "name": "Node 2",
      "depth": 1
    }
  ],
  "total_connected": 10
}
```

**Status Codes:**

- `200 OK`: Successfully retrieved connected nodes
- `404 Not Found`: Source node doesn't exist
- `500 Internal Server Error`: Database or server error

#### Get Node Details

```
GET /nodes/{node_id}
```

Retrieve information about a specific node.

#### List All Nodes

```
GET /nodes
```

List all nodes in the graph (paginated).

#### Create Node

```
POST /nodes
```

Create a new node in the graph.

#### Create Edge

```
POST /edges
```

Create a connection between two nodes.

### System Endpoints

#### Health Check

```
GET /health
```

Returns service health status and database connectivity.

## 🗄️ Database Schema

### Tables

**nodes**

- `id`: Primary key
- `name`: Node identifier/name
- `description`: Optional description
- `created_at`: Timestamp
- `updated_at`: Timestamp

**edges**

- `id`: Primary key
- `source_node_id`: Foreign key to nodes
- `target_node_id`: Foreign key to nodes
- `label`: Optional edge label
- `created_at`: Timestamp

### Recursive Query Strategy

The core traversal uses MySQL's `WITH RECURSIVE` CTE with path-based cycle detection:

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

This approach:

- ✅ Single database query (no N+1 problems)
- ✅ Efficient for deep graphs
- ✅ True cycle detection via path tracking (stops immediately when revisiting a node)
- ✅ Returns nodes in breadth-first order

## 🔧 Configuration

Configuration is managed through environment variables (see `.env` or `docker-compose.yml`):

```env
# Application
APP_NAME=graph-navigator
DEBUG=false
LOG_LEVEL=info

# Database
DATABASE_URL=mysql+asyncmy://user:password@db:3306/graphdb
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# API
API_V1_PREFIX=/api/v1
```

## 🧪 Development

### Running Tests

```bash
# With Docker
docker-compose run --rm api pytest

# Locally (requires venv)
pytest tests/ -v
```

### Database Migrations

Using Alembic for schema management:

```bash
# Create a new migration
docker-compose run --rm api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose run --rm api alembic upgrade head

# Rollback
docker-compose run --rm api alembic downgrade -1
```

### Seeding Data

```bash
# Reseed the database
docker-compose run --rm api python scripts/seed_database.py
```

## 🎯 Trade-offs and Considerations

### What's Included (MVP Scope)

✅ **Core Functionality**:

- Complete graph storage and traversal
- Single-query recursive traversal
- Production-ready error handling
- Docker containerization
- Auto-generated API docs

✅ **Code Quality**:

- Type hints throughout
- Pydantic validation
- Async/await pattern
- Structured logging
- Clean architecture

### Deliberate Simplifications

⚖️ **Authentication/Authorization**: Not implemented for MVP

- Reason: Adds complexity without demonstrating core competency
- Production: Would add JWT/OAuth2 with role-based access

⚖️ **Caching Layer**: Not implemented

- Reason: Premature optimization for initial version
- Production: Would add Redis for frequently accessed paths

⚖️ **Rate Limiting**: Not implemented

- Reason: Single-user MVP scenario
- Production: Would add middleware for API throttling

⚖️ **Advanced Graph Features**:

- No weighted edges or shortest path algorithms
- Reason: Beyond MVP scope
- Note: Cycle detection is implemented via path tracking in the recursive query
- Production: Would add weighted edges and pathfinding based on requirements

⚖️ **Monitoring/Observability**:

- Basic logging only, no APM integration
- Reason: Infrastructure concern for MVP
- Production: Would integrate Prometheus/Grafana/Sentry

### Performance Considerations

- **Connection Pooling**: Configured for moderate load
- **Query Optimization**: Indexed foreign keys, single recursive query
- **Cycle Detection**: Path tracking prevents infinite loops in cyclic graphs
- **Async IO**: FastAPI + asyncmy for non-blocking operations

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check if MySQL is ready
docker-compose logs db

# Restart services
docker-compose down
docker-compose up --build
```

### Port Already in Use

If port 8000 or 3306 is already in use:

```bash
# Edit docker-compose.yml and change the port mapping
ports:
  - "8001:8000"  # Changed from 8000:8000
```

### Fresh Start

```bash
# Clean everything and start fresh
docker-compose down -v
docker-compose up --build
```

## 📚 Technology Stack

- **Framework**: FastAPI 0.109+
- **Database**: MySQL 8.0
- **ORM**: SQLAlchemy 2.0 (async)
- **Validation**: Pydantic v2
- **Migration**: Alembic
- **Testing**: Pytest + httpx
- **Container**: Docker + Docker Compose

## 📝 License

MIT License
