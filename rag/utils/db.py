import asyncio
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from http.client import HTTPException
from typing import Any, Optional, Sequence

import tenacity
from sqlalchemy import Column, Text, DateTime, UUID, select, text, String, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()
log = logging.getLogger(__name__)


class User(Base):
    __tablename__ = "users"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
    )
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(300), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    sessions = relationship(
        "AISession", back_populates="user", cascade="all, delete-orphan"
    )


class AISession(Base):
    __tablename__ = "ai_sessions"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    title = Column(String(100), default="New session")

    user = relationship("User", back_populates="sessions")
    messages = relationship(
        "AIMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AIMessage.created_at",
    )


class AIMessage(Base):
    __tablename__ = "ai_messages"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
    )
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("ai_sessions.id"), nullable=False
    )
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    ai_model = Column(String(50), default="")
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    session = relationship("AISession", back_populates="messages")


class ConnectionPoolManager:
    POOL_STATS_INTERVAL = 60
    MAX_RETRIES = 3
    RETRY_DELAY = 1

    def __init__(self, url, name):
        self.Session = None
        self.url = url
        self.name = name
        self.engine = None
        self.monitor_task = None

        self.pool_config = {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }

    async def initialize(self) -> "ConnectionPoolManager":
        await self.create_database_if_not_exists()

        self.engine = create_async_engine(self.url + self.name, **self.pool_config)
        self.Session = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        self.monitor_task = asyncio.create_task(self.monitor_pool_stats())
        # Only run one time
        # await self.create_tables()
        return self

    async def create_database_if_not_exists(self) -> None:
        temp_engine = create_async_engine(
            self.url,
            isolation_level="AUTOCOMMIT",
        )

        async with temp_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": self.name},
            )

            if not result.scalar():
                await conn.execute(text(f"CREATE DATABASE {self.name}"))

    async def create_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            print("created table successfully")

    async def get_session(self) -> AsyncSession:
        return self.Session()

    async def monitor_pool_stats(self) -> None:
        while True:
            try:
                if self.engine and self.engine.pool:
                    pool = self.engine.pool
                    total_size = self.pool_config["pool_size"]
                    current_size = pool.size()
                    checkedout = pool.checkedout()
                    available = pool.checkedin()
                    overflow = current_size - total_size

                    stats = {
                        "total_size": total_size,
                        "current_size": current_size,
                        "checkedout": checkedout,
                        "available": available,
                        "overflow": overflow,
                        "max_allowed": total_size + self.pool_config["max_overflow"],
                    }
                    print("Pool stats:", stats)
            except Exception as e:
                raise e
            await asyncio.sleep(self.POOL_STATS_INTERVAL)

    async def close(self) -> None:
        if self.monitor_task:
            try:
                self.monitor_task.cancel()
                await self.monitor_task
            except Exception as e:
                log.error(f"Error cancelling monitor task: {str(e)}")
                pass

        if self.engine:
            await self.engine.dispose()

    async def save_chat(
        self,
        session_id: UUID,
        role: str,
        content: text,
        ai_model: Optional[str] = "",
    ) -> dict[str, Any]:
        async with self.Session() as session:
            async with session.begin():
                stmt = select(AISession).where(AISession.id == session_id).limit(1)
                result = await session.execute(stmt)
                data = result.scalars().first()
                if not data:
                    raise HTTPException("invalid id")
                message = AIMessage(
                    id=uuid.uuid4(),
                    session_id=session_id,
                    role=role,
                    ai_model=ai_model,
                    content=content,
                )
                session.add(message)
                await session.flush()

                return {
                    "id": message.id,
                    "session_id": message.session_id,
                    "role": message.role,
                    "content": message.content,
                }

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(MAX_RETRIES),
        wait=tenacity.wait_fixed(RETRY_DELAY),
        retry=tenacity.retry_if_exception_type(Exception),
        before=tenacity.before_log(log, logging.INFO),
        after=tenacity.after_log(log, logging.INFO),
    )
    async def get_chats(
        self, session_id: UUID, limit: int = 300, order: Optional[str] = "asc"
    ) -> Sequence[AIMessage]:
        session = await self.get_session()

        stmt = (
            select(AIMessage)
            .where(AIMessage.session_id == session_id)
            .order_by(
                AIMessage.created_at.desc()
                if order == "order"
                else AIMessage.created_at.asc()
            )
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.unique().scalars().all()


async def run_db() -> ConnectionPoolManager:
    try:
        cnn_pool = ConnectionPoolManager(os.getenv("DB_BASE_URI"), os.getenv("DB_NAME"))
        await cnn_pool.initialize()
        return cnn_pool
    except Exception as e:
        log.error(f"Failed to initialize database: {e}")
        sys.exit(-1)
