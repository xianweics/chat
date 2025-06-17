import logging
import os
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Text,
    DateTime,
    JSON,
    UUID,
    ForeignKey,
    select,
    text,
)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, relationship, joinedload

Base = declarative_base()
log = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()


class Message(Base):
    __tablename__ = "messages"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
    )
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    thread_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    created_time = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    history = relationship("History", back_populates="message", uselist=False)


class History(Base):
    __tablename__ = "history"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        default=uuid.uuid4,
    )
    message_id = Column(
        UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False, index=True
    )
    thoughts = Column(JSON, nullable=False)
    created_time = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    message = relationship("Message", back_populates="history")


class ConnectionPoolManager:
    POOL_STATS_INTERVAL = 30

    def __init__(self, conn_string):
        self.Session = None
        self.conn_string = conn_string
        self.engine = None
        self.monitor_task = None

        self.pool_config = {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }

    async def initialize(self):
        print("Initializing database connection pool...")
        self.engine = create_async_engine(self.conn_string, **self.pool_config)

        self.Session = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

        async with self.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        self.monitor_task = asyncio.create_task(self.monitor_pool_stats())
        await self.create_tables()
        return self

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self):
        return self.Session()

    async def monitor_pool_stats(self):
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
                print(f"Error monitoring pool: {e}")
            await asyncio.sleep(self.POOL_STATS_INTERVAL)

    async def close(self):
        if self.monitor_task:
            try:
                self.monitor_task.cancel()
                await self.monitor_task
            except Exception as e:
                log.error(f"Error cancelling monitor task: {str(e)}")
                pass

        if self.engine:
            await self.engine.dispose()

        print("Connection pool manager shutdown complete")

    async def save_conversation(self, user_id, thread_id, question, answer, thoughts):
        message_id = str(uuid.uuid4())
        session = await self.get_session()
        try:
            message = Message(
                user_id=user_id,
                thread_id=thread_id,
                id=message_id,
                question=question,
                answer=answer,
            )

            async with session.begin():
                session.add(message)
                await session.flush()

                history = History(message_id=message_id, thoughts=thoughts)
                session.add(history)
                await session.refresh(message)
                await session.refresh(history)
            print(f"Saved conversation {message_id}")

            return {
                "message": {
                    "id": message.id,
                    "user_id": message.user_id,
                    "thread_id": message.thread_id,
                    "question": message.question,
                    "answer": message.answer,
                    "created_time": message.created_time,
                },
                "history": {
                    "id": history.id,
                    "message_id": history.message_id,
                    "thoughts": history.thoughts,
                    "created_time": history.created_time,
                },
            }

        except Exception as e:
            print(f"Failed to save conversation: {str(e)}")
            raise e

        finally:
            await session.close()

    async def get_chat_by_thread(self, user_id, thread_id, included_history=False):
        session = await self.get_session()

        try:
            stmt = select(Message).where(
                Message.thread_id == thread_id, Message.user_id == user_id
            )

            if included_history:
                stmt = stmt.options(joinedload(Message.history))

            result = await session.execute(stmt)
            messages = result.unique().scalars().all()

            return [
                {
                    "id": m.id,
                    "user_id": m.user_id,
                    "thread_id": m.thread_id,
                    "question": m.question,
                    "answer": m.answer,
                    "created_time": m.created_time,
                    "history": (
                        {
                            "id": m.history.id,
                            "message_id": m.history.message_id,
                            "thoughts": m.history.thoughts,
                            "created_time": m.history.created_time,
                        }
                        if included_history and m.history
                        else None
                    ),
                }
                for m in messages
            ]
        except Exception as e:
            print(f"Error in get_chat_by_thread: {str(e)}")
            raise e
        finally:
            await session.close()
        return None

    async def get_history_by_id(self, id):
        session = await self.get_session()

        try:
            stmt = select(History).where(History.id == id)
            result = await session.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            print(f"Error in get_history_by_id: {str(e)}")
            raise e
        finally:
            await session.close()


async def run_db():
    try:
        cnn_pool = ConnectionPoolManager(os.getenv("DB_URI"))
        await cnn_pool.initialize()
        user_id = uuid.uuid4()
        thread_id = uuid.uuid4()
        print("Test user_id:", user_id)
        print("Test thread_id:", thread_id)

        result = await cnn_pool.save_conversation(
            user_id=user_id,
            thread_id=thread_id,
            question="haha",
            answer="lala",
            thoughts=[{"data": "test"}],
        )
        print("Save result:", result)

        messages = await cnn_pool.get_chat_by_thread(user_id, thread_id)
        print("Messages without history:", messages)
        messages = await cnn_pool.get_chat_by_thread(
            "f9cc6947-d895-4ad0-b27f-1412259cfb6a", thread_id
        )
        print("Messages without history:", messages)

        messages_with_history = await cnn_pool.get_chat_by_thread(
            user_id, thread_id, True
        )
        print("Messages with history:", messages_with_history)
        messages_with_history = await cnn_pool.get_chat_by_thread(
            "f9cc6947-d895-4ad0-b27f-1412259cfb6a", thread_id, True
        )
        print("Messages with history:", messages_with_history)

        return cnn_pool
    except Exception as e:
        log.error(f"Failed to initialize database: {e}")
        sys.exit(-1)


import asyncio

asyncio.run(run_db())
