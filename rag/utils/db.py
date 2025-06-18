import asyncio
import logging
import os
import sys
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, Text, DateTime, UUID, select, text, JSON
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

Base = declarative_base()
log = logging.getLogger(__name__)


class Message(Base):
    __tablename__ = "messages"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
    )
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user = Column(Text, nullable=False)
    ai = Column(Text)
    thinking = Column(JSON, nullable=False)
    created_time = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))


class ConnectionPoolManager:
    POOL_STATS_INTERVAL = 60

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
        await self.create_tables()
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
        self, user_id: UUID, user: str, ai: str, thinking: list
    ) -> dict[str, Any]:
        session = await self.get_session()
        try:
            serializable_thinking = []
            for msg in thinking:
                if hasattr(msg, "type") and hasattr(msg, "content"):
                    msg_dict = {"role": msg.type, "content": msg.content}
                    if hasattr(msg, "tool_calls"):
                        msg_dict["tool_calls"] = msg.tool_calls
                    serializable_thinking.append(msg_dict)

            message = Message(
                user_id=user_id,
                id=uuid.uuid4(),
                user=user,
                ai=ai,
                thinking=serializable_thinking or thinking,
            )
            async with session.begin():
                session.add(message)
                await session.flush()

            return {
                "id": message.id,
                "user_id": message.user_id,
                "user": message.user,
                "ai": message.ai,
                "thinking": message.thinking,
                "created_time": message.created_time,
            }

        except Exception as e:
            print(traceback.format_exc())
            raise e

        finally:
            await session.close()

    async def get_chats(
        self, user_id: UUID, id: UUID, return_items=("*",)
    ) -> list[dict[str, Any | None]] | None:
        session = await self.get_session()

        try:
            stmt = select(Message).where(Message.id == id, Message.user_id == user_id)
            result = await session.execute(stmt)
            messages = result.unique().scalars().all()
            return [
                {
                    "id": m.id if "id" or "*" in return_items else None,
                    "user_id": m.user_id if "user_id" or "*" in return_items else None,
                    "user": (m.user if "user" or "*" in return_items else None),
                    "ai": m.ai if "ai" or "*" in return_items else None,
                    "thinking": (
                        m.thinking if "thinking" or "*" in return_items else None
                    ),
                    "created_time": (
                        m.created_time
                        if "created_time" or "*" in return_items
                        else None
                    ),
                }
                for m in messages
            ]
        except Exception as e:
            raise e
        finally:
            await session.close()
        return None


async def run_db() -> ConnectionPoolManager:
    try:
        cnn_pool = ConnectionPoolManager(os.getenv("DB_BASE_URI"), os.getenv("DB_NAME"))
        await cnn_pool.initialize()
        return cnn_pool
    except Exception as e:
        log.error(f"Failed to initialize database: {e}")
        sys.exit(-1)
