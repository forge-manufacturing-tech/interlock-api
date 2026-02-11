import os
import sqlite3
from typing import Any

from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    primary_db_path: str
    read_only_db_path: str | None = None


class DatabaseManager:
    """
    Manages connections to SQLite databases.

    Supports a primary (read-write) database and an optional attached
    read-only database.  SQLite files work on local filesystems and on
    GCS FUSE / NFS mounts in production — no external server required.
    """

    def __init__(self, config: DatabaseConfig | None = None):
        self.config = config or self._load_config_from_env()
        self._conn: sqlite3.Connection | None = None

        self._initialize_database()

    # -- Configuration -----------------------------------------------------------

    def _load_config_from_env(self) -> DatabaseConfig:
        """Loads configuration from environment variables."""
        return DatabaseConfig(
            primary_db_path=os.getenv("DB_PATH", "./data/interlock.db"),
            read_only_db_path=os.getenv("DB_READ_ONLY_PATH"),
        )

    # -- Lifecycle ---------------------------------------------------------------

    def _initialize_database(self) -> None:
        """Creates the database file (and parent dirs) and opens a connection."""
        os.makedirs(
            os.path.dirname(os.path.abspath(self.config.primary_db_path)),
            exist_ok=True,
        )

        try:
            self._conn = sqlite3.connect(
                self.config.primary_db_path,
                check_same_thread=False,
            )
            # Return rows as sqlite3.Row so columns are accessible by name.
            self._conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrent read performance.
            self._conn.execute("PRAGMA journal_mode=WAL")
            # Enable foreign key enforcement (off by default in SQLite).
            self._conn.execute("PRAGMA foreign_keys=ON")
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            raise

    @property
    def connection(self) -> sqlite3.Connection:
        """Returns the active database connection."""
        if self._conn is None:
            raise RuntimeError("Database not initialized")
        return self._conn

    def get_read_only_connection(self) -> sqlite3.Connection | None:
        """Returns a read-only connection to the secondary database, if configured."""
        if self.config.read_only_db_path:
            conn = sqlite3.connect(
                f"file:{self.config.read_only_db_path}?mode=ro",
                uri=True,
                check_same_thread=False,
            )
            conn.row_factory = sqlite3.Row
            return conn
        return None

    # -- Query helpers -----------------------------------------------------------

    def execute(
        self,
        query: str,
        parameters: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> sqlite3.Cursor:
        """Executes a SQL statement against the primary database."""
        conn = self.connection
        return conn.execute(query, parameters or ())

    def execute_many(
        self,
        query: str,
        seq_of_parameters: list[tuple[Any, ...] | dict[str, Any]],
    ) -> sqlite3.Cursor:
        """Executes a SQL statement against many parameter sets."""
        conn = self.connection
        return conn.executemany(query, seq_of_parameters)

    def fetch_one(
        self,
        query: str,
        parameters: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> sqlite3.Row | None:
        """Executes a query and returns the first row, or None."""
        cursor = self.execute(query, parameters)
        return cursor.fetchone()

    def fetch_all(
        self,
        query: str,
        parameters: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> list[sqlite3.Row]:
        """Executes a query and returns all rows."""
        cursor = self.execute(query, parameters)
        return cursor.fetchall()

    def commit(self) -> None:
        """Commits the current transaction."""
        self.connection.commit()

    # -- Cleanup -----------------------------------------------------------------

    def close(self) -> None:
        """Closes the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
