import logging

from concurrent_log_handler import ConcurrentRotatingFileHandler

LOG_FILE = "./app.log"
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 3


def load_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.WARNING)

    handler = ConcurrentRotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)
    return logger
