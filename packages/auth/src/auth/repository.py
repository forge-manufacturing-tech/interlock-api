from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from database.manager import DatabaseManager

from .security import (
    create_access_token,
    get_api_key_last4,
    hash_api_key,
    hash_password,
    verify_password,
)


_AUTH_DDL: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id              TEXT PRIMARY KEY,
        email           TEXT NOT NULL UNIQUE,
        name            TEXT,
        password_hash   TEXT NOT NULL,
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS api_keys (
        id              TEXT PRIMARY KEY,
        user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        key_hash        TEXT NOT NULL UNIQUE,
        last4           TEXT NOT NULL,
        name            TEXT NOT NULL,
        created_at      TEXT NOT NULL DEFAULT (datetime('now')),
        revoked_at      TEXT,
        last_used_at    TEXT
    )
    """,
]


def initialize_auth_schema(db: DatabaseManager) -> None:
    for stmt in _AUTH_DDL:
        db.execute(stmt)
    db.commit()


class AuthRepository:
    def __init__(self, db: DatabaseManager | None = None):
        self.db = db or DatabaseManager()
        initialize_auth_schema(self.db)

    def create_user(self, email: str, password: str, name: str | None = None) -> dict:
        existing = self.db.fetch_one(
            "SELECT id FROM users WHERE email = ?", (email,)
        )
        if existing:
            raise ValueError("A user with this email already exists")

        user_id = uuid4()
        pw_hash = hash_password(password)
        now = datetime.now(timezone.utc).isoformat()

        self.db.execute(
            """
            INSERT INTO users (id, email, name, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(user_id), email, name, pw_hash, now),
        )
        self.db.commit()

        token = create_access_token(user_id, email)
        return {
            "user": {
                "id": user_id,
                "email": email,
                "name": name,
                "created_at": now,
            },
            "access_token": token,
        }

    def authenticate_user(self, email: str, password: str) -> dict:
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE email = ?", (email,)
        )
        if not row:
            raise ValueError("Invalid email or password")

        if not verify_password(password, row["password_hash"]):
            raise ValueError("Invalid email or password")

        user_id = UUID(row["id"])
        token = create_access_token(user_id, row["email"])
        return {
            "user": {
                "id": user_id,
                "email": row["email"],
                "name": row["name"],
                "created_at": row["created_at"],
            },
            "access_token": token,
        }

    def get_user_by_id(self, user_id: UUID) -> dict | None:
        row = self.db.fetch_one(
            "SELECT id, email, name, created_at FROM users WHERE id = ?",
            (str(user_id),),
        )
        if not row:
            return None
        return {
            "id": UUID(row["id"]),
            "email": row["email"],
            "name": row["name"],
            "created_at": row["created_at"],
        }

    def get_user_by_api_key(self, api_key: str) -> dict | None:
        key_hash = hash_api_key(api_key)
        row = self.db.fetch_one(
            """
            SELECT u.id, u.email, u.name, u.created_at, ak.id as key_id
            FROM api_keys ak
            JOIN users u ON ak.user_id = u.id
            WHERE ak.key_hash = ? AND ak.revoked_at IS NULL
            """,
            (key_hash,),
        )
        if not row:
            return None

        now = datetime.now(timezone.utc).isoformat()
        self.db.execute(
            "UPDATE api_keys SET last_used_at = ? WHERE id = ?",
            (now, row["key_id"]),
        )
        self.db.commit()

        return {
            "id": UUID(row["id"]),
            "email": row["email"],
            "name": row["name"],
            "created_at": row["created_at"],
        }

    def create_api_key(self, user_id: UUID, name: str) -> dict:
        from .security import generate_api_key

        raw_key = generate_api_key()
        key_hash = hash_api_key(raw_key)
        last4 = get_api_key_last4(raw_key)
        key_id = uuid4()
        now = datetime.now(timezone.utc).isoformat()

        self.db.execute(
            """
            INSERT INTO api_keys (id, user_id, key_hash, last4, name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (str(key_id), str(user_id), key_hash, last4, name, now),
        )
        self.db.commit()

        return {
            "id": key_id,
            "name": name,
            "key": raw_key,
            "last4": last4,
            "created_at": now,
        }

    def list_api_keys(self, user_id: UUID) -> list[dict]:
        rows = self.db.fetch_all(
            """
            SELECT id, name, last4, created_at, revoked_at, last_used_at
            FROM api_keys
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (str(user_id),),
        )
        return [
            {
                "id": UUID(r["id"]),
                "name": r["name"],
                "last4": r["last4"],
                "created_at": r["created_at"],
                "revoked_at": r["revoked_at"],
                "last_used_at": r["last_used_at"],
            }
            for r in rows
        ]

    def revoke_api_key(self, key_id: UUID, user_id: UUID) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        cur = self.db.execute(
            """
            UPDATE api_keys SET revoked_at = ?
            WHERE id = ? AND user_id = ? AND revoked_at IS NULL
            """,
            (now, str(key_id), str(user_id)),
        )
        self.db.commit()
        return cur.rowcount > 0
