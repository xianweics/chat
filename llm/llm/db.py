import os
from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy import (
    Column,
    String,
    JSON,
    create_engine,
    DateTime,
    func,
    ForeignKey,
    UUID,
)
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import uuid
import traceback

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, default="")


class Messages(Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=func.now())
    embedding = Column(Vector(int(os.getenv("DEFAULT_DIMENSIONS"))))

    user = relationship("User", backref="messages")


class DB(BaseCheckpointSaver):
    def __init__(self, oai):
        super().__init__()
        self.engine = create_engine(os.getenv("DB_URI"))
        self.Session = sessionmaker(bind=self.engine)
        self.oai = oai
        Base.metadata.create_all(self.engine)

    # todo: need to remove later
    def create_user(self):
        session = self.Session()
        user = User(username="temp user")
        session.add(user)
        session.commit()

    def save(self, **kwargs):
        session = self.Session()
        d = kwargs.get("data")
        record = Messages(
            id=kwargs.get("id"),
            user_id=kwargs.get("user_id"),
            data=d,
            embedding=self.oai.embeddings.create(
                input=d,
                dimensions=int(os.getenv("DEFAULT_DIMENSIONS")),
                model=os.getenv("DASHSCOPE_EMBEDDING"),
            )
            .data[0]
            .embedding,
        )
        try:
            session.add(record)
            session.commit()
        except Exception:
            traceback.format_exc()
            session.rollback()
            raise
        finally:
            session.close()

    def get(self, **kwargs):
        session = self.Session()
        try:
            record = (
                session.query(Messages)
                .filter_by(id=kwargs.get("id"), user_id=kwargs.get("user_id"))
                .first()
            )
            return record.data if record else None
        except:
            traceback.format_exc()
            session.rollback()
            raise
        finally:
            session.close()
