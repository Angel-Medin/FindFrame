import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s | %(message)s"
    )

    # Consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Archivo (rotativo)
    file_handler = RotatingFileHandler(
        "app.log",
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
