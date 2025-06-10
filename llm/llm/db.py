import os

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from psycopg_pool import ConnectionPool


def create_db(llm_embedding):
    connection_pool = ConnectionPool(
        conninfo=os.getenv("DB_URI"),
        max_size=20,
        min_size=2,
        kwargs={"autocommit": True, "prepare_threshold": 0, "connect_timeout": 5},
        timeout=10,
    )
    connection_pool.open()

    checkpointer = PostgresSaver(connection_pool)
    checkpointer.setup()

    store = PostgresStore(
        conn=connection_pool,
        index={"dims": int(os.getenv("DEFAULT_DIMENSIONS")), "embed": llm_embedding},
    )
    store.setup()
    return checkpointer, store
