import logging
from logging import Logger
from pathlib import Path

from concurrent_log_handler import ConcurrentRotatingFileHandler

MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 3

pp = Path(__file__).parent
LOG_FILE = str(Path(f"{pp}/app.log"))


def load_logger() -> Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)

    for handler in logger.handlers:
        if isinstance(handler, ConcurrentRotatingFileHandler):
            return logger

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
