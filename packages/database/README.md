# Database Package

This package manages the graph database connection using **Kùzu**.

## Architecture

This package supports a **Dual-Graph Federation** model:
1.  **Primary Database (Private)**: Read/Write access. Stores user-specific data.
2.  **Referenced Database (Public)**: Read-Only access. Stores shared industry standards or public datasets.

## Configuration

The database can be configured via Environment Variables:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `KUZU_DB_PATH` | Path to the private database directory/file. | `./interlock.kuzu` |
| `KUZU_PUBLIC_DB_PATH` | Path to the public read-only database. | None |
| `KUZU_BUFFER_POOL_SIZE` | Memory buffer for the database (bytes). | 1073741824 (1GB) |

## Cloud Deployment (GCP / Kubernetes)

Since Kùzu uses the filesystem, persistence depends on where the `KUZU_DB_PATH` points.

### Deployment options:
1.  **Cloud Run + Cloud Storage FUSE**: 
    - Mount a GCS bucket to `/mnt/gcs_data`.
    - Set `KUZU_DB_PATH=/mnt/gcs_data/private.kuzu`.
2.  **Cloud Run + Filestore (NFS)**:
    - Mount an NFS share to `/data`.
    - Set `KUZU_DB_PATH=/data/private.kuzu`.
3.  **Kubernetes (GKE)**:
    - Use a `PersistentVolumeClaim` (PVC) mounted to the pod.
    - Point `KUZU_DB_PATH` to the mount path.

## Usage

```python
from database.manager import DatabaseManager

db = DatabaseManager()

# Run a query on the private graph
results = db.execute("MATCH (a:Node) RETURN a")

# Access the public graph separately (Application-Side Federation)
public_conn = db.get_public_connection()
if public_conn:
    standards = public_conn.execute("MATCH (s:Standard) RETURN s")
```
