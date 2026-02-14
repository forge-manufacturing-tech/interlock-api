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
        role            TEXT NOT NULL DEFAULT 'member',
        ai_enabled      BOOLEAN NOT NULL DEFAULT FALSE,
        created_at      TEXT NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS api_keys (
        id              TEXT PRIMARY KEY,
        user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        key_hash        TEXT NOT NULL UNIQUE,
        last4           TEXT NOT NULL,
        name            TEXT NOT NULL,
        created_at      TEXT NOT NULL DEFAULT NOW(),
        revoked_at      TEXT,
        last_used_at    TEXT
    )
    """,
]

_MIGRATIONS: list[str] = [
    "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'member'",
    "ALTER TABLE users ADD COLUMN ai_enabled BOOLEAN NOT NULL DEFAULT FALSE",
]


def initialize_auth_schema(db: DatabaseManager) -> None:
    for stmt in _AUTH_DDL:
        try:
            db.execute_ddl(stmt)
        except Exception:
            pass

    for migration in _MIGRATIONS:
        try:
            db.execute_ddl(migration)
        except Exception:
            pass

    try:
        first_user = db.fetch_one(
            "SELECT id, role FROM users ORDER BY created_at ASC LIMIT 1"
        )
        if first_user and first_user.get("role") == "member":
            db.execute(
                "UPDATE users SET role = 'admin', ai_enabled = TRUE WHERE id = %s",
                (first_user["id"],),
            )
        db.commit()
    except Exception:
        db.rollback()


class AuthRepository:
    def __init__(self, db: DatabaseManager | None = None):
        self.db = db or DatabaseManager()
        initialize_auth_schema(self.db)

    def _is_first_user(self) -> bool:
        row = self.db.fetch_one("SELECT COUNT(*) as cnt FROM users")
        return row is not None and row["cnt"] == 0

    def create_user(self, email: str, password: str, name: str | None = None) -> dict:
        existing = self.db.fetch_one(
            "SELECT id FROM users WHERE email = %s", (email,)
        )
        if existing:
            raise ValueError("A user with this email already exists")

        is_first = self._is_first_user()
        role = "admin" if is_first else "member"
        ai_enabled = True if is_first else False

        user_id = uuid4()
        pw_hash = hash_password(password)
        now = datetime.now(timezone.utc).isoformat()

        self.db.execute(
            """
            INSERT INTO users (id, email, name, password_hash, role, ai_enabled, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (str(user_id), email, name, pw_hash, role, ai_enabled, now),
        )
        self.db.commit()

        token = create_access_token(user_id, email)
        return {
            "user": {
                "id": user_id,
                "email": email,
                "name": name,
                "role": role,
                "ai_enabled": ai_enabled,
                "created_at": now,
            },
            "access_token": token,
        }

    def authenticate_user(self, email: str, password: str) -> dict:
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE email = %s", (email,)
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
                "role": row.get("role", "member"),
                "ai_enabled": row.get("ai_enabled", False),
                "created_at": row["created_at"],
            },
            "access_token": token,
        }

    def get_user_by_id(self, user_id: UUID) -> dict | None:
        row = self.db.fetch_one(
            "SELECT id, email, name, role, ai_enabled, created_at FROM users WHERE id = %s",
            (str(user_id),),
        )
        if not row:
            return None
        return {
            "id": UUID(row["id"]),
            "email": row["email"],
            "name": row["name"],
            "role": row.get("role", "member"),
            "ai_enabled": row.get("ai_enabled", False),
            "created_at": row["created_at"],
        }

    def get_user_by_api_key(self, api_key: str) -> dict | None:
        key_hash = hash_api_key(api_key)
        row = self.db.fetch_one(
            """
            SELECT u.id, u.email, u.name, u.role, u.ai_enabled, u.created_at, ak.id as key_id
            FROM api_keys ak
            JOIN users u ON ak.user_id = u.id
            WHERE ak.key_hash = %s AND ak.revoked_at IS NULL
            """,
            (key_hash,),
        )
        if not row:
            return None

        now = datetime.now(timezone.utc).isoformat()
        self.db.execute(
            "UPDATE api_keys SET last_used_at = %s WHERE id = %s",
            (now, row["key_id"]),
        )
        self.db.commit()

        return {
            "id": UUID(row["id"]),
            "email": row["email"],
            "name": row["name"],
            "role": row.get("role", "member"),
            "ai_enabled": row.get("ai_enabled", False),
            "created_at": row["created_at"],
        }

    def list_users(self) -> list[dict]:
        rows = self.db.fetch_all(
            "SELECT id, email, name, role, ai_enabled, created_at FROM users ORDER BY created_at ASC"
        )
        return [
            {
                "id": UUID(r["id"]),
                "email": r["email"],
                "name": r["name"],
                "role": r.get("role", "member"),
                "ai_enabled": r.get("ai_enabled", False),
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    def update_user(self, user_id: UUID, ai_enabled: bool | None = None, role: str | None = None) -> dict | None:
        updates = []
        params: list = []
        if ai_enabled is not None:
            updates.append("ai_enabled = %s")
            params.append(ai_enabled)
        if role is not None:
            if role not in ("admin", "member"):
                raise ValueError("Role must be 'admin' or 'member'")
            updates.append("role = %s")
            params.append(role)
        if not updates:
            return self.get_user_by_id(user_id)

        params.append(str(user_id))
        self.db.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id = %s",
            tuple(params),
        )
        self.db.commit()
        return self.get_user_by_id(user_id)

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
            VALUES (%s, %s, %s, %s, %s, %s)
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
            WHERE user_id = %s
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
            UPDATE api_keys SET revoked_at = %s
            WHERE id = %s AND user_id = %s AND revoked_at IS NULL
            """,
            (now, str(key_id), str(user_id)),
        )
        self.db.commit()
        return cur.rowcount > 0
