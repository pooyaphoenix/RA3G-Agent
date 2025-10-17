import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def get_logger(name: str, logfile: str, level=logging.INFO):
    Path("logs").mkdir(exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = RotatingFileHandler(logfile, maxBytes=5_000_000, backupCount=3, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    return logger
