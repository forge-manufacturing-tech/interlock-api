from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from database.manager import DatabaseManager
from models.chat import ChatMessage, ChatSession
from sqlmodel import col, select


class ChatRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_session(self, user_id: UUID, title: str | None = None) -> ChatSession:
        with self.db.session as session:
            chat_session = ChatSession(user_id=user_id, title=title)
            session.add(chat_session)
            session.commit()
            session.refresh(chat_session)
            return chat_session

    def list_sessions(self, user_id: UUID) -> list[ChatSession]:
        with self.db.session as session:
            statement = select(ChatSession).where(col(ChatSession.user_id) == user_id).order_by(col(ChatSession.updated_at).desc())
            return list(session.exec(statement).all())

    def get_session(self, session_id: UUID) -> ChatSession | None:
        with self.db.session as session:
            return session.get(ChatSession, session_id)

    def delete_session(self, session_id: UUID) -> bool:
        with self.db.session as session:
            chat_session = session.get(ChatSession, session_id)
            if chat_session:
                session.delete(chat_session)
                session.commit()
                return True
            return False

    def add_message(
        self,
        session_id: UUID,
        role: str,
        content: Any,
        tool_calls: Any | None = None,
    ) -> ChatMessage:
        with self.db.session as session:
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                tool_calls=tool_calls,
            )
            session.add(message)

            # Update session updated_at
            chat_session = session.get(ChatSession, session_id)
            if chat_session:
                chat_session.updated_at = datetime.now(UTC)
                session.add(chat_session)

            session.commit()
            session.refresh(message)
            return message

    def get_messages(self, session_id: UUID) -> list[ChatMessage]:
        with self.db.session as session:
            statement = select(ChatMessage).where(col(ChatMessage.session_id) == session_id).order_by(col(ChatMessage.created_at).asc())
            return list(session.exec(statement).all())
