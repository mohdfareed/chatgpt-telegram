"""The database models defining the database schema."""

from typing import Any

import sqlalchemy as sql
import sqlalchemy.orm as orm
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import FernetEngine

from database import encryption_key
from database.core import DatabaseModel, engine

encrypted = StringEncryptedType(sql.Unicode, encryption_key, FernetEngine)


class User(DatabaseModel):
    """A telegram user."""

    __tablename__ = "users"

    token_usage: orm.Mapped[int] = orm.mapped_column(default=0)
    """The user's cumulative token usage."""
    usage: orm.Mapped[float] = orm.mapped_column(default=0)
    """The user's cumulative usage in USD."""

    def __init__(self, id: int, **kw: Any):
        super().__init__(id=id, **kw)


class Message(DatabaseModel):
    """A message in a chat history."""

    __tablename__ = "messages"

    session_id: orm.Mapped[str] = orm.mapped_column()
    """The session to which the message belongs."""
    _session_index = sql.Index(session_id)

    content: orm.Mapped[str] = orm.mapped_column(encrypted)
    """The message's contents."""
    metadata: orm.Mapped[str] = orm.mapped_column(encrypted)
    """The message's metadata."""

    def __init__(self, session_id: str, **kw: Any):
        super().__init__(session_id=session_id, **kw)

    @classmethod
    def load(cls, session_id: str):
        """Load a chat history by its session ID."""

        statement = sql.select(cls).where(cls.session_id == session_id)
        with orm.Session(engine()) as session:
            return session.scalars(statement).all()


class ChatModel(DatabaseModel):
    """A ChatGPT model's parameters."""

    __tablename__ = "models"

    session_id: orm.Mapped[str] = orm.mapped_column(unique=True)
    """The unique session to which the model belongs."""
    _session_index = sql.Index(session_id)

    parameters: orm.Mapped[str] = orm.mapped_column(encrypted)
    """The model's parameters."""

    def __init__(self, session_id: str, **kw: Any):
        super().__init__(session_id=session_id, **kw)

    def _loading_statement(self):
        # load a model by its ID or session ID
        return sql.select(ChatModel).where(
            ChatModel.id == self.id | ChatModel.session_id == self.session_id
        )


class Chat(DatabaseModel):
    """A telegram private chat (user), group chat, forum, or channel."""

    __tablename__ = "chats"

    topic_id: orm.Mapped[str | None] = orm.mapped_column()
    """The chat's topic ID. None for a general chat."""
    _topic_index = sql.Index(topic_id)

    token_usage: orm.Mapped[int] = orm.mapped_column()
    """The chat's cumulative token usage."""
    usage: orm.Mapped[float] = orm.mapped_column()
    """The chat's cumulative usage in USD."""

    @property
    def session_id(self):
        """The chat's session ID."""
        return f"{self.id}:{self.topic_id}"

    def __init__(self, id: int, topic_id: str | None, **kw: Any):
        super().__init__(id=id, topic_id=topic_id, **kw)


__all__ = ["Chat", "ChatModel", "Message", "User"]
