# Database Package

This package manages the relational database connection using **PostgreSQL** (via `psycopg2`).

## Architecture

The system uses a standard relational database model to store the manufacturing graph.
- **Connection**: Managed by `DatabaseManager`.
- **Schema**: Defined in `src/database/schema.py`.
- **Migrations**: Currently, the system uses an **idempotent initialization** strategy. At startup, it runs `CREATE TABLE IF NOT EXISTS` statements for all tables. It does *not* currently support complex schema migrations (e.g., column renames) automatically; these must be handled manually or by resetting the database in development.

## Configuration

The database is configured via Environment Variables:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | Full PostgreSQL connection string (libpq format). | None (Required) |

## Usage

```python
from database.manager import DatabaseManager

db = DatabaseManager()

# Execute raw SQL
db.execute("SELECT * FROM part_nodes")

# Connection management is handled automatically.
```
