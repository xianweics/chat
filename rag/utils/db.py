import logging
import os
import sys
import threading
import time

from psycopg_pool import ConnectionPool

log = logging.getLogger(__name__)

# db
DB_MONITOR_INTERVAL = 60
DB_CONNECT_MAX = 20
DB_CONNECT_MIN = 2
DB_CONNECT_TIMEOUT = 5
DB_TIMEOUT = 10


def monitor_connection_pool(db_connection_pool, interval=DB_MONITOR_INTERVAL):
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
    try:
        pool = ConnectionPool(
            conninfo=os.getenv("DB_URI"),
            min_size=DB_CONNECT_MIN,
            max_size=DB_CONNECT_MAX,
            kwargs={
                "autocommit": True,
                "connect_timeout": DB_CONNECT_TIMEOUT,
            },
            timeout=DB_TIMEOUT,
        )
        pool.open()
        monitor_connection_pool(pool)
        return pool
    except Exception as e:
        log.error(f"Failed to open connection pool: {e}")
        sys.exit(1)
