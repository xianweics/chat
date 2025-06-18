import asyncio
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Coroutine

from sqlalchemy import Column, Text, DateTime, JSON, UUID, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

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
    thinking = Column(JSON, nullable=False)
    created_time = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))


class ConnectionPoolManager:
    POOL_STATS_INTERVAL = 60

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

        self.monitor_task = asyncio.create_task(self.monitor_pool_stats())
        await self.create_tables()
        print("database connection pool...")
        return self

    async def create_tables(self):
        async with self.engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all)
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

    async def save_conversation(self, user_id, thread_id, question, answer, thinking):
        session = await self.get_session()
        try:
            message = Message(
                user_id=user_id,
                thread_id=thread_id,
                id=str(uuid.uuid4()),
                question=question,
                answer=answer,
                thinking=thinking,
            )

            async with session.begin():
                session.add(message)
                await session.flush()

                result_data = {
                    "id": message.id,
                    "user_id": message.user_id,
                    "thread_id": message.thread_id,
                    "question": message.question,
                    "answer": message.answer,
                    "thinking": message.thinking,
                    "created_time": message.created_time,
                }

            print(f"Saved conversation {message.id}")
            return result_data

        except Exception as e:
            print(f"Failed to save conversation: {str(e)}")
            raise e

        finally:
            await session.close()

    async def get_chats(self, user_id, thread_id, included_history=False):
        session = await self.get_session()

        try:
            stmt = select(Message).where(
                Message.thread_id == thread_id, Message.user_id == user_id
            )

            result = await session.execute(stmt)
            messages = result.unique().scalars().all()

            return [
                {
                    "id": m.id,
                    "user_id": m.user_id,
                    "thread_id": m.thread_id,
                    "question": m.question,
                    "answer": m.answer,
                    "thinking": m.thinking if included_history else None,
                    "created_time": m.created_time,
                }
                for m in messages
            ]
        except Exception as e:
            print(f"Error in get_chats: {str(e)}")
            raise e
        finally:
            await session.close()
        return None

    async def get_history(self, id) -> list[dict[str, Any]]:
        session = await self.get_session()

        try:
            stmt = select(Message).where(Message.id == id)
            result = await session.execute(stmt)

            messages = result.scalars().all()
            return [
                {
                    "id": m.id,
                    "user_id": m.user_id,
                    "thread_id": m.thread_id,
                    "question": m.question,
                    "answer": m.answer,
                    "thinking": m.thinking,
                    "created_time": m.created_time,
                }
                for m in messages
            ]
        except Exception as e:
            print(f"Error in get_history: {str(e)}")
            raise e
        finally:
            await session.close()
        return None


async def run_db():
    try:
        cnn_pool = ConnectionPoolManager(os.getenv("DB_URI"))
        await cnn_pool.initialize()
        # user_id = uuid.uuid4()
        # thread_id = uuid.uuid4()
        # print("Test user_id:", user_id)
        # print("Test thread_id:", thread_id)
        #
        # result = await cnn_pool.save_conversation(
        #     user_id=user_id,
        #     thread_id=thread_id,
        #     question="haha",
        #     answer="lala",
        #     thinking=[{"data": "test"}],
        # )
        # print("Save result:", result)
        #
        # messages = await cnn_pool.get_chats(user_id, thread_id)
        # print("Messages without history:", messages)
        # messages = await cnn_pool.get_chats(
        #     "f9cc6947-d895-4ad0-b27f-1412259cfb6a", thread_id
        # )
        # print("Messages without history:", messages)
        #
        # messages_with_history = await cnn_pool.get_chats(user_id, thread_id, True)
        # print("Messages with history:", messages_with_history)
        # messages_with_history = await cnn_pool.get_chats(
        #     "f9cc6947-d895-4ad0-b27f-1412259cfb6a", thread_id, True
        # )
        # print("Messages with history:", messages_with_history)
        history = await cnn_pool.get_history("6820064c-58f7-41cb-ad68-81ad74ff4d88")
        print("history:", history)

        return cnn_pool
    except Exception as e:
        log.error(f"Failed to initialize database: {e}")
        sys.exit(-1)


asyncio.run(run_db())
