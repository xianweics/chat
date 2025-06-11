import logging
import os
import sys
import threading

from psycopg_pool import ConnectionPool
import time

log = logging.getLogger(__name__)


def monitor_connection_pool(db_connection_pool, interval=60):

    def monitor():
        stats = db_connection_pool.get_stats()
        active = stats.get("connections_in_use", 0)
        total = db_connection_pool.max_size
        log.info(
            f"Connection db_connection_pool status: {active}/{total} connections in use"
        )
        if active >= total * 0.8:
            log.warning(
                f"Connection db_connection_pool nearing capacity: {active}/{total}"
            )
        time.sleep(interval)

    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()


def run_db():
    connection_pool = ConnectionPool(
        conninfo=os.getenv("DB_URI"),
        max_size=20,
        min_size=2,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "connect_timeout": 5,
        },
        timeout=10,
    )
    try:
        connection_pool.open()
        monitor_connection_pool(connection_pool)
        log.info("Database connection pool initialized")
    except Exception as e:
        log.error(f"Failed to open connection pool: {e}")
        sys.exit(1)
    return connection_pool
