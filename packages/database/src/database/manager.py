import os
from typing import Any

import psycopg2
import psycopg2.extensions
import psycopg2.extras
from pydantic import BaseModel
from sqlalchemy import Engine
from sqlmodel import Session, create_engine


class DatabaseConfig(BaseModel):
    database_url: str


class DatabaseManager:
    """
    Manages connections to PostgreSQL databases.
    """

    def __init__(self, config: DatabaseConfig | None = None):
        self.config = config or self._load_config_from_env()
        self._conn: psycopg2.extensions.connection | None = None
        self._engine: Engine = create_engine(self.config.database_url)
        self._initialize_database()

    def _load_config_from_env(self) -> DatabaseConfig:
        url = os.getenv("DATABASE_URL")
        if not url:
            raise RuntimeError("DATABASE_URL environment variable is required")
        return DatabaseConfig(database_url=url)

    def _initialize_database(self) -> None:
        try:
            # psycopg2 doesn't understand "cockroachdb://" protocol, but it works with CockroachDB
            # as if it were PostgreSQL if we use "postgresql://" or the connection string.
            psycopg_url = self.config.database_url
            if psycopg_url.startswith("cockroachdb://"):
                psycopg_url = "postgresql://" + psycopg_url[len("cockroachdb://") :]

            self._conn = psycopg2.connect(
                psycopg_url,
                cursor_factory=psycopg2.extras.RealDictCursor,
            )
            self._conn.autocommit = False
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            raise

    @property
    def connection(self) -> psycopg2.extensions.connection:
        if self._conn is None or self._conn.closed:
            self._initialize_database()
        return self._conn

    @property
    def engine(self) -> Engine:
        return self._engine

    @property
    def session(self) -> Session:
        """Returns a new SQLModel Session."""
        return Session(self._engine)

    def execute(
        self,
        query: str,
        parameters: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> psycopg2.extensions.cursor:
        conn = self.connection
        cur = conn.cursor()
        cur.execute(query, parameters or None)
        return cur

    def execute_many(
        self,
        query: str,
        seq_of_parameters: list[tuple[Any, ...] | dict[str, Any]],
    ) -> psycopg2.extensions.cursor:
        conn = self.connection
        cur = conn.cursor()
        cur.executemany(query, seq_of_parameters)
        return cur

    def fetch_one(
        self,
        query: str,
        parameters: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> dict | None:
        cursor = self.execute(query, parameters)
        return cursor.fetchone()

    def fetch_all(
        self,
        query: str,
        parameters: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> list[dict]:
        cursor = self.execute(query, parameters)
        return cursor.fetchall()

    def commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()

    def close(self) -> None:
        if self._conn is not None and not self._conn.closed:
            self._conn.close()
            self._conn = None

    def execute_ddl(self, query: str) -> None:
        conn = self.connection
        if conn.status != 0:
            conn.rollback()
        old_autocommit = conn.autocommit
        conn.autocommit = True
        try:
            cur = conn.cursor()
            cur.execute(query)
            cur.close()
        finally:
            conn.autocommit = old_autocommit
