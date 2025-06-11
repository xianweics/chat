import logging
import os
from concurrent_log_handler import ConcurrentRotatingFileHandler


def load_logger():
    logger = logging.getLogger()
    handler = ConcurrentRotatingFileHandler(
        filename=os.getenv("LOG_FILE"),
        maxBytes=int(os.getenv("MAX_BYTES")),
        backupCount=int(os.getenv("BACKUP_COUNT")),
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)
    return logger
