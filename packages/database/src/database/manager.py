import os
from typing import Any

import kuzu
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    primary_db_path: str
    public_db_path: str | None = None
    buffer_pool_size: int = 1024 * 1024 * 1024  # 1GB default


class DatabaseManager:
    """
    Manages connections to Kùzu graph databases.
    Supports a primary (private) database and an optional attached (public) database.
    Designed to be cloud-agnostic and work in containerized environments.
    """

    def __init__(self, config: DatabaseConfig | None = None):
        self.config = config or self._load_config_from_env()
        self.db = None
        self.conn = None

        self._initialize_database()

    def _load_config_from_env(self) -> DatabaseConfig:
        """Loads configuration from environment variables."""
        return DatabaseConfig(
            primary_db_path=os.getenv("KUZU_DB_PATH", "./interlock.kuzu"),
            public_db_path=os.getenv("KUZU_PUBLIC_DB_PATH"),
            buffer_pool_size=int(
                os.getenv("KUZU_BUFFER_POOL_SIZE", 1024 * 1024 * 1024)
            ),
        )

    def _initialize_database(self):
        """Initializes the Kùzu database connection."""
        # Ensure the directory exists if we are in read-write mode (default for primary)
        os.makedirs(
            os.path.dirname(os.path.abspath(self.config.primary_db_path)), exist_ok=True
        )

        try:
            # Initialize the primary database
            self.db = kuzu.Database(
                self.config.primary_db_path,
                buffer_pool_size=self.config.buffer_pool_size,
            )
            self.conn = kuzu.Connection(self.db)

            # Note: For federation, we currently use a dual-connection strategy
            # (managed by this class) rather than attaching at the engine level,
            # to ensure compatibility across different environment setups.

        except Exception as e:
            print(f"Failed to initialize database: {e}")
            raise

    def get_public_connection(self):
        """Returns a connection to the public database if configured."""
        if self.config.public_db_path:
            return kuzu.Connection(
                kuzu.Database(self.config.public_db_path, read_only=True)
            )
        return None

    def execute(self, query: str, parameters: dict[str, Any] | None = None) -> Any:
        """Executes a Cypher query against the primary database."""
        if not self.conn:
            raise RuntimeError("Database not initialized")
        return self.conn.execute(query, parameters or {})

    def query_public_reference(self, public_id: str) -> Any:
        """
        Example federated query helper.
        This manually cross-references.
        """
        if not self.config.public_db_path:
            raise RuntimeError("No Public DB configured")

        # Open a temporary connection or use a cached one
        # Ideally, cache this connection in __init__
        public_conn = self.get_public_connection()
        return public_conn.execute(
            "MATCH (n) WHERE n.id = $id RETURN n", {"id": public_id}
        )

    def close(self):
        """
        Closes the database connection?
        Kùzu handles this automatically via RAII usually.
        """
        pass
