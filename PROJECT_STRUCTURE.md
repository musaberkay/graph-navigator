# Project Structure

```
graph-navigator/
├── 📄 README.md                      # Comprehensive project documentation
├── 📄 QUICKSTART.md                  # Quick start guide
├── 📄 docker-compose.yml             # Docker orchestration
├── 📄 Dockerfile                     # Application container definition
├── 📄 requirements.txt               # Python dependencies
├── 📄 .env.example                   # Environment variables template
├── 📄 .gitignore                     # Git ignore rules
├── 📄 Makefile                       # Convenience commands
├── 📄 pytest.ini                     # Pytest configuration
├── 📄 alembic.ini                    # Alembic configuration
│
├── 📁 app/                           # Main application package
│   ├── __init__.py
│   ├── main.py                       # FastAPI application entry point
│   │
│   ├── 📁 api/                       # API endpoints (controllers)
│   │   ├── __init__.py
│   │   ├── nodes.py                  # Node endpoints including /connected
│   │   ├── edges.py                  # Edge endpoints
│   │   └── health.py                 # Health check endpoint
│   │
│   ├── 📁 core/                      # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py                 # Application settings
│   │   └── database.py               # Database connection & session
│   │
│   ├── 📁 models/                    # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   └── graph.py                  # Node and Edge models
│   │
│   ├── 📁 schemas/                   # Pydantic schemas
│   │   ├── __init__.py
│   │   └── graph.py                  # Request/response schemas
│   │
│   └── 📁 services/                  # Business logic layer
│       ├── __init__.py
│       └── graph_service.py          # Graph operations & recursive query
│
├── 📁 alembic/                       # Database migrations
│   ├── env.py                        # Migration environment
│   ├── script.py.mako               # Migration template
│   └── versions/
│       └── 001_initial_schema.py     # Initial database schema
│
├── 📁 scripts/                       # Utility scripts
│   ├── __init__.py
│   └── seed_database.py              # Database seeding script
│
└── 📁 tests/                         # Test suite
    ├── __init__.py
    ├── conftest.py                   # Test configuration & fixtures
    └── test_api.py                   # API endpoint tests
```

## Key Files Explained

### Application Core

- **`app/main.py`**: FastAPI application setup, middleware, router registration
- **`app/core/config.py`**: Environment-based configuration using Pydantic
- **`app/core/database.py`**: SQLAlchemy async engine and session management

### Data Layer

- **`app/models/graph.py`**: Node and Edge ORM models with relationships
- **`app/schemas/graph.py`**: Pydantic models for validation and serialization

### Business Logic

- **`app/services/graph_service.py`**:
  - Core graph operations
  - **Recursive traversal query** (the heart of the challenge)
  - Single SQL query using `WITH RECURSIVE` CTE

### API Layer

- **`app/api/nodes.py`**:
  - `GET /nodes/{node_id}/connected` - **Main connectivity endpoint**
  - `GET /nodes/{node_id}` - Get single node
  - `GET /nodes` - List nodes (paginated)
  - `POST /nodes` - Create node
  - `DELETE /nodes/{node_id}` - Delete node

- **`app/api/edges.py`**:
  - `POST /edges` - Create edge between nodes

- **`app/api/health.py`**:
  - `GET /health` - Health check with DB connectivity test

### Database

- **`alembic/versions/001_initial_schema.py`**: Initial schema migration
  - Creates `nodes` table
  - Creates `edges` table with foreign keys
  - Adds indexes for performance

### DevOps

- **`docker-compose.yml`**: Orchestrates MySQL and FastAPI containers
- **`Dockerfile`**: Multi-stage Python container
- **`scripts/seed_database.py`**: Creates 6-level deep graph with 24+ nodes

### Testing

- **`tests/conftest.py`**: Pytest fixtures and test database setup
- **`tests/test_api.py`**: API endpoint tests

## Data Flow

```
HTTP Request
    ↓
FastAPI Router (app/api/nodes.py)
    ↓
Dependency Injection (get_db)
    ↓
Service Layer (app/services/graph_service.py)
    ↓
Database Query (WITH RECURSIVE CTE)
    ↓
SQLAlchemy ORM (app/models/graph.py)
    ↓
MySQL Database
    ↓
Response via Pydantic Schema (app/schemas/graph.py)
    ↓
JSON Response
```

## The Recursive Query

Located in `app/services/graph_service.py::get_connected_nodes()`:

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

This single query efficiently traverses the entire graph structure.
